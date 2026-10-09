#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地大模型问答 —— 对接 qwen2.5:7b-instruct-q4_K_M

支持三种后端（auto 会自动探测）:
  1. openai   Ollama 的 OpenAI 兼容层  /v1/chat/completions   ← 默认，WorkBuddy 已配置的即此接口
  2. ollama   Ollama 原生              /api/chat
  3. llamacpp llama.cpp server         /completion

已实测环境:
  - 端点   http://192.168.1.75:11434
  - 模型   qwen2.5:7b-instruct-q4_K_M (7.6B, Q4_K_M)
  - 上下文 32768 tokens   → 可放心使用 top_k=6~10
  - 速度   约 6 tokens/s → 默认开启流式输出，避免长时间无反馈

针对 4bit-7B 的提示词工程:
  - 指令短、显式（7B 对长指令遵循度下降）
  - 强制「资料不足时直说」，抑制幻觉
  - 低温 (0.2)、限制生成长度

用法:
    python ask.py "反向传播的正向传递做什么？"
    python ask.py "解释残差连接" -k 8 --temp 0.1
    python ask.py "卷积的不变性" --chapter 10
    python ask.py "..." --no-stream                # 关闭流式
    python ask.py "..." --show-context             # 打印喂给模型的上下文
    python ask.py "..." --url http://192.168.1.75:11434 --backend openai
"""
import json, os, sys, time, argparse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from retrieve import load, format_ctx, corpus_path  # noqa: E402

DEFAULT_URL = os.environ.get("KB_OLLAMA_URL", "http://192.168.1.75:11434")
DEFAULT_MODEL = os.environ.get("KB_MODEL", "qwen2.5:7b-instruct-q4_K_M")

SYSTEM_BOOK = """你是《理解深度学习》（Simon J.D. Prince 著）的教材助理工。
严格按以下规则回答：
1. 只使用【资料】中的信息，禁止使用资料外的知识，禁止推测。
2. 若【资料】不足以回答，只输出一句：资料中未涉及该问题。
3. 【资料】由扫描识别生成，可能夹杂图表标签、子图编号、坐标轴数字等无意义碎片（例如「残差连接无残差连接（a）（b）」）。忽略这些碎片，不要把它们写进答案。
4. 回答简明，控制在 200 字以内，用中文。
5. 结尾用一行标注来源，格式：来源：第X章 章节名。"""

SYSTEM_GENERIC = """你是一个本地知识库助理工，严格依据【资料】回答。
规则：
1. 只使用【资料】中的信息，禁止使用资料外的知识，禁止推测。
2. 若【资料】不足以回答，只输出一句：资料中未涉及该问题。
3. 回答简明，控制在 200 字以内，用中文。
4. 结尾用一行标注来源（章 / 表 / 页号）。"""

USER_TMPL = """【资料】
{context}

【问题】
{question}"""


# ---------------------------------------------------------------- HTTP
def http_post(url, payload, timeout=600, stream=False):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def get_json(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def alive(url, path=""):
    return get_json(url + path, timeout=4) is not None


# ---------------------------------------------------------------- 后端
def stream_openai(url, model, system, user, temp, max_tokens):
    """OpenAI 兼容层：SSE 流式"""
    payload = {
        "model": model, "stream": True,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": temp, "max_tokens": max_tokens, "top_p": 0.85,
    }
    buf = []
    with http_post(f"{url}/v1/chat/completions", payload) as r:
        for raw in r:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                d = json.loads(body)
            except json.JSONDecodeError:
                continue
            delta = (d.get("choices") or [{}])[0].get("delta") or {}
            piece = delta.get("content", "")
            if piece:
                buf.append(piece)
                sys.stdout.write(piece)
                sys.stdout.flush()
    print()
    return "".join(buf)


def call_openai(url, model, system, user, temp, max_tokens):
    payload = {
        "model": model, "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": temp, "max_tokens": max_tokens, "top_p": 0.85,
    }
    with http_post(f"{url}/v1/chat/completions", payload) as r:
        d = json.loads(r.read().decode("utf-8"))
    return (d["choices"][0]["message"]["content"] or "").strip()


def call_ollama(url, model, system, user, temp, max_tokens):
    payload = {
        "model": model, "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": temp, "num_predict": max_tokens,
                    "top_p": 0.85, "repeat_penalty": 1.1},
    }
    with http_post(f"{url}/api/chat", payload) as r:
        d = json.loads(r.read().decode("utf-8"))
    return ((d.get("message") or {}).get("content") or "").strip()


def call_llamacpp(url, system, user, temp, max_tokens):
    # Qwen 系列使用 ChatML，需手工拼接
    prompt = (f"<|im_start|>system\n{system}<|im_end|>\n"
              f"<|im_start|>user\n{user}<|im_end|>\n"
              f"<|im_start|>assistant\n")
    payload = {
        "prompt": prompt, "temperature": temp, "n_predict": max_tokens,
        "top_p": 0.85, "repeat_penalty": 1.1,
        "stop": ["<|im_end|>", "<|endoftext|>"],
    }
    with http_post(f"{url}/completion", payload) as r:
        d = json.loads(r.read().decode("utf-8"))
    return (d.get("content") or "").strip()


# ---------------------------------------------------------------- 重试封装
def backend_call(backend, url, model, system, user, temp, max_tokens, no_stream):
    """带限流/服务繁忙自动重试的生成调用。

    观察到的真实错误:
      - 429 使用量超出频率限制（云端代理 Ollama 会限流）
      - 500 the model provider is temporarily unavailable
      - 503 服务繁忙
    这些属于瞬时/限流问题，指数退避后通常可恢复。
    """
    last = None
    for attempt in range(4):
        try:
            if backend == "openai":
                if no_stream:
                    return call_openai(url, model, system, user, temp, max_tokens)
                return stream_openai(url, model, system, user, temp, max_tokens)
            if backend == "ollama":
                ans = call_ollama(url, model, system, user, temp, max_tokens)
                print(ans)
                return ans
            ans = call_llamacpp(url, system, user, temp, max_tokens)
            print(ans)
            return ans
        except urllib.error.HTTPError as e:
            code = getattr(e, "code", 0)
            if code in (429, 500, 503) and attempt < 3:
                wait = 5 * (2 ** attempt)
                try:
                    detail = e.read().decode("utf-8", "ignore")[:160]
                except Exception:
                    detail = ""
                print(f"\n[限流/繁忙 {code}] 第 {attempt + 1} 次重试，"
                      f"{wait}s 后… {detail}", file=sys.stderr)
                time.sleep(wait)
                last = e
                continue
            raise
    raise last


# ---------------------------------------------------------------- 主流程
def detect(url):
    if alive(url, "/v1/models"):
        return "openai"
    if alive(url, "/api/tags"):
        return "ollama"
    if alive(url, "/health") or alive(url, "/props"):
        return "llamacpp"
    return None


def answer(question, k=6, chapter=None, temp=0.2, max_tokens=512,
           max_chars=4000, url=DEFAULT_URL, model=DEFAULT_MODEL,
           backend="auto", no_stream=False, chunks=None, corpus=None,
           all_corpora=False):
    """RAG + 本地模型问答核心（CLI 与机器人共用）。

    返回 (ans, hits, context, n)：答案文本、检索命中列表、上下文、命中片数。
    多语料：传入 corpus=<name> / chunks=<path> / all_corpora=True 查询指定或合并语料。
    """
    cp = chunks or (corpus_path(corpus) if corpus else None)
    bm = load(chunks_path=cp, all_corpora=all_corpora)
    hits = bm.search(question, topk=k, chapter=chapter)
    if not hits:
        return "未检索到相关资料。请换用更贴近原文的措辞。", hits, "", 0
    context, n = format_ctx(hits, max_chars=max_chars)
    user = USER_TMPL.format(context=context, question=question)
    system = SYSTEM_GENERIC if (corpus or all_corpora) else SYSTEM_BOOK
    if backend == "auto":
        backend = detect(url)
        if not backend:
            raise RuntimeError(f"未探测到推理服务: {url}")
    ans = backend_call(backend, url, model, system, user,
                       temp, max_tokens, no_stream)
    return ans, hits, context, n


def main():
    ap = argparse.ArgumentParser(description="《理解深度学习》本地问答")
    ap.add_argument("question", help="要问的问题")
    ap.add_argument("-k", "--topk", type=int, default=6, help="检索片数(默认6)")
    ap.add_argument("--chapter", type=int, default=None, help="限定章号")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"模型名(默认 {DEFAULT_MODEL})")
    ap.add_argument("--backend", choices=["auto", "openai", "ollama", "llamacpp"], default="auto")
    ap.add_argument("--url", default=DEFAULT_URL, help=f"服务地址(默认 {DEFAULT_URL})")
    ap.add_argument("--temp", type=float, default=0.2)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--max-chars", type=int, default=4000, help="上下文预算(默认4000字)")
    ap.add_argument("--no-stream", action="store_true", help="关闭流式输出")
    ap.add_argument("--show-context", action="store_true")
    ap.add_argument("--corpus", help="指定子语料名（chunks/<name>/chunks.jsonl）")
    ap.add_argument("--chunks", help="显式切片文件路径")
    ap.add_argument("--all", action="store_true", help="合并主库 + 所有子语料检索")
    a = ap.parse_args()

    try:
        ans, hits, context, n = answer(
            a.question, k=a.topk, chapter=a.chapter, temp=a.temp,
            max_tokens=a.max_tokens, max_chars=a.max_chars,
            url=a.url, model=a.model, backend=a.backend, no_stream=a.no_stream,
            chunks=a.chunks, corpus=a.corpus, all_corpora=a.all)
    except RuntimeError as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.HTTPError as e:
        code = getattr(e, "code", 0)
        print(f"\n请求失败 (HTTP {code}) {a.url}。", file=sys.stderr)
        if code == 429:
            print("原因：接口频率限制。建议：① 调大重试前等待；"
                  "② 换用真正本机部署的 Ollama（无此限制）；"
                  "③ 降低调用频率。", file=sys.stderr)
        elif code in (500, 503):
            print("原因：模型服务暂时不可用，稍后重试。", file=sys.stderr)
        sys.exit(3)
    except urllib.error.URLError as e:
        print(f"\n连接失败 {a.url}: {e}", file=sys.stderr)
        sys.exit(3)
    except KeyError as e:
        print(f"\n响应格式异常，缺少字段 {e}。请检查模型名是否正确。", file=sys.stderr)
        sys.exit(4)

    if a.show_context:
        print("=" * 70)
        print(context)
        print("=" * 70, f"\n上下文 {len(context)} 字 / {n} 片\n")

    if a.no_stream:
        print("\n【回答】\n" + ans)

    print("\n" + "-" * 70)
    srcs = []
    for r, _ in hits:
        t = f"第{r['chapter']}章 {r['chapter_title']}"
        if r.get("section"):
            t += f" / {r['section']} {r.get('section_title','')}"
        if r.get("page_start"):
            t += f" (p.{r['page_start']})"
        if t not in srcs:
            srcs.append(t)
    print("参考切片: " + " | ".join(srcs[:6]))


if __name__ == "__main__":
    main()
