#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_sources_md.py — 从 raw 元数据生成 SOURCES.md（全部公开来源 + URL + 许可依据）"""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "SOURCES.md")

BOOKS = [
    ("红楼梦", "集藏/小说/红楼梦.txt"),
    ("三国演义", "集藏/演义/三国演义.txt"),
    ("水浒传", "集藏/小说/水浒传.txt"),
    ("西游记", "集藏/小说/西游记.txt"),
    ("聊斋志异", "集藏/小说/聊斋志异.txt"),
    ("封神演义", "集藏/演义/封神演义.txt"),
    ("镜花缘", "集藏/小说/镜花缘.txt"),
    ("东周列国志", "集藏/演义/东周列国志.txt"),
    ("儒林外史", "集藏/小说/儒林外史.txt"),
]
REPO = "garychowcmu/daizhigev20"
STATS = [
    (2025, "https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html"),
    (2024, "https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html"),
    (2023, "https://www.stats.gov.cn/sj/zxfb/202402/t20240229_1947915.html"),
    (2022, "https://www.stats.gov.cn/sj/zxfb/202302/t20230206_1902000.html"),
]


def cjk(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def main():
    lines = ["# 公开语料来源清单（public5m，≈500 万汉字）", "",
             "全部资源来自互联网公开渠道，获取日期 2026-09-23。",
             "本清单为论文实验语料的完整出处登记。", ""]

    lines += ["## 一、公有领域书籍（9 种，约 489 万字）", "",
              f"- 仓库：GitHub `{REPO}`（殆知阁古代文献 v20）",
              f"  - 仓库主页：<https://github.com/{REPO}>",
              "  - 文件获取地址（CDN，与仓库内容一致）：`https://cdn.jsdelivr.net/gh/"
              + REPO + "@master/<路径>`",
              "  - 原始地址：`https://raw.githubusercontent.com/" + REPO
              + "/master/<路径>`",
              "- 许可依据：所收均为公有领域（public domain）古代文献，"
              "文本数字化整理版在仓库《使用须知》中声明自由传播。",
              "- 语料中用途：红楼梦→文字版 PDF；聊斋志异、封神演义→合成扫描版 PDF"
              "（200 DPI 光栅化后走 macOS Vision OCR 路径）；其余 5 种→docx。"
              "（《儒林外史》仅下载备查，未入最终语料。）", "",
              "| 书名 | 仓库路径 | 入库形式 | 汉字数 |", "|---|---|---|---|"]
    for name, path in BOOKS:
        fn = {"红楼梦": "hongloumeng", "三国演义": "sanguo_yanyi", "水浒传": "shuihu_zhuan",
              "西游记": "xiyouji", "聊斋志异": "liaozhai", "封神演义": "fengshen_yanyi",
              "镜花缘": "jinghua_yuan", "东周列国志": "dongzhou_lieguo",
              "儒林外史": "rulinwaishi"}[name]
        p = os.path.join(RAW, f"{fn}.txt")
        n = cjk(open(p, encoding="utf-8").read()) if os.path.exists(p) else 0
        used = "备查" if name == "儒林外史" else (
            "文字版PDF" if name == "红楼梦" else
            ("扫描版PDF+OCR" if name in ("聊斋志异", "封神演义") else "docx"))
        lines.append(f"| {name} | {path} | {used} | {n:,} |")

    docs = [json.loads(l) for l in
            open(os.path.join(RAW, "gov_docs.jsonl"), encoding="utf-8") if l.strip()]
    lines += ["", "## 二、国务院政策文件（180 篇，约 63 万字）", "",
              "- 来源：中国政府网（www.gov.cn）政策文件库，国务院及其办公厅公开发布文件",
              "- 检索接口：`https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary_gw`",
              "- 许可依据：政府公开信息（《政府信息公开条例》），公开传播",
              "- 入库形式：正文抽取后转为 docx", "",
              f"共 {len(docs)} 篇，逐篇出处如下：", "",
              "| # | 发文字号 | 标题 | 发布时间 | 原文 URL |", "|---|---|---|---|---|"]
    for i, d in enumerate(docs, 1):
        lines.append(f"| {i} | {d.get('pcode') or '—'} | {d['title'][:40]} | "
                     f"{d.get('pubtime','—')[:10]} | {d['url']} |")

    lines += ["", "## 三、国家统计公报数据表（4 个年度，126 CSV + 4 XLSX）", "",
              "- 来源：国家统计局（stats.gov.cn）年度国民经济和社会发展统计公报",
              "- 许可依据：政府公开信息", "",
              "| 年度 | 公报 URL | 入库文件 |", "|---|---|---|"]
    for y, url in STATS:
        lines.append(f"| {y} | {url} | stats_communique_{y}.xlsx + 32 张表 CSV |")

    total = 0
    for name, _p in BOOKS:
        pass
    lines += ["", "## 四、合计", "",
              "语料总量（入库后按格式族统计，见 `stats_build.json`）：",
              "318 个源文件 / 7,591 逻辑页（行）/ 4,976,658 汉字 / 14,076 切片。",
              "",
              f"生成时间：{time.strftime('%Y-%m-%d %H:%M')}"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"saved -> {OUT} ({len(lines)} lines, {len(docs)} gov docs)")


if __name__ == "__main__":
    main()
