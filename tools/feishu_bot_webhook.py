#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书群机器人桥接服务 —— 把 ask.py 的 RAG + 本地 7B 模型问答接入飞书群聊

复用 ask.answer() 完成检索与生成，本服务只负责：
  1. 接收飞书事件回调（URL 验证握手 / 消息事件）
  2. 校验请求签名（HMAC-SHA256，标准库）＋ 可选 AES 解密（Encrypt Key）
  3. 解析群内 @机器人 文本消息，剥离提及前缀
  4. 立即 ACK(200)，再异步调用回复 API（飞书回调 ~10s 超时，模型 ~6 tok/s）
  5. tenant_access_token 缓存、模型调用并发信号量（应对 429 限流）

仅用 Python 标准库；解密依赖可选 pycryptodome（开启 Encrypt Key 时需要）。

运行：
    python3 feishu_bot.py
依赖配置见 bot_config.py（或同名环境变量）。

飞书自建应用所需权限：im:message（读取/发送消息）、im:message:send_as_bot
"""
import json, os, sys, re, hashlib, hmac, base64, threading, time
import urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ask import answer  # 复用 RAG + 模型管线

# ---------------------------------------------------------------- 配置
try:
    import bot_config as _C
except Exception:
    _C = None


def cfg(name, default=""):
    v = os.environ.get(name)
    if v:
        return v
    return getattr(_C, name, default) if _C else default


APP_ID = cfg("FEISHU_APP_ID")
APP_SECRET = cfg("FEISHU_APP_SECRET")
ENCRYPT_KEY = cfg("FEISHU_ENCRYPT_KEY")                 # 事件订阅 Encrypt Key（验签 + 解密）
LEGACY_TOKEN = cfg("FEISHU_LEGACY_TOKEN", "")           # 旧版 verification token（仅本地测试）
API_BASE = cfg("FEISHU_API_BASE", "https://open.feishu.cn/open-apis")
PORT = int(cfg("FEISHU_BOT_PORT", "8080"))
WEBHOOK_PATH = cfg("FEISHU_WEBHOOK_PATH", "/feishu")
OLLAMA_URL = cfg("KB_OLLAMA_URL", "http://192.168.1.75:11434")
MODEL = cfg("KB_MODEL", "qwen2.5:7b-instruct-q4_K_M")
K = int(cfg("BOT_TOPK", "6"))
MAX_CHARS = int(cfg("BOT_MAX_CHARS", "4000"))
MAX_REPLY = int(cfg("BOT_MAX_REPLY", "4000"))           # 飞书单条文本上限附近
CONCURRENCY = int(cfg("BOT_MAX_CONCURRENCY", "1"))      # 同时进行的模型调用数（限流保护）

# ---------------------------------------------------------------- 可选 AES 解密
try:
    from Crypto.Cipher import AES
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False


def _decrypt_body(raw_body):
    """若开启 Encrypt Key，飞书会把事件体用 AES-256-CBC 加密进 {"encrypt":...}。"""
    obj = json.loads(raw_body)
    if "encrypt" not in obj:
        return raw_body
    if not ENCRYPT_KEY:
        raise RuntimeError("收到加密事件但未配置 FEISHU_ENCRYPT_KEY")
    if not _HAS_CRYPTO:
        raise RuntimeError("需安装 pycryptodome：pip install pycryptodome")
    key = hashlib.md5(ENCRYPT_KEY.encode("utf-8")).hexdigest()   # 32 hex → 32 bytes
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, key[:16].encode("utf-8"))
    decrypted = cipher.decrypt(base64.b64decode(obj["encrypt"]))
    pad = decrypted[-1]
    return decrypted[:-pad].decode("utf-8")


def verify_signature(headers, raw_body):
    """飞书签名校验：X-Lark-Signature = base64(HMAC-SHA256(ts+nonce+body, key))。"""
    if not ENCRYPT_KEY:
        if LEGACY_TOKEN:                      # 回退：旧版 token（仅本地调试）
            try:
                return json.loads(raw_body).get("token") == LEGACY_TOKEN
            except Exception:
                return False
        return True                           # 未配置任何校验（仅本机隧道测试）
    sig = headers.get("X-Lark-Signature") or headers.get("x-lark-signature")
    ts = headers.get("X-Lark-Request-Timestamp") or headers.get("x-lark-request-timestamp")
    nonce = headers.get("X-Lark-Request-Nonce") or headers.get("x-lark-request-nonce")
    if not sig or ts is None or nonce is None:
        return False
    msg = (str(ts) + str(nonce) + raw_body).encode("utf-8")
    exp = base64.b64encode(
        hmac.new(ENCRYPT_KEY.encode("utf-8"), msg, hashlib.sha256).digest()).decode("utf-8")
    return hmac.compare_digest(exp, sig)


# ---------------------------------------------------------------- 飞书 API
_token = {"value": None, "exp": 0}
_token_lock = threading.Lock()


def get_tenant_token():
    with _token_lock:
        if _token["value"] and time.time() < _token["exp"] - 30:
            return _token["value"]
        data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode("utf-8")
        req = urllib.request.Request(
            API_BASE + "/auth/v3/tenant_access_token/internal",
            data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode("utf-8"))
        if d.get("code") != 0:
            raise RuntimeError("获取 tenant_access_token 失败: " + str(d))
        _token["value"] = d["tenant_access_token"]
        _token["exp"] = time.time() + int(d.get("expire", 7200))
        return _token["value"]


def send_reply(message_id, text):
    tok = get_tenant_token()
    url = API_BASE + "/im/v1/messages?receive_id_type=message_id"
    payload = {"receive_id": message_id, "msg_type": "text",
               "content": json.dumps({"text": text})}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def clean_text(content_json):
    """解析消息 content，并剥离 @机器人 提及前缀。"""
    try:
        obj = json.loads(content_json)
    except Exception:
        return content_json
    t = obj.get("text", "")
    t = re.sub(r"@_user_\d+\s*", "", t)        # 群内 @机器人 标记
    t = t.replace("@_chat_", "")
    t = re.sub(r"@ou_[A-Za-z0-9]+", "", t)     # open_id 提及
    return t.strip()


# ---------------------------------------------------------------- 并发控制
_sem = threading.Semaphore(max(1, CONCURRENCY))


def handle_event(obj):
    ev = obj.get("event", {})
    msg = ev.get("message", {})
    if msg.get("message_type") != "text":
        return
    chat_type = msg.get("chat_type")
    mentions = msg.get("mention") or []
    if chat_type == "group" and not mentions:
        return                                # 群聊仅响应被 @ 的消息
    q = clean_text(msg.get("content", "{}"))
    if not q:
        return

    try:
        with _sem:
            ans, hits, _, _ = answer(q, k=K, max_chars=MAX_CHARS,
                                     url=OLLAMA_URL, model=MODEL,
                                     backend="openai", no_stream=True)
    except Exception as e:
        ans = "处理失败：%s" % e
        hits = []

    srcs = []
    for r, _ in hits[:6]:
        s = f"第{r['chapter']}章 {r['chapter_title']}"
        if r.get("section"):
            s += f" / {r['section']} {r.get('section_title', '')}"
        if s not in srcs:
            srcs.append(s)
    if srcs:
        ans = ans + "\n\n— 来源：" + "；".join(srcs)
    if len(ans) > MAX_REPLY:
        ans = ans[: MAX_REPLY - 10] + "…(已截断)"

    try:
        send_reply(msg.get("message_id"), ans)
    except Exception as e:
        print("[回复失败]", e, file=sys.stderr)


# ---------------------------------------------------------------- HTTP 服务
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"ok": True, "service": "feishu-bot"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) or b""
        raw_body = raw.decode("utf-8", "ignore")

        if not verify_signature(self.headers, raw_body):
            self._send(401, {"msg": "bad signature"})
            return
        try:
            plain = _decrypt_body(raw_body)
        except Exception as e:
            print("[解密失败]", e, file=sys.stderr)
            self._send(200, {"msg": "decrypt failed"})
            return
        try:
            obj = json.loads(plain)
        except Exception:
            self._send(200, {})
            return

        # URL 验证握手（配置事件订阅时飞书会发一次）
        if obj.get("type") == "url_verification":
            self._send(200, {"challenge": obj.get("challenge", "")})
            return

        # 事件：立即 ACK，异步处理（避免飞书 10s 超时）
        self._send(200, {"code": 0, "msg": "success"})
        if obj.get("header", {}).get("event_type") == "im.message.receive_v1":
            threading.Thread(target=handle_event, args=(obj,), daemon=True).start()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if not (APP_ID and APP_SECRET):
        print("缺少 FEISHU_APP_ID / FEISHU_APP_SECRET，请在 bot_config.py 或环境变量中填写。",
              file=sys.stderr)
        sys.exit(1)
    print(f"飞书 bot 启动: http://0.0.0.0:{PORT}{WEBHOOK_PATH}")
    print(f"  APP_ID={APP_ID[:6]}…  模型={MODEL}  topk={K}  并发={CONCURRENCY}")
    if not ENCRYPT_KEY and not LEGACY_TOKEN:
        print("  [警告] 未配置签名校验（仅限本机隧道调试，生产请设置 Encrypt Key）。",
              file=sys.stderr)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
