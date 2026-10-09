#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_sensitivity.py — 表X（参数敏感性）的检索部分：
  L ∈ {300, 500, 800} × k ∈ {3, 5, 8} 的 Recall@k 与切片数。
  L=500 复用 public5m 主库；L=300/800 现场重建（同 overlap 比例 0.18L）。

产出 sensitivity_retrieval.json
（生成时延 Tgen 由 eval_tgen.py 在服务器空闲时补充测量。）
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
KB = os.path.dirname(PC)
sys.path.insert(0, os.path.join(KB, "tools"))
sys.path.insert(0, HERE)

from build_chunks import main as build_main            # noqa: E402
from eval_retrieval import BM25Var, load_questions, find_gold  # noqa: E402

MERGED = os.path.join(KB, "chapters", "public5m")
QF = os.path.join(HERE, "questions.jsonl")
OUT = os.path.join(HERE, "sensitivity_retrieval.json")

GRID = [(300, 3), (300, 5), (500, 5), (500, 8), (800, 5), (800, 8)]


def records_for(L):
    out_dir = os.path.join(KB, "chunks", f"public5m_L{L}")
    if L == 500:
        out_dir = os.path.join(KB, "chunks", "public5m")
    elif not os.path.exists(os.path.join(out_dir, "chunks.jsonl")):
        build_main(chapters_dir=MERGED, out_dir=out_dir,
                   target=L, overlap=round(L * 0.18), book_specific=False,
                   min_seg=12, min_chunk=12)
    return [json.loads(l) for l in
            open(os.path.join(out_dir, "chunks.jsonl"), encoding="utf-8") if l.strip()]


def main():
    qs = [json.loads(l) for l in open(QF, encoding="utf-8") if l.strip()]
    in_scope = [q for q in qs if q["stratum"] in ("routine", "paraphrased")]

    results = {}
    for L in (300, 500, 800):
        recs = records_for(L)
        gold_map = {q["qid"]: find_gold(recs, q["anchor"]) for q in in_scope}
        bm = BM25Var(recs)                     # 生产配置：质量重加权
        for (LL, k) in GRID:
            if LL != L:
                continue
            n_hit = 0
            n_valid = 0
            ranks = []
            for q in in_scope:
                gold = gold_map[q["qid"]]
                if not gold:
                    continue
                ranked = bm.rank(q["question"], topk=8, use_quality=True)
                pos = next((j + 1 for j, i in enumerate(ranked) if i in gold), None)
                n_valid += 1
                if pos is not None and pos <= k:
                    n_hit += 1
                    ranks.append(pos)
            results[f"L{L}_k{k}"] = {
                "L": L, "k": k, "chunks": len(recs),
                "R_at_k": round(n_hit / max(1, n_valid), 3), "n": n_valid,
            }
            print(f"L={L} k={k}: chunks={len(recs)} "
                  f"R@{k}={results[f'L{L}_k{k}']['R_at_k']}", flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
