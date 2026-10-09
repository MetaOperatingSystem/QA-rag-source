# -*- coding: utf-8 -*-
"""
feishu_notify.py —— 用飞书【自定义机器人 Webhook】把消息推送到群（单向通知）。

重要：飞书「自定义机器人」(Webhook) 只能发送消息，不能接收或回复群成员 @ 它的提问。
本脚本用于把 ask.py 的教材回答主动推到群里（例如手动触发、定时任务、自动化调用）。
若要「群成员 @机器人 自动回复」，请用 feishu_bot.py（企业自建应用 + WebSocket 长连接）。

用法：
  python3 feishu_notify.py --text "今日学习：第7章 梯度与参数初始化"
  python3 feishu_notify.py --question "反向传播的两个阶段分别做什么？" -k 5
  python3 feishu_notify.py --text "测试" --dry-run        # 只打印 payload，不实际发送
  echo "某段文本" | python3 feishu_notify.py              # 从 stdin 读取

依赖：仅 Python 标准库。
"""
import sys, os, json, time, base64, hmac, hashlib, argparse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bot_config
from ask import answer


def build_payload(text):
    """构造飞书自定义机器人文本消息体；可选关键词前缀 + 加签。"""
    kw = getattr(bot_config, "FEISHU_WEBHOOK_KEYWORD", "") or ""
    if kw and not text.startswith(kw):
        text = kw + " " + text
    payload = {"msg_type": "text", "content": {"text": text}}
    secret = getattr(bot_config, "FEISHU_WEBHOOK_SECRET", "") or ""
    if secret:
        ts = str(int(time.time()))
        s = (ts + "\n" + secret).encode("utf-8")
        sign = base64.b64encode(
            hmac.new(secret.encode("utf-8"), s, hashlib.sha256).digest()
        ).decode("utf-8")
        payload["timestamp"] = ts
        payload["sign"] = sign
    return payload


def send(text, dry_run=False):
    url = getattr(bot_config, "FEISHU_WEBHOOK_URL", "") or ""
    if not url:
        print("错误：未配置 FEISHU_WEBHOOK_URL（在 bot_config.py 设置，或用环境变量）。",
              file=sys.stderr)
        sys.exit(2)
    payload = build_payload(text)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    if dry_run:
        print("[dry-run] 目标地址:", url)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP 错误", e.code, ":", e.read().decode("utf-8", "ignore"),
              file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print("发送失败:", e, file=sys.stderr)
        sys.exit(3)

    code = resp.get("code", resp.get("StatusCode"))
    if code not in (0, None):
        print("飞书拒绝推送:", resp, file=sys.stderr)
        sys.exit(3)
    print("已推送到群。")


def main():
    ap = argparse.ArgumentParser(description="飞书自定义机器人 Webhook 单向推送")
    ap.add_argument("--question", help="用 ask.py 生成教材回答后推送")
    ap.add_argument("--text", help="直接推送指定文本")
    ap.add_argument("--k", type=int, default=int(getattr(bot_config, "BOT_TOPK", 6)),
                    help="--question 时的检索 top_k")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印 payload，不实际发送到群")
    args = ap.parse_args()

    if args.question:
        ans, _hits, _ctx, _n = answer(args.question, k=args.k)
        text = ans
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("无内容可发送。用法见 README_bot.md（第二节之一）。", file=sys.stderr)
        sys.exit(1)
    send(text, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
