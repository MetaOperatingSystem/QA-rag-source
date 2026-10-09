#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键建库：把任意异构源 → 可检索语料（ingest → split_chapters → build_chunks → 缓存）

这是面向「多源数据」的端到端入口。第一步（ingest）自动适配：
  扫描 PDF / 文字 PDF / Word(.docx/.doc) / Excel(.xlsx/.xls) / CSV / 纯文本 / Markdown

产物（均以语料名为命名空间，绝不覆盖主库《理解深度学习》）：
  full-text/<name>_全文.txt
  chapters/<name>/第NN章_标题.md
  chunks/<name>/chunks.jsonl  +  chunks/<name>/bm25.pkl（检索缓存）

用法：
  python3 build_corpus.py 某书.pdf
  python3 build_corpus.py 销售表.xlsx --name 销售数据
  python3 build_corpus.py 讲义.docx --type docx
"""
import os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ingest, split_chapters, build_chunks
from retrieve import load, corpus_path


def main():
    ap = argparse.ArgumentParser(description="一键建库：异构源 → 可检索语料")
    ap.add_argument("source", help="源文件路径")
    ap.add_argument("--name", help="语料名（默认取文件名）")
    ap.add_argument("--type", choices=["auto", "pdf", "docx", "doc", "xlsx", "xls",
                                        "csv", "txt", "md"], default="auto")
    ap.add_argument("--ocr-bin", help="已编译的 ocr 二进制（扫描 PDF 用）")
    ap.add_argument("--target", type=int, default=400, help="切片目标长度（通用源默认 400）")
    ap.add_argument("--overlap", type=int, default=60, help="切片重叠（通用源默认 60）")
    ap.add_argument("--min-seg", type=int, default=12,
                    help="段最小字符（低于则丢弃，通用源默认 12，适配小表格/短章）")
    ap.add_argument("--min-chunk", type=int, default=12, help="切片最小字符")
    ap.add_argument("--skip-ingest", action="store_true",
                    help="跳过摄入（若 full-text 已存在），直接分章+切片")
    a = ap.parse_args()

    forced = None if a.type == "auto" else a.type

    if a.skip_ingest:
        name = a.name or ingest.sanitize(os.path.splitext(os.path.basename(a.source))[0])
        full = os.path.join(KB, "full-text", f"{name}_全文.txt")
        if not os.path.exists(full):
            print("skip-ingest 但找不到", full, file=sys.stderr); sys.exit(1)
        meta = {"name": name}
    else:
        full, meta = ingest.run(a.source, name=a.name, forced=forced, ocr_bin=a.ocr_bin)
        name = meta["name"]

    print("\n[2/4] 分章 …")
    chapters_dir, _ = split_chapters.run(full, name)

    print("\n[3/4] 切片 …")
    out_dir = os.path.join(KB, "chunks", name)
    build_chunks.main(chapters_dir=chapters_dir, out_dir=out_dir,
                      target=a.target, overlap=a.overlap, book_specific=False,
                      min_seg=a.min_seg, min_chunk=a.min_chunk)

    print("\n[4/4] 重建检索缓存 …")
    cache_path = os.path.join(KB, "chunks", name, "bm25.pkl")
    bm = load(chunks_path=corpus_path(name), cache_path=cache_path, force=True)
    print(f"缓存完成，索引片数: {len(bm.records)}")

    print("\n=== 建库完成 ===")
    print(f"  语料名 : {name}")
    print(f"  全文   : full-text/{name}_全文.txt")
    print(f"  章节   : chapters/{name}/  ({len(os.listdir(chapters_dir))-1} 章)")
    print(f"  切片   : chunks/{name}/chunks.jsonl  ({len(bm.records)} 片)")
    print(f"\n查询示例:")
    print(f"  python3 retrieve.py \"你的问题\" --corpus {name}")
    print(f"  python3 ask.py \"你的问题\" --corpus {name}")


if __name__ == "__main__":
    main()
