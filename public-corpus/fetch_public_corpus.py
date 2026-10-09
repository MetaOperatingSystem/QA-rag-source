#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_public_corpus.py — 获取公开中文语料（约500万字），用于替代受版权
保护的《理解深度学习》扫描件，作为论文 Corpus-A 体量替代实验语料。

来源（全部公开、可注明出处）：
  1. 殆知阁古代文献 GitHub 仓库（garychowcmu/daizhigev20）
     - 古典小说（作者逝世远超著作权保护期，属公有领域）
     - 经 jsDelivr CDN 下载（国内可达）
  2. 中国政府网 www.gov.cn 政策文件库
     - 《著作权法》第五条：法律、法规，国家机关的决议、决定、命令
       等官方文件不适用本法 → 公文本身无版权
  3. 国家统计局统计公报（公开数据）→ 由脚本构建 xlsx / csv

产出：
  raw/        原始下载（含 provenance 记录）
  PROVENANCE.md  每份资源的公开地址、体量、许可依据
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

CDN = "https://cdn.jsdelivr.net/gh/garychowcmu/daizhigev20@master/"
REPO_URL = "https://github.com/garychowcmu/daizhigev20/tree/master/"

# (本地文件名, 仓库路径, 展示标题)
BOOKS = [
    ("sanguo_yanyi.txt",  "集藏/演义/三国演义.txt",          "三国演义"),
    ("shuihu_zhuan.txt",  "集藏/小说/水浒传.txt",            "水浒传"),
    ("xiyouji.txt",       "集藏/小说/西游记.txt",            "西游记"),
    ("rulin_waishi.txt",  "集藏/小说/儒林外史.txt",          "儒林外史"),
    ("jinghua_yuan.txt",  "集藏/小说/镜花缘.txt",            "镜花缘"),
    ("fengshen_yanyi.txt","集藏/演义/封神演义.txt",          "封神演义"),
    ("dongzhou_lieguo.txt","集藏/演义/东周列国志.txt",        "东周列国志"),
    ("liaozhai.txt",      "集藏/小说/聊斋志异.txt",          "聊斋志异"),
]

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def cjk_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def fetch(url, timeout=90, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  retry {i+1}: {e}", file=sys.stderr)
            time.sleep(3)
    return None


def fetch_books():
    prov = []
    for fname, path, title in BOOKS:
        out = os.path.join(RAW, fname)
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f"[skip] {title} already downloaded")
        else:
            url = CDN + urllib.parse.quote(path)
            print(f"[get ] {title} ...", flush=True)
            data = fetch(url)
            if data is None:
                print(f"  FAILED: {title}")
                continue
            with open(out, "wb") as f:
                f.write(data)
            time.sleep(1)
        try:
            s = open(out, encoding="utf-8").read()
        except UnicodeDecodeError:
            s = open(out, encoding="gb18030", errors="ignore").read()
        prov.append({
            "file": fname, "title": title, "kind": "book",
            "source": REPO_URL + urllib.parse.quote(path),
            "bytes": os.path.getsize(out),
            "chars": len(s), "cjk": cjk_count(s),
            "license": "public domain (author deceased > 100 yrs); "
                       "digitised text from daizhigev20 open repository",
        })
        print(f"        cjk={prov[-1]['cjk']:,}")
    return prov


if __name__ == "__main__":
    prov = fetch_books()
    with open(os.path.join(RAW, "provenance_books.json"), "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=2)
    total = sum(p["cjk"] for p in prov)
    print(f"\nBOOKS TOTAL CJK: {total:,}")
