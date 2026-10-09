# -*- coding: utf-8 -*-
"""
Feishu bot configuration TEMPLATE — WebSocket (long-connection) mode.

HOW TO USE
----------
1. Copy this file to `bot_config.py` in the same directory:
       cp tools/bot_config.example.py tools/bot_config.py
2. Replace the placeholder values below with YOUR OWN Feishu app credentials.
3. (Optional) Instead of creating the file, export the values as environment
   variables — `feishu_bot.py` reads env vars first, then falls back to this file.

SECURITY
--------
The real `bot_config.py` contains secrets and MUST NOT be committed or shared.
Only this `.example.py` template is distributed with the source package.

Create a Feishu 【企业自建应用】, then take App ID / App Secret from
「凭证与基础信息」, and in 「事件订阅」 choose 「使用长连接接收事件」
and add the event `im.message.receive_v1`.
"""
FEISHU_APP_ID = "cli_xxxxxxxxxxxxxxxx"          # <-- replace with your App ID
FEISHU_APP_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxx"  # <-- replace with your App Secret

# Feishu API gateway (mainland China default; for Lark overseas use
# https://open.larksuite.com/open-apis)
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# SDK log level: DEBUG / INFO / WARN / ERROR
FEISHU_LOG_LEVEL = "ERROR"

# Backend model (must match ask.py defaults; change KB_OLLAMA_URL if the
# model runs on a different host)
KB_OLLAMA_URL = "http://192.168.1.75:11434"   # <-- your Ollama / OpenAI-compatible endpoint
KB_MODEL = "qwen2.5:7b-instruct-q4_K_M"

# QA params / rate-limit
BOT_TOPK = 6
BOT_MAX_CHARS = "4000"
BOT_MAX_REPLY = "4000"          # single-reply character cap (~4000 for Feishu text)
BOT_MAX_CONCURRENCY = "1"       # concurrent model calls; keep 1 when backend rate-limits
