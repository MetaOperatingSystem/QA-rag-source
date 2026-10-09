#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_public5m.py — 把 public-corpus/prepared/ 下全部异构源合并建库为一个
生产形态语料 public5m（约500万字），复现论文 S1-S5 全管线。

  ingest（含 OCR）→ split_chapters → 合并为 chapters/public5m/（源名前缀）→
  build_chunks（L=500 参考配置）→ BM25 缓存

产出：
  chapters/public5m/*.md + _sources.json（全局来源登记）
  chunks/public5m/chunks.jsonl + bm25.pkl
  public-corpus/stats_build.json（建库统计，供论文表VI/表VIII填写）
"""
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

import ingest          # noqa: E402
import split_chapters  # noqa: E402
import build_chunks    # noqa: E402
from retrieve import load, corpus_path  # noqa: E402

KB = os.path.dirname(HERE)          # knowledge-base/（HERE = knowledge-base/public-corpus）
PREP = os.path.join(HERE, "prepared")
MERGED = os.path.join(KB, "chapters", "public5m")
OUT = os.path.join(KB, "chunks", "public5m")

NAME = "public5m"


def cjk_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def source_list():
    """固定顺序的源清单：(路径, 展示前缀, 格式族)。"""
    srcs = []
    srcs.append((os.path.join(PREP, "红楼梦_文字版.pdf"), "红楼梦", "pdf-text"))
    srcs.append((os.path.join(PREP, "聊斋志异_扫描版.pdf"), "聊斋志异", "pdf-scan"))
    srcs.append((os.path.join(PREP, "封神演义_扫描版.pdf"), "封神演义", "pdf-scan"))
    for f, t in [("三国演义.docx", "三国演义"), ("水浒传.docx", "水浒传"),
                 ("西游记.docx", "西游记"), ("镜花缘.docx", "镜花缘"),
                 ("东周列国志.docx", "东周列国志")]:
        srcs.append((os.path.join(PREP, f), t, "docx"))
    # 政府公文：docx 文件名序 = gov_docs.jsonl 行序
    gov_meta = [json.loads(l) for l in
                open(os.path.join(HERE, "raw", "gov_docs.jsonl"), encoding="utf-8") if l.strip()]
    for i, g in enumerate(gov_meta, 1):
        p = os.path.join(PREP, "gov", f"gov_{i:03d}_*.docx")
        hits = glob.glob(p)
        if not hits:
            continue
        prefix = (g["pcode"] or "公文") + " " + g["title"][:18]
        srcs.append((hits[0], prefix, "docx"))
    # 统计表
    for y in (2025, 2024, 2023, 2022):
        srcs.append((os.path.join(PREP, f"stats_communique_{y}.xlsx"),
                     f"{y}年统计公报", "xlsx"))
    for p in sorted(glob.glob(os.path.join(PREP, "stats_communique_*_table*.csv"))):
        y = re.search(r"(20\d\d)", os.path.basename(p)).group(1)
        tno = re.search(r"table(\d+)", os.path.basename(p)).group(1)
        srcs.append((p, f"{y}公报表{int(tno)}", "csv"))
    return srcs


def main():
    t_all0 = time.time()
    os.makedirs(MERGED, exist_ok=True)
    for f in os.listdir(MERGED):
        if f.endswith(".md"):
            os.remove(os.path.join(MERGED, f))

    srcs = source_list()
    print(f"sources: {len(srcs)}")
    registry = []          # 全局来源登记
    stats = {"pdf-text": [0, 0, 0], "pdf-scan": [0, 0, 0],
             "docx": [0, 0, 0], "xlsx": [0, 0, 0], "csv": [0, 0, 0]}
    # stats[fmt] = [files, pages, cjk]

    for si, (path, prefix, fmt) in enumerate(srcs, 1):
        base = os.path.basename(path)
        if not os.path.exists(path):
            print(f"  [missing] {base}")
            continue
        name = ingest.sanitize(os.path.splitext(base)[0])[:60]
        t0 = time.time()
        try:
            full, meta = ingest.run(path, name=name)
        except Exception as e:
            print(f"  [ingest fail] {base}: {e}", file=sys.stderr)
            continue
        # 跳过重复摄入（同前缀多文件会覆盖 full-text —— 因此这里对 gov/stats
        # 这类同前缀风险源做显式改名保护）
        chapters_dir, index = split_chapters.run(full, name)
        n_merged = 0
        for fn in sorted(f for f in os.listdir(chapters_dir) if f.endswith(".md")):
            fp = os.path.join(chapters_dir, fn)
            first = open(fp, encoding="utf-8").readline().strip()
            m = re.match(r"#\s*第(\d+)章\s*(.*)", first)
            ch_no = int(m.group(1)) if m else 1
            ch_title = (m.group(2).strip() if m else "") or "正文"
            body = open(fp, encoding="utf-8").read().split("\n", 1)[1]
            new_title = f"{prefix}·{ch_title}"[:60]
            out_name = f"S{si:03d}_第{ch_no:03d}章_{new_title}.md"
            with open(os.path.join(MERGED, out_name), "w", encoding="utf-8") as f:
                f.write(f"# 第{ch_no}章 {new_title}\n{body}")
            n_merged += 1
        body_chars = 0
        for fn in glob.glob(os.path.join(MERGED, f"S{si:03d}_*.md")):
            body_chars += cjk_count(open(fn, encoding="utf-8").read())
        stats[fmt][0] += 1
        stats[fmt][1] += meta.get("pages", 0)
        stats[fmt][2] += body_chars
        registry.append({"src": si, "file": base, "prefix": prefix, "format": fmt,
                         "pages": meta.get("pages", 0), "chapters": n_merged,
                         "cjk": body_chars, "ingest_s": round(time.time() - t0, 1)})
        print(f"  [{si:3d}] {prefix[:22]:<24} fmt={fmt:<8} pages={meta.get('pages',0):>5} "
              f"chapters={n_merged:>3} cjk={body_chars:>8,} ({time.time()-t0:.1f}s)")

    with open(os.path.join(MERGED, "_sources.json"), "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=1)

    total_cjk = sum(v[2] for v in stats.values())
    total_files = sum(v[0] for v in stats.values())
    total_pages = sum(v[1] for v in stats.values())
    print(f"\n== 合并完成: {total_files} 源 / {total_pages} 页 / {total_cjk:,} CJK ==")

    # ---- build chunks（参考配置 L=500, overlap=90）----
    t0 = time.time()
    records = build_chunks.main(chapters_dir=MERGED, out_dir=OUT,
                                target=500, overlap=90, book_specific=False,
                                min_seg=12, min_chunk=12)
    chunk_s = time.time() - t0

    # ---- BM25 索引 ----
    t0 = time.time()
    bm = load(chunks_path=corpus_path(NAME),
              cache_path=os.path.join(KB, "chunks", NAME, "bm25.pkl"), force=True)
    index_s = time.time() - t0
    idx_size = os.path.getsize(os.path.join(KB, "chunks", NAME, "bm25.pkl"))

    lens = sorted(r["n_chars"] for r in bm.records)
    out = {
        "name": NAME,
        "format_stats": {k: {"files": v[0], "pages_rows": v[1], "cjk": v[2]}
                         for k, v in stats.items()},
        "totals": {"files": total_files, "pages_rows": total_pages,
                   "cjk": total_cjk, "chunks": len(bm.records),
                   "median_chunk": lens[len(lens) // 2],
                   "mean_chunk": sum(lens) // len(lens)},
        "timings": {"ingest_total_s": round(time.time() - t_all0 - chunk_s - index_s, 1),
                    "chunk_s": round(chunk_s, 1), "index_s": round(index_s, 1)},
        "index_pickle_bytes": idx_size,
    }
    with open(os.path.join(HERE, "stats_build.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
