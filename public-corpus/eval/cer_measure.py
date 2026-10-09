#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cer_measure.py — 合成扫描版（200 DPI 光栅化 → Vision OCR）逐页 CER。
真值由 prepare_corpus.clean_source + split_pages_by_chars 确定性复现（同源同分页），
因此无需滑动窗口对齐：OCR 第 n 页 ↔ 真值第 n 页 一一对应。
产出 cer_results.json
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
sys.path.insert(0, PC)

from prepare_corpus import clean_source, split_pages_by_chars, SCAN_CHARS_PER_PAGE  # noqa

KB = os.path.dirname(PC)
RAW = os.path.join(PC, "raw")
PAIRS = [("聊斋志异_扫描版", "liaozhai.txt"),
         ("封神演义_扫描版", "fengshen_yanyi.txt")]
N_PAGES = 20
OUT = os.path.join(HERE, "cer_results.json")


def cjk_only(s):
    return "".join(c for c in s if "\u4e00" <= c <= "\u9fff")


def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def pages_of(full_text):
    parts = re.split(r"<<<PAGE (\d+)>>>", full_text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def main():
    import random
    random.seed(42)
    results = {}
    for name, rawf in PAIRS:
        text, _ = clean_source(os.path.join(RAW, rawf))
        truth = split_pages_by_chars(text, SCAN_CHARS_PER_PAGE)
        ocr = pages_of(open(os.path.join(KB, "full-text", f"{name}_全文.txt"),
                            encoding="utf-8").read())
        idx = [i for i in range(1, min(len(truth), max(ocr)) + 1)
               if len(cjk_only(ocr.get(i, ""))) >= 150]
        sample = random.sample(idx, min(N_PAGES, len(idx)))
        cers = []
        for i in sample:
            o = cjk_only(ocr[i])
            t = cjk_only(truth[i - 1])
            d = levenshtein(o, t)
            cer = d / max(1, len(t))
            cers.append(round(cer, 4))
        cers.sort()
        results[name] = {
            "n_pages": len(sample), "n_pages_total": len(truth),
            "cer_median": round(cers[len(cers) // 2], 4),
            "cer_mean": round(sum(cers) / len(cers), 4),
            "cer_min": cers[0], "cer_max": cers[-1], "per_page": cers,
        }
        print(f"== {name}: CER median={results[name]['cer_median']} "
              f"mean={results[name]['cer_mean']} (n={len(sample)}/{len(truth)} pages)")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
