#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_ask.py — 端到端 RAG 问答实验（表XI 忠实度/拒答、表XII 时延分解）

四种配置：
  production    生产配置（SYSTEM_GENERIC + temp 0.2 + 面包屑上下文）
  no_refusal    去掉强制拒答条款（规则2 改为可据常识作答）
  temp08        温度 0.8
  no_breadcrumb 上下文去掉 [i]第X章 面包屑头，仅裸文本

每题记录：检索时延、prompt_eval / eval（生成）tokens 与时长、答案、自动判分。
产出 e2e_results.json（增量追加，按 config 分组）。
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)          # public-corpus/
KB = os.path.dirname(PC)            # knowledge-base/
sys.path.insert(0, os.path.join(KB, "tools"))

from retrieve import load, corpus_path, format_ctx  # noqa: E402

URL = os.environ.get("KB_OLLAMA_URL", "http://192.168.1.75:11434")
MODEL = os.environ.get("KB_MODEL", "qwen2.5:7b-instruct-q4_K_M")
K = 5
CORPUS = "public5m"

SYSTEM_GENERIC = """你是一个本地知识库助理工，严格依据【资料】回答。
规则：
1. 只使用【资料】中的信息，禁止使用资料外的知识，禁止推测。
2. 若【资料】不足以回答，只输出一句：资料中未涉及该问题。
3. 回答简明，控制在 200 字以内，用中文。
4. 结尾用一行标注来源（章 / 表 / 页号）。"""

SYSTEM_NOREF = """你是一个本地知识库助理工，依据【资料】回答问题。
规则：
1. 优先使用【资料】中的信息。
2. 若【资料】不足以回答，可以结合你的常识合理作答。
3. 回答简明，控制在 200 字以内，用中文。"""

USER_TMPL = """【资料】
{context}

【问题】
{question}"""

REFUSAL_MARKERS = ["资料中未涉及", "未检索到相关资料", "未检索到", "资料中未提供",
                   "资料中未包含", "无法根据资料", "没有找到相关", "资料中没有"]

QF = os.path.join(HERE, "questions.jsonl")
OUT = os.path.join(HERE, "e2e_results.json")


def http_post(url, payload, timeout=900):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def call_ollama(system, user, temp, max_tokens=512):
    payload = {
        "model": MODEL, "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": temp, "num_predict": max_tokens,
                    "top_p": 0.85, "repeat_penalty": 1.1},
    }
    last = None
    for attempt in range(5):
        try:
            with http_post(f"{URL}/api/chat", payload) as r:
                d = json.loads(r.read().decode("utf-8"))
            msg = d.get("message") or {}
            t = {
                "total_s": d.get("total_duration", 0) / 1e9,
                "load_s": d.get("load_duration", 0) / 1e9,
                "prompt_eval_count": d.get("prompt_eval_count", 0),
                "prompt_eval_s": d.get("prompt_eval_duration", 0) / 1e9,
                "eval_count": d.get("eval_count", 0),
                "eval_s": d.get("eval_duration", 0) / 1e9,
            }
            return (msg.get("content") or "").strip(), t
        except urllib.error.HTTPError as e:
            code = getattr(e, "code", 0)
            if code in (429, 500, 503) and attempt < 4:
                wait = 5 * (2 ** attempt)
                print(f"    [HTTP {code}] retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
                last = e
                continue
            raise
    raise last


def context_plain(hits, max_chars=4000):
    """无面包屑消融：裸文本拼接。"""
    out, used = [], 0
    for r, _s in hits:
        block = r["text"]
        if used + len(block) > max_chars:
            break
        out.append(block)
        used += len(block)
    return "\n\n".join(out), len(out)


def is_refusal(ans):
    return any(m in ans for m in REFUSAL_MARKERS)


def grade(q, ans):
    """返回 (refused, keys_hit, grade)。grade ∈ full/partial/wrong/refused/unanswered"""
    if is_refusal(ans):
        return True, [], "refused"
    hits = [k for k in q.get("answer_keys", []) if k in ans]
    if not q.get("answer_keys"):
        return False, hits, ("oos_refused" if False else "answered")
    if len(hits) == len(q["answer_keys"]):
        return False, hits, "full"
    if hits:
        return False, hits, "partial"
    return False, hits, "wrong"


def find_gold(records, anchor):
    return {i for i, r in enumerate(records) if anchor in r["text"]}


def run_config(cfg, qs, bm, records, gold_map):
    sysmap = {"production": (SYSTEM_GENERIC, 0.2, True),
              "no_refusal": (SYSTEM_NOREF, 0.2, True),
              "temp08": (SYSTEM_GENERIC, 0.8, True),
              "no_breadcrumb": (SYSTEM_GENERIC, 0.2, False)}
    system, temp, breadcrumb = sysmap[cfg]
    rows = []
    for qi, q in enumerate(qs, 1):
        t0 = time.perf_counter()
        hits = bm.search(q["question"], topk=K)
        t_ret = time.perf_counter() - t0
        gold = gold_map.get(q["qid"], set())
        rank = next((j + 1 for j, (r, _s) in enumerate(hits)
                     if records.index(r) in gold), None) if gold else None
        if not hits:
            rows.append({"qid": q["qid"], "stratum": q["stratum"],
                         "question": q["question"], "t_ret_s": round(t_ret, 4),
                         "rank": rank, "error": "no_hits",
                         "answer": "未检索到相关资料。请换用更贴近原文的措辞。",
                         "refused": True, "keys_hit": [], "grade": "refused",
                         "timing": None})
            continue
        ctx, n = (format_ctx(hits, max_chars=4000) if breadcrumb
                  else context_plain(hits, max_chars=4000))
        user = USER_TMPL.format(context=ctx, question=q["question"])
        try:
            ans, t = call_ollama(system, user, temp)
        except Exception as e:
            rows.append({"qid": q["qid"], "stratum": q["stratum"],
                         "question": q["question"], "t_ret_s": round(t_ret, 4),
                         "rank": rank, "error": str(e)[:200], "answer": "",
                         "refused": None, "keys_hit": [], "grade": "error",
                         "timing": None})
            continue
        refused, keys_hit, g = grade(q, ans)
        rows.append({"qid": q["qid"], "stratum": q["stratum"],
                     "question": q["question"], "t_ret_s": round(t_ret, 4),
                     "n_ctx_chunks": n, "ctx_chars": len(ctx), "rank": rank,
                     "answer": ans, "refused": refused, "keys_hit": keys_hit,
                     "grade": g, "timing": t})
        print(f"  [{cfg}] {qi}/{len(qs)} {q['qid']} grade={g} "
              f"gen={t['eval_s']:.1f}s/{t['eval_count']}tok rank={rank}",
              flush=True)
    return rows


def summarize(rows):
    ins = [r for r in rows if r["stratum"] in ("routine", "paraphrased")
           and r["grade"] != "error"]
    oos = [r for r in rows if r["stratum"] == "out-of-scope"
           and r["grade"] != "error"]
    def rate(sub, pred): return round(100 * sum(1 for r in sub if pred(r)) / max(1, len(sub)), 1)
    s = {
        "n_inscope": len(ins), "n_oos": len(oos),
        "HR_inscope": rate(ins, lambda r: r["grade"] in ("wrong", "partial")),
        "full_correct_inscope": rate(ins, lambda r: r["grade"] == "full"),
        "RR_inscope": rate(ins, lambda r: r["refused"]),
        "HR_oos": rate(oos, lambda r: not r["refused"]),
        "RR_oos": rate(oos, lambda r: r["refused"]),
        "HR_overall": rate(ins + oos, lambda r: (r["stratum"] == "out-of-scope") != (not r["refused"]) and r["grade"] in ("wrong", "partial", "answered") or (r["stratum"] != "out-of-scope" and r["grade"] in ("wrong", "partial")) or (r["stratum"] == "out-of-scope" and not r["refused"])),
        "RR_overall": rate(ins + oos, lambda r: r["refused"]),
    }
    lat = [r["timing"] for r in rows if r.get("timing")]
    if lat:
        def med(vals): vs = sorted(vals); return round(vs[len(vs)//2], 3)
        s["latency"] = {
            "t_ret_s_med": med([r["t_ret_s"] for r in rows]),
            "prompt_eval_s_med": med([t["prompt_eval_s"] for t in lat]),
            "prompt_tok_med": med([t["prompt_eval_count"] for t in lat]),
            "gen_s_med": med([t["eval_s"] for t in lat]),
            "gen_tok_med": med([t["eval_count"] for t in lat]),
            "tok_per_s_med": med([t["eval_count"] / max(1e-9, t["eval_s"]) for t in lat]),
            "total_s_med": med([t["total_s"] for t in lat]),
        }
    return s


def main(configs):
    qs = [json.loads(l) for l in open(QF, encoding="utf-8") if l.strip()]
    limit = int(os.environ.get("EVAL_LIMIT", "0"))
    if limit:
        qs = qs[:limit]
    in_scope = [q for q in qs if q["stratum"] in ("routine", "paraphrased")]
    records = [json.loads(l) for l in
               open(corpus_path(CORPUS), encoding="utf-8") if l.strip()]
    gold_map = {q["qid"]: find_gold(records, q["anchor"]) for q in in_scope}
    bm = load(chunks_path=corpus_path(CORPUS),
              cache_path=os.path.join(KB, "chunks", CORPUS, "bm25.pkl"))

    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT, encoding="utf-8"))
    for cfg in configs:
        rows = run_config(cfg, qs, bm, records, gold_map)
        results[cfg] = {"rows": rows, "summary": summarize(rows)}
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        print(f"== {cfg} ==\n{json.dumps(results[cfg]['summary'], ensure_ascii=False, indent=1)}")


if __name__ == "__main__":
    cfgs = sys.argv[1:] or ["production"]
    main(cfgs)
