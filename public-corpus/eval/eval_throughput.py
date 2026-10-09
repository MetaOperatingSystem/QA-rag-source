#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_throughput.py — 表XIII 与并发行为测量：
  串行 / 2 并发 / 4 并发 各 8 题（生产配置），测：
    - 每请求 total_s、eval_s（生成）、prompt_eval_s
    - 聚合吞吐（answers/min）、每请求有效 tok/s
  须在 e2e 实验结束后运行（独占服务器）。

产出 throughput_results.json
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
KB = os.path.dirname(PC)
sys.path.insert(0, os.path.join(KB, "tools"))
sys.path.insert(0, HERE)

from retrieve import load, corpus_path, format_ctx       # noqa: E402
from eval_retrieval import load_questions                # noqa: E402
from eval_ask import SYSTEM_GENERIC, USER_TMPL, call_ollama  # noqa: E402

QF = os.path.join(HERE, "questions.jsonl")
OUT = os.path.join(HERE, "throughput_results.json")
N = 8
LEVELS = (1, 2, 4)


def main():
    qs = [q for q in load_questions() if q["stratum"] == "routine"][:N]
    bm = load(chunks_path=corpus_path("public5m"),
              cache_path=os.path.join(KB, "chunks", "public5m", "bm25.pkl"))
    results = {}
    for level in LEVELS:
        reqs = []
        for q in qs:
            hits = bm.search(q["question"], topk=5)
            ctx, _n = format_ctx(hits, max_chars=4000)
            reqs.append(USER_TMPL.format(context=ctx, question=q["question"]))

        def one(user):
            t0 = time.perf_counter()
            ans, t = call_ollama(SYSTEM_GENERIC, user, 0.2)
            wall = time.perf_counter() - t0
            return {"wall_s": round(wall, 2), "eval_s": round(t["eval_s"], 2),
                    "eval_count": t["eval_count"], "total_s": round(t["total_s"], 2)}

        t0 = time.perf_counter()
        if level == 1:
            rows = [one(u) for u in reqs]
        else:
            with ThreadPoolExecutor(max_workers=level) as ex:
                rows = list(ex.map(one, reqs))
        wall = time.perf_counter() - t0
        toks = sum(r["eval_count"] for r in rows)
        results[f"conc{level}"] = {
            "n": len(rows), "wall_s": round(wall, 1),
            "answers_per_min": round(len(rows) / wall * 60, 2),
            "tok_per_s_aggregate": round(toks / wall, 2),
            "per_request_gen_s": [r["eval_s"] for r in rows],
            "per_request_wall_s": [r["wall_s"] for r in rows],
            "mean_total_s": round(sum(r["total_s"] for r in rows) / len(rows), 2),
        }
        print(f"conc={level}: wall={wall:.0f}s "
              f"answers/min={results[f'conc{level}']['answers_per_min']} "
              f"tok/s={results[f'conc{level}']['tok_per_s_aggregate']}", flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
