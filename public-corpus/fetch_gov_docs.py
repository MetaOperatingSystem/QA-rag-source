#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_gov_docs.py — 从中国政府网政策文件库抓取公开公文全文。

依据：《中华人民共和国著作权法》第五条，法律、法规，国家机关的决议、
决定、命令和其他具有立法、行政、司法性质的文件及其官方正式译文，
不适用本法。国务院及其办公厅文件属行政性质官方文件。

接口：https://sousuo.www.gov.cn/search-gov/data  (公开 JSON)
产出：raw/gov_docs.jsonl   每行 {title,pcode,pubtime,url,text,cjk}
"""
import json
import os
import re
import html
import sys
import time
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(RAW, "gov_docs.jsonl")

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko)"}

API = ("https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary_gw"
       "&q={q}&timetype=timeqb&sort=pubtime&sortType=1&searchfield=title"
       "&p={p}&n=20&inpro=&dup=&orpro=")

QUERIES = [("", 4), ("教育", 3), ("高等学校", 2), ("职业", 2)]
SLEEP_LIST = 1.0
SLEEP_DOC = 0.6


def get(url, timeout=25, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")


def cjk_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def extract_body(page):
    m = re.search(r'<div[^>]*class="pages_content"[^>]*>(.*?)</div>\s*<!--', page, re.S)
    if not m:
        m = re.search(r'<div[^>]*id="UCAP-CONTENT"[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return None
    t = re.sub(r"<[^>]+>", "\n", m.group(1))
    t = html.unescape(t)
    t = re.sub(r"[ \t\u3000]+", "", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    return t


def main():
    seen, docs = set(), []
    for q, pages in QUERIES:
        for p in range(1, pages + 1):
            url = API.format(q=urllib.parse.quote(q), p=p)
            try:
                d = json.loads(get(url))
            except Exception as e:
                print(f"[list fail] q={q} p={p}: {e}", file=sys.stderr)
                time.sleep(3)
                continue
            items = ((d.get("searchVO") or {}).get("listVO")) or []
            print(f"[list] q='{q}' p={p}: {len(items)} items")
            for it in items:
                u = it.get("url", "")
                if not u or u in seen:
                    continue
                seen.add(u)
                docs.append(it)
            time.sleep(SLEEP_LIST)

    print(f"\nunique docs: {len(docs)}")
    ok, fail = 0, 0
    with open(OUT, "w", encoding="utf-8") as f:
        for i, it in enumerate(docs):
            u = it["url"]
            try:
                page = get(u)
            except Exception as e:
                print(f"  [doc fail] {u}: {e}", file=sys.stderr)
                fail += 1
                time.sleep(2)
                continue
            body = extract_body(page)
            if not body or len(body) < 500:
                print(f"  [doc empty] {u}")
                fail += 1
                continue
            rec = {
                "title": re.sub(r"\s+", "", it.get("title", "")),
                "pcode": it.get("pcode", ""),
                "pubtime": it.get("pubtimeStr", ""),
                "url": u,
                "chars": len(body),
                "cjk": cjk_count(body),
                "text": body,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ok += 1
            if (i + 1) % 20 == 0:
                print(f"  ... {i+1}/{len(docs)} fetched (ok={ok})")
            time.sleep(SLEEP_DOC)

    total = 0
    with open(OUT, encoding="utf-8") as f:
        for line in f:
            total += json.loads(line)["cjk"]
    print(f"\ndone: ok={ok} fail={fail} total_cjk={total:,}")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
