#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finish_merge_stats.py — merge_public5m.py 崩溃后的收尾：
  1) 重跑 build_chunks（计时，产出与已有一致）
  2) 构建 BM25 缓存（计时）
  3) 从 _sources.json 汇总，写出 stats_build.json（供论文表VI/表VIII）
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)                      # knowledge-base/
sys.path.insert(0, os.path.join(KB, "tools"))

import build_chunks
from retrieve import load, corpus_path

MERGED = os.path.join(KB, "chapters", "public5m")
OUT = os.path.join(KB, "chunks", "public5m")
NAME = "public5m"


def cjk_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def main():
    registry = json.load(open(os.path.join(MERGED, "_sources.json"), encoding="utf-8"))
    stats = {}
    ingest_s = 0.0
    for r in registry:
        f = stats.setdefault(r["format"], {"files": 0, "pages_rows": 0, "cjk": 0})
        f["files"] += 1
        f["pages_rows"] += r["pages"]
        f["cjk"] += r["cjk"]
        ingest_s += r["ingest_s"]

    t0 = time.time()
    records = build_chunks.main(chapters_dir=MERGED, out_dir=OUT,
                                target=500, overlap=90, book_specific=False,
                                min_seg=12, min_chunk=12)
    chunk_s = time.time() - t0

    t0 = time.time()
    bm = load(chunks_path=corpus_path(NAME),
              cache_path=os.path.join(OUT, "bm25.pkl"), force=True)
    index_s = time.time() - t0
    idx_size = os.path.getsize(os.path.join(OUT, "bm25.pkl"))

    lens = sorted(r["n_chars"] for r in bm.records)
    out = {
        "name": NAME,
        "format_stats": stats,
        "totals": {"files": sum(v["files"] for v in stats.values()),
                   "pages_rows": sum(v["pages_rows"] for v in stats.values()),
                   "cjk": sum(v["cjk"] for v in stats.values()),
                   "chunks": len(bm.records),
                   "median_chunk": lens[len(lens) // 2],
                   "mean_chunk": sum(lens) // len(lens)},
        "timings": {"ingest_sum_s": round(ingest_s, 1),
                    "chunk_s": round(chunk_s, 1), "index_s": round(index_s, 1)},
        "index_pickle_bytes": idx_size,
    }
    with open(os.path.join(HERE, "stats_build.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out["totals"], ensure_ascii=False))
    print("timings:", out["timings"], "| index bytes:", idx_size)


if __name__ == "__main__":
    main()
