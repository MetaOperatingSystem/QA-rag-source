# 飞书群机器人接入指南

把《理解深度学习》知识库问答接入飞书群聊。采用 **B 类 · 企业自建应用机器人（WebSocket 长连接自动回复）**。

> ⚠️ **本知识库仅采用 B 类 · 企业自建应用机器人（WebSocket 长连接自动回复）**
> 对应工具：**`feishu_bot.py`**。已确认：长连接接收事件在飞书后台验证成功。
> （A 类自定义机器人 Webhook 单向推送方案已弃用，相关配置已从 `bot_config.py` 移除。）

## 一、B 类：企业自建应用机器人（可接收 @提问并自动回复）

```
群成员 @机器人
  → 飞书经 wss 长连接推送 im.message.receive_v1（明文）
  → 本机 feishu_bot.py（仅需能访问公网，无需公网 IP / 隧道）
  → answer() 检索 + 调 192.168.1.75:11434（内网，可达）
  → 经「回复消息」API 异步发回群
```

**为什么用长连接而不是 Webhook：** 飞书长连接模式由 SDK 在客户端主动建立 `wss://` 出站连接，
飞书经该隧道推事件。因此**不需要公网 IP、不需要域名、不需要 cloudflared/ngrok/frp 内网穿透**，
也不需要验签 / 解密（传输内置加密，推给开发者的是明文）。这正是你要求的「不用暴露公网」。
前提仅一条：**运行 bot 的机器能访问公网飞书服务器**（局域网能出网即可）。

> 旧版 Webhook 实现（需公网回调地址 + 隧道 + 签名校验）已存档于 `feishu_bot_webhook.py`。

---

## 二、B 类：在飞书创建企业自建应用

1. [飞书开放平台](https://open.feishu.cn/) → 开发者后台 → 创建**企业自建应用**。
2. **凭证与基础信息**：记下 `App ID`、`App Secret`（填入 `bot_config.py`）。
3. **权限管理** → 开通：
   - `im:message`（获取与发送消息）
   - `im:message:send_as_bot`（以机器人身份发消息）
   - `im:message.receive_v1`（接收消息，v2.0，订阅事件时添加）
4. **事件订阅**：
   - 订阅方式选择 **「使用长连接接收事件」**（关键！不要选 Webhook）。
   - 添加事件：**接收消息** `im.message.receive_v1`（v2.0）。
   - 长连接模式无需配置请求地址、无需 Encrypt Key、无需验签。
5. **发布应用** → 创建版本并发布；把机器人**加入目标群**（群设置 → 添加机器人）。
   - 群内默认机器人只接收被 @ 的消息；如需接收全部消息，在事件订阅高级设置里调整（此时
     本 bot 已用 `mentions` 非空判断群聊消息，未 @ 的会被忽略，不会刷屏）。

> 海外版 Lark：把 `FEISHU_API_BASE` 改为 `https://open.larksuite.com/open-apis`。

---

## 三、B 类：填写配置

编辑 `bot_config.py`（已预填你的 App ID / App Secret），只需确认无误；或用环境变量覆盖：

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export KB_OLLAMA_URL=http://192.168.1.75:11434
```

---

## 四、启动 bot（无需任何隧道）

```bash
cd knowledge-base/tools
python3 feishu_bot.py
# 输出：
#   飞书长连接 bot 启动（免公网 / 免内网穿透 / 免验签）
#   APP_ID=cli_aa…  模型=qwen2.5:7b-instruct-q4_K_M  topk=6  并发=1
#   在飞书群内 @机器人 即可提问；后台 wss 长连接持续保活与重连。
```

启动前安装依赖：
```bash
/Users/suweibin/.workbuddy/binaries/python/envs/default/bin/pip install lark-oapi -U
```

> 常驻运行：`nohup python3 feishu_bot.py > bot.log 2>&1 &`；或交给 launchd / systemd 托管。
> 长连接断开 SDK 会自动重连（指数退避），无需人工干预。

---

## 五、群内测试

1. 在群里 **@机器人 反向传播的两个阶段分别做什么？**
2. 机器人应数秒~数十秒内回复答案，并附「— 来源：第X章 …」。
3. 验证连接：启动后控制台若出现 `connected to wss://...` 即长连接建立成功
   （`FEISHU_LOG_LEVEL=INFO` 时可见；也可 `DEBUG` 看完整事件）。

本地自检（不依赖飞书）：用 `ask.py` 直接验证问答内核——
```bash
python3 ask.py "反向传播的两个阶段分别做什么？" -k 5
```

---

## 六、工程要点与已知约束

- **3 秒处理限制**：飞书长连接要求事件回调在 3 秒内返回，否则触发超时重推。
  `do_message` 只做解析与派发（`微秒级`）后立即返回，真正的模型推理在后台线程池执行，
  结果经「回复消息」API 异步发送，不占用回调窗口。
- **限流**：模型端为带频率限制的云端代理，会返回 429。`answer()` 内已做指数退避重试；
  `BOT_MAX_CONCURRENCY=1` 限制并发避免雪崩。群聊高频提问时建议改用**真正本机 Ollama**（无限流）。
- **公式失真**：教材公式经 OCR 失真，涉及推导请对照原书（回复已带页码来源）。
- **仅企业自建应用**：长连接模式不支持商店应用；卡片回调（card.action.trigger）也不支持长连接。
- **多平台复用**：`answer()` 与渠道无关。接入企业微信 / QQ 时只需替换 `feishu_bot.py`
  中的「接收 / 回复」部分，核心问答不变（企业微信同样有 WebSocket / 长轮询能力可复用此思路）。
