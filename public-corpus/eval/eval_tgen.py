#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_tgen.py — 表X 的生成时延 Tgen 部分：
  6 个 (L, k) 组合 × 8 个固定样本题，生产提示词，测 eval_s / eval_count / prompt_eval。
  须在 e2e 实验结束后运行（独占服务器，避免争用干扰时延）。

产出 tgen_results.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
KB = os.path.dirname(PC)
sys.path.insert(0, os.path.join(KB, "tools"))
sys.path.insert(0, HERE)

from retrieve import format_ctx                      # noqa: E402
from eval_retrieval import BM25Var, load_questions   # noqa: E402
from eval_ask import SYSTEM_GENERIC, USER_TMPL, call_ollama  # noqa: E402

QF = os.path.join(HERE, "questions.jsonl")
OUT = os.path.join(HERE, "tgen_results.json")
GRID = [(300, 3), (300, 5), (500, 5), (500, 8), (800, 5), (800, 8)]
N_SAMPLE = 8


def main():
    qs = load_questions()
    sample = [q for q in qs if q["stratum"] == "routine"][:N_SAMPLE]
    results = {}
    for L in (300, 500, 800):
        d = os.path.join(KB, "chunks", "public5m" if L == 500 else f"public5m_L{L}")
        recs = [json.loads(l) for l in
                open(os.path.join(d, "chunks.jsonl"), encoding="utf-8") if l.strip()]
        bm = BM25Var(recs)
        for (LL, k) in GRID:
            if LL != L:
                continue
            gens, prompts, ptoks = [], [], []
            for q in sample:
                ranked = bm.rank(q["question"], topk=k, use_quality=True)
                hits = [(recs[i], 0.0) for i in ranked]
                ctx, n = format_ctx(hits, max_chars=4000)
                user = USER_TMPL.format(context=ctx, question=q["question"])
                ans, t = call_ollama(SYSTEM_GENERIC, user, 0.2)
                gens.append(t["eval_s"])
                prompts.append(t["prompt_eval_s"])
                ptoks.append(t["prompt_eval_count"])
            gens_s = sorted(gens)
            results[f"L{L}_k{k}"] = {
                "L": L, "k": k, "n": len(sample),
                "tgen_s_median": round(gens_s[len(gens)//2], 2),
                "tgen_s_mean": round(sum(gens)/len(gens), 2),
                "prompt_eval_s_median": round(sorted(prompts)[len(prompts)//2], 2),
                "prompt_tok_median": sorted(ptoks)[len(ptoks)//2],
            }
            print(f"L={L} k={k}: Tgen_med={results[f'L{L}_k{k}']['tgen_s_median']}s "
                  f"prompt={results[f'L{L}_k{k}']['prompt_eval_s_median']}s "
                  f"({results[f'L{L}_k{k}']['prompt_tok_median']} tok)", flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
