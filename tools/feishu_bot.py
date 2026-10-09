#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书群机器人桥接 —— WebSocket 长连接模式（免公网 / 免内网穿透 / 免验签）

与旧版 feishu_bot_webhook.py 的区别：
  - 旧版：飞书 POST 回调到本机 HTTP 服务，需公网 URL 或隧道 + 签名校验 + 可选解密。
  - 本版：用 lark-oapi SDK 在客户端【主动】建立 wss 长连接，飞书经该隧道推事件。
          因此【无需公网 IP / 域名 / 内网穿透】，运行环境只要能访问公网飞书服务器即可；
          事件传输由 SDK 内置加密，推送给开发者的是明文，无需验签 / 解密。

数据流向（模型在内网也完全可达）：
  群成员 @机器人
    → 飞书经 wss 长连接推送 im.message.receive_v1（明文 JSON）
    → 本机 handler 解析文本、立即返回（满足飞书 3 秒处理限制），任务丢入线程池
    → 线程池调 answer()（检索 + 访问 192.168.1.75 本地模型）
    → 经飞书「回复消息」API 异步发回群

核心问答逻辑全部复用 ask.answer()，本文件只做消息桥接。

依赖：lark-oapi（pip install lark-oapi -U）。注意：长连接模式仅支持【企业自建应用】。
"""
import json, os, sys, re, threading, time
from concurrent.futures import ThreadPoolExecutor
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ask import answer  # 复用 RAG + 本地 7B 模型问答管线

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
API_BASE = cfg("FEISHU_API_BASE", "https://open.feishu.cn/open-apis")
OLLAMA_URL = cfg("KB_OLLAMA_URL", "http://192.168.1.75:11434")
MODEL = cfg("KB_MODEL", "qwen2.5:7b-instruct-q4_K_M")
K = int(cfg("BOT_TOPK", "6"))
MAX_CHARS = int(cfg("BOT_MAX_CHARS", "4000"))
MAX_REPLY = int(cfg("BOT_MAX_REPLY", "4000"))       # 飞书单条文本上限附近
CONCURRENCY = int(cfg("BOT_MAX_CONCURRENCY", "1"))  # 同时进行的模型调用数（限流保护）
LOG_LEVEL = cfg("FEISHU_LOG_LEVEL", "ERROR")        # DEBUG / INFO / WARN / ERROR

# ---------------------------------------------------------------- 飞书 API（标准库 HTTP）
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


def _post_json(url, token, payload):
    """POST JSON 到飞书 API，返回解析后的 dict（不在此判业务码）。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8",
                 "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def _safe_code(body):
    try:
        return json.loads(body) or {}
    except Exception:
        return {}


# 群不支持「回复」时飞书返回的业务码（话题群 / 已删除话题 / 不支持的消息类型）
_REPLY_FALLBACK_CODES = (230071, 230019, 230054)


def send_reply(message_id, chat_id, text):
    """把答案发回。优先用「回复消息」接口挂在原消息下；
    若群不支持回复（话题群等），降级为向群发一条新消息。"""
    tok = get_tenant_token()
    content = json.dumps({"text": text}, ensure_ascii=False)
    # 1) 回复消息（路径 message_id 已定位会话，无需 receive_id）
    try:
        d = _post_json(API_BASE + "/im/v1/messages/" + message_id + "/reply",
                       tok, {"msg_type": "text", "content": content})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        d = _safe_code(body)
        if d.get("code") in _REPLY_FALLBACK_CODES and chat_id:
            _post_json(API_BASE + "/im/v1/messages?receive_id_type=chat_id",
                       tok, {"receive_id": chat_id, "msg_type": "text", "content": content})
            return
        raise RuntimeError("reply HTTP %s: %s" % (e.code, body))
    if d.get("code") == 0:
        return
    # 业务码非 0：尝试降级为发到群
    if d.get("code") in _REPLY_FALLBACK_CODES and chat_id:
        _post_json(API_BASE + "/im/v1/messages?receive_id_type=chat_id",
                   tok, {"receive_id": chat_id, "msg_type": "text", "content": content})
        return
    raise RuntimeError("reply failed: %s" % d)


def clean_text(content_json):
    """解析消息 content，并剥离 @机器人 提及前缀。"""
    try:
        obj = json.loads(content_json)
    except Exception:
        return content_json
    t = obj.get("text", "")
    t = re.sub(r"@_user_\d+\s*", "", t)        # 群内 @机器人 标记
    t = re.sub(r"@ou_[A-Za-z0-9]+\s*", "", t)  # open_id 提及
    t = t.replace("@_chat_", "")
    return t.strip()


# ---------------------------------------------------------------- 并发控制：后台推理线程池
_sem = threading.Semaphore(max(1, CONCURRENCY))
_exec = ThreadPoolExecutor(max_workers=max(1, CONCURRENCY))


def worker(message_id, chat_id, q):
    """后台线程：真正调用模型（较慢），再异步回复。"""
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
        send_reply(message_id, chat_id, ans)
    except Exception as e:
        print("[回复失败]", e, file=sys.stderr)


def do_message(data):
    """SDK 事件回调：事件到达即被调用。必须在 3 秒内返回，故只解析 + 派发，不在此推理。"""
    import lark_oapi as lark
    try:
        d = json.loads(lark.JSON.marshal(data))   # SDK 对象 → 字典，规避字段名版本差异
    except Exception:
        return None
    ev = (d.get("event") or {})
    msg = ev.get("message") or {}
    if msg.get("message_type") != "text":
        return None                                # 暂只处理文本消息
    chat_type = msg.get("chat_type")
    mentions = msg.get("mentions") or []
    if chat_type == "group" and not mentions:
        return None                                # 群聊仅处理被 @ 的消息（防刷屏）
    q = clean_text(msg.get("content", "{}"))
    if not q:
        return None
    message_id = msg.get("message_id")
    chat_id = msg.get("chat_id")                 # 群聊 id，用于「回复」不可用时降级发群
    # 立即返回；推理放入后台线程池，避免触发飞书「3 秒超时重推」
    _exec.submit(worker, message_id, chat_id, q)
    return None


# ---------------------------------------------------------------- 主流程
def main():
    if not (APP_ID and APP_SECRET):
        print("缺少 FEISHU_APP_ID / FEISHU_APP_SECRET，请在 bot_config.py 或环境变量填写。",
              file=sys.stderr)
        sys.exit(1)
    try:
        import lark_oapi as lark
        from lark_oapi import EventDispatcherHandler, LogLevel
        from lark_oapi.ws import Client as WsClient
    except Exception as e:
        print("需安装 lark-oapi：\n"
              "  /Users/suweibin/.workbuddy/binaries/python/envs/default/bin/pip install lark-oapi -U\n"
              + str(e), file=sys.stderr)
        sys.exit(2)

    lv = getattr(LogLevel, LOG_LEVEL.upper(), LogLevel.ERROR)
    handler = (EventDispatcherHandler.builder("", "")   # 两个参数长连接模式下必须为空字符串
               .register_p2_im_message_receive_v1(do_message)
               .build())
    cli = WsClient(app_id=APP_ID, app_secret=APP_SECRET,
                   event_handler=handler, log_level=lv)

    print("飞书长连接 bot 启动（免公网 / 免内网穿透 / 免验签）")
    print(f"  APP_ID={APP_ID[:6]}…  模型={MODEL}  topk={K}  并发={CONCURRENCY}")
    print("  在飞书群内 @机器人 即可提问；后台 wss 长连接持续保活与重连。")
    try:
        cli.start()                      # 阻塞主线程，直到进程结束
    except KeyboardInterrupt:
        print("\n已退出。")


if __name__ == "__main__":
    main()
