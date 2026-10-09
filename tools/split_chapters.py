#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用分章器：把任意规范化全文 → chapters/<name>/第NN章_标题.md

与 build_chapters.py（仅适配《理解深度学习》）不同，本脚本内容驱动、
不写死书名与目录结构，可处理：
  - 文字版 / 扫描版书籍 PDF（含「第 N 章」「Chapter N」）
  - Word / Markdown（含 Markdown 一级标题作为章）
  - Excel / CSV（按「工作表」分章，每张表一章）

输入契约（由 ingest.py 产出）：
  <<<PAGE n>>>     通用逻辑页块
  <<<SHEET 名>>>   电子表工作表边界（可选）

输出：
  <kb>/chapters/<name>/第NN章_标题.md   每章一个文件，含 <!-- p.n --> 页锚点
  <kb>/chapters/<name>/_index.json      章节索引

用法：
  python3 split_chapters.py full-text/某书_全文.txt --name 某书
  python3 split_chapters.py full-text/某表_全文.txt --name 某表
"""
import os, re, json, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)
CHAPTERS = os.path.join(KB, "chapters")

# 章标题识别（页面内任意行，不只顶部）
CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "叁": 3, "两": 2}
CH_HEAD = re.compile(r"^第\s*([0-9０-９]{1,3}|[零一二三四五六七八九十百叁两]+)\s*[章篇部卷回]\s*(.{0,30})$")
EN_HEAD = re.compile(r"^Chapter\s+([0-9]{1,3})[\.\:\s]\s*(.+)$", re.IGNORECASE)
JUAN_HEAD = re.compile(r"^卷\s*([一二三四五六七八九十]{1,3})\s*(.{0,30})$")
MD_H1 = re.compile(r"^#\s+(.+)$")
MD_H2 = re.compile(r"^##\s+(.+)$")
ROMAN = re.compile(r"^[IVXLCDM]{1,7}$")


def cn2int(s):
    """中文数字章号 → int（支持 一~九十九 / 百；阿拉伯数字原样）。"""
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "百" in s:
        a, b = s.split("百", 1)
        return CN_NUM.get(a, 1) * 100 + (cn2int(b) if b else 0)
    if "十" in s:
        a, b = s.split("十", 1)
        left = CN_NUM.get(a, 1) if a else 1
        right = CN_NUM.get(b, 0) if b else 0
        return left * 10 + right
    return sum(CN_NUM.get(c, 0) for c in s)


def split_pages(raw):
    """返回 (sheets, pages)。sheets: list[(name, [page_indices])]；
    pages: dict[page_no] -> text。若无 SHEET 标记，sheets=None。"""
    parts = re.split(r"<<<PAGE\s+(\d+)>>>\n", raw)
    pages = {int(parts[i]): parts[i + 1].strip("\n") for i in range(1, len(parts), 2)}
    sheet_parts = re.split(r"<<<SHEET\s+(.+?)>>>\n", raw)
    sheets = None
    if len(sheet_parts) > 1:
        sheets = []
        for i in range(1, len(sheet_parts), 2):
            name = sheet_parts[i].strip()
            body = sheet_parts[i + 1]
            nums = [int(x) for x in re.findall(r"<<<PAGE\s+(\d+)>>>", body)]
            sheets.append((name, nums))
    return sheets, pages


def detect_heading(line):
    """返回 (ch_no, title) 或 None。"""
    s = line.strip()
    m = CH_HEAD.match(s)
    if m:
        title = m.group(2).strip()
        return cn2int(m.group(1)), (title if title else "")
    m = JUAN_HEAD.match(s)
    if m:
        title = m.group(2).strip()
        return cn2int(m.group(1)), (title if title else "")
    m = EN_HEAD.match(s)
    if m:
        title = m.group(2).strip()
        return int(m.group(1)), title
    return None


def clean_page(text, is_first, head_title):
    """轻量清洗：去掉纯页码行；首段去掉与章标题重复的标题行。"""
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            out.append("")
            continue
        if re.fullmatch(r"\d{1,4}", s) or ROMAN.fullmatch(s):
            continue
        if is_first and head_title and s == head_title:
            continue
        out.append(ln)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out).strip()


def sanitize_title(t):
    t = t.strip().replace("/", "／").replace("\\", "／")
    return re.sub(r"[\\:*?\"<>|]", "_", t)[:40] or "未命名"


def run(full_text_path, name, out_dir=None):
    raw = open(full_text_path, encoding="utf-8").read()
    sheets, pages = split_pages(raw)
    out_dir = out_dir or os.path.join(CHAPTERS, name)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".md"):
            os.remove(os.path.join(out_dir, f))

    chapters = []  # (ch_no, title, [page_nos])

    if sheets:
        # 电子表：每个工作表 = 一章
        for idx, (sname, pnos) in enumerate(sheets, 1):
            title = sanitize_title(sname)
            chapters.append((idx, title, pnos))
    else:
        # 书籍 / Word / Markdown：按标题分章
        order = sorted(pages)
        cur = None  # (ch_no, title, [pnos])
        md_ch = 0
        for pn in order:
            txt = pages[pn]
            head = None
            for ln in txt.split("\n")[:3]:
                h = detect_heading(ln)
                if h:
                    head = h
                    break
            if head is None:
                # Markdown H1 作为章（覆盖中英文之外的情形）
                for ln in txt.split("\n")[:3]:
                    m = MD_H1.match(ln.strip())
                    if m:
                        head = (None, m.group(1).strip())
                        break
            if head:
                ch_no, title = head
                if ch_no is None:
                    md_ch += 1
                    ch_no = 1000 + md_ch  # Markdown 章用大号避免与数字章冲突
                if cur is None or ch_no != cur[0]:
                    if cur:
                        chapters.append(cur)
                    cur = (ch_no, sanitize_title(title), [pn])
                else:
                    cur[2].append(pn)
            else:
                if cur is None:
                    cur = (1, "正文", [pn])
                else:
                    cur[2].append(pn)
        if cur:
            chapters.append(cur)

    if not chapters:
        chapters = [(1, "正文", sorted(pages))]

    index = []
    for ch_no, title, pnos in chapters:
        body = []
        for i, pn in enumerate(pnos):
            t = clean_page(pages[pn], is_first=(i == 0), head_title=(title if i == 0 else ""))
            if t:
                body.append(f"<!-- p.{pn} -->\n{t}")
        text = f"# 第{ch_no}章 {title}\n\n" + "\n\n".join(body) + "\n"
        fn = f"第{ch_no:02d}章_{title}.md"
        open(os.path.join(out_dir, fn), "w", encoding="utf-8").write(text)
        index.append({"章号": ch_no, "标题": title, "起页": pnos[0], "止页": pnos[-1],
                      "页数": len(pnos), "字符数": len(text), "文件": fn})

    meta = {"name": name, "章节数": len(index), "created_at": datetime.datetime.now().isoformat(timespec="seconds")}
    with open(os.path.join(out_dir, "_index.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "chapters": index}, f, ensure_ascii=False, indent=2)

    print(f"[分章] 语料 {name} → {len(index)} 章，输出 {out_dir}")
    for i in index:
        print(f"  第{i['章号']}章 {i['标题']:<20} p{i['起页']}-{i['止页']}  {i['字符数']:>7,}字")
    return out_dir, index


def main():
    ap = argparse.ArgumentParser(description="通用分章：规范化全文 → 章节 md")
    ap.add_argument("full_text", help="ingest.py 产出的 全文.txt 路径")
    ap.add_argument("--name", help="语料名（默认取全文文件名前缀）")
    ap.add_argument("--out-dir", help="章节输出目录（默认 chapters/<name>）")
    a = ap.parse_args()
    if not a.name:
        base = os.path.basename(a.full_text)
        a.name = re.sub(r"_全文\.txt$", "", base)
        a.name = re.sub(r"\.txt$", "", a.name)
    run(a.full_text, a.name, a.out_dir)


if __name__ == "__main__":
    main()
