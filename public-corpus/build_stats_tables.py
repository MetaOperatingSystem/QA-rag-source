#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_stats_tables.py — 解析国家统计局《国民经济和社会发展统计公报》
(2022–2025 年度) 页面中的数据表，构建公开数据 xlsx（每年度一个文件，
多工作表）与 csv。

来源（国家统计局官网，公开政府信息）：
  2025: https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html
  2024: https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html
  2023: https://www.stats.gov.cn/sj/zxfb/202402/t20240228_1947915.html
  2022: https://www.stats.gov.cn/sj/zxfb/202302/t20230228_1919011.html
产出：prepared/stats_communique_<year>.xlsx
      prepared/stats_communique_<year>_tableNN.csv
"""
import csv
import os
import re
import html
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PREP = os.path.join(HERE, "prepared")
os.makedirs(PREP, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0"}
YEARS = {
    2025: "https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html",
    2024: "https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html",
    2023: "https://www.stats.gov.cn/sj/zxfb/202402/t20240228_1947915.html",
    2022: "https://www.stats.gov.cn/sj/zxfb/202302/t20230228_1919011.html",
}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def cell_text(c):
    t = re.sub(r"<[^>]+>", "", c)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def parse_tables(page):
    tables = []
    for m in re.finditer(r"<table[^>]*>(.*?)</table>", page, re.S | re.I):
        rows = []
        for rm in re.finditer(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S | re.I):
            cells = [cell_text(c.group(1))
                     for c in re.finditer(r"<t[dh][^>]*>(.*?)</t[dh]>",
                                          rm.group(1), re.S | re.I)]
            if cells and any(cells):
                rows.append(cells)
        if len(rows) >= 2 and len(rows[0]) >= 2:
            tables.append(rows)
    return tables


def cjk_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


from openpyxl import Workbook

grand_rows = grand_chars = 0
for year, url in YEARS.items():
    try:
        page = fetch(url)
    except Exception as e:
        print(f"[fail] {year}: {e}")
        continue
    tables = parse_tables(page)
    nrow = sum(len(t) for t in tables)
    nchar = sum(len(c) for t in tables for r in t for c in r)
    print(f"{year}: tables={len(tables)} rows={nrow} cell-chars={nchar:,}")
    grand_rows += nrow
    grand_chars += nchar

    for i, t in enumerate(tables, 1):
        path = os.path.join(PREP, f"stats_communique_{year}_table{i:02d}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            for row in t:
                w.writerow(row)

    wb = Workbook()
    ws0 = wb.active
    ws0.title = "说明"
    ws0.append(["数据来源", url])
    ws0.append(["名称", f"中华人民共和国{year}年国民经济和社会发展统计公报"])
    ws0.append(["发布机构", "国家统计局"])
    ws0.append(["表数", len(tables)])
    for i, t in enumerate(tables, 1):
        ws = wb.create_sheet(f"表{i:02d}")
        for row in t:
            ws.append(row)
    wb.save(os.path.join(PREP, f"stats_communique_{year}.xlsx"))
    time.sleep(1)

print(f"\nTOTAL: rows={grand_rows:,} cell-chars={grand_chars:,}")
