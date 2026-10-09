#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段3：章节 → RAG 切片（面向 qwen2.5:7b-instruct-q4_K_M 优化）

设计要点：
  - 目标 500 字 / 片，重叠 90 字：top_k=5 时约 2500 字，留足生成余量
  - 先按小节切，再按句切，保证语义完整
  - 每片附「章节 > 小节」面包屑，帮助 4bit 模型定位
  - 自动抽取关键词（TF-IDF 风格）增强 BM25 检索
  - 质量打分：过滤图表 OCR 噪声片

用法（默认 = 《理解深度学习》主库，行为不变）：
    python3 build_chunks.py

通用语料（新源，跳过主库专属逻辑）：
    python3 build_chunks.py --chapters-dir chapters/某表 --out-dir chunks/某表 --no-book-specific
"""
import re, os, json, math, collections, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)            # package root (this file lives in <root>/tools/)
CHDIR = os.path.join(KB, "chapters")
OUT = os.path.join(KB, "chunks")

TARGET = 500      # 目标片长（中文字符）
MIN_SIZE = 160    # 过短则与下一片合并
OVERLAP = 90      # 相邻片重叠
MAX_SIZE = 900    # 硬上限

# 小节标题：编号 + 至少一个汉字（可过滤图表坐标轴数字如 "2.0 0.0"）
SEC_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?[ 　]+([^\s]*[\u4e00-\u9fff][^\s]*.{0,36})$")
PAGE_RE = re.compile(r"<!-- p\.(\d+) -->")

STOP = set("""的 了 是 在 和 与 及 或 为 以 对 从 到 把 被 而 且 则 若 如 使 由 于
这 那 其 之 中 上 下 个 们 它 他 她 我 你 有 会 能 可 要 就 也 还 很 更 最 不 无 非
一个 我们 可以 这个 那个 因为 所以 但是 如果 通过 进行 使用 由于 因此 例如 表示
图 表 式 章 节 问题 小结 注释 本章小结 参考文献 理解深度学习 如下 其中 称为 部分""".split())


def repair_sections(text, ch_no):
    """修复丢失章号前缀的小节标题： '1 问题定义' -> '7.1 问题定义'"""
    out, seen = [], set()
    for line in text.split("\n"):
        m = SEC_RE.match(line)
        if not m:
            # 裸号：'1 问题定义'
            m2 = re.match(r"^\s*(\d{1,2})[ 　]+([^\s]*[\u4e00-\u9fff][^\s]*.{0,26})$", line)
            if m2 and len(line.strip()) <= 30 and not line.rstrip().endswith(("。", "，", "、")):
                n, rest = int(m2.group(1)), m2.group(2).strip()
                if 1 <= n <= 20:
                    line = f"{ch_no}.{n} {rest}"
                    m = SEC_RE.match(line)
        if m:
            seen.add(m.group(2))
        out.append(line)
    return "\n".join(out)


def split_sentences(text):
    """按中文句末标点切句，保留标点"""
    parts = re.split(r"(?<=[。！？；])|\n+", text)
    return [p for p in (s.strip() for s in parts) if p]


def _no_space_needed(buf):
    return all(len(b) <= 60 for b in buf)


def pack(sents, target=TARGET, overlap=OVERLAP, max_size=MAX_SIZE):
    """贪心装箱：累积句子直到 >= target，带重叠"""
    chunks, buf = [], []
    cur_len = 0
    for s in sents:
        buf.append(s); cur_len += len(s)
        if cur_len >= target or cur_len >= max_size:
            chunks.append("".join(buf) if _no_space_needed(buf) else "\n".join(buf))
            # 重叠：保留尾部若干字
            tail, tl = [], 0
            for b in reversed(buf):
                if tl + len(b) > overlap and tail:
                    break
                tail.insert(0, b); tl += len(b)
            buf, cur_len = tail, tl
    if buf:
        chunks.append("".join(buf) if _no_space_needed(buf) else "\n".join(buf))
    # 合并过短片
    merged = []
    for c in chunks:
        if merged and len(c) < MIN_SIZE:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def quality(t):
    """质量打分：识别图表 OCR 噪声"""
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if not lines:
        return 0.0, "low"
    long_lines = sum(1 for l in lines if len(l) >= 12)
    punct = sum(1 for l in lines if re.search(r"[。！？，、；：]", l))
    cjk = sum(1 for ch in t if "\u4e00" <= ch <= "\u9fff")
    ratio_cjk = cjk / max(1, len(t))
    score = 0.45 * (long_lines / len(lines)) + 0.35 * (punct / len(lines)) + 0.20 * ratio_cjk
    grade = "high" if score >= 0.62 else ("medium" if score >= 0.42 else "low")
    return round(score, 3), grade


def keywords(text, df, N, topk=8):
    """中文关键词抽取：bigram TF-IDF + 邻接合并（无需分词器）"""
    tf = collections.Counter()
    for run in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for i in range(len(run) - 1):
            tf[run[i:i + 2]] += 1
    eng = collections.Counter()
    for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text):
        w = w.lower()
        if w not in STOP:
            eng[w] += 1

    sc = {}
    for w, c in tf.items():
        if w in STOP or len(w) != 2:
            continue
        sc[w] = c * math.log(N / df.get(w, 1) + 1)
    for w, c in eng.items():
        sc[w] = c * math.log(N / df.get(w, 1) + 1)

    by_head = collections.defaultdict(list)
    for w in list(sc):
        if len(w) == 2:
            by_head[w[0]].append(w)
    by_tail = collections.defaultdict(list)
    for w in list(sc):
        if len(w) == 2:
            by_tail[w[1]].append(w)

    items = sorted(sc.items(), key=lambda x: -x[1])
    used, terms = set(), []
    for w, s in items:
        if w in used:
            continue
        if len(w) > 2:
            used.add(w); terms.append((s, w)); continue
        term = w; used.add(w)
        thr = s * 0.55
        while True:
            nxt = None
            for w2 in by_head.get(term[-1], []):
                if w2 not in used and sc.get(w2, 0) >= thr:
                    if nxt is None or sc[w2] > sc[nxt]:
                        nxt = w2
            if not nxt:
                break
            term += nxt[1]; used.add(nxt)
        while True:
            prv = None
            for w2 in by_tail.get(term[0], []):
                if w2 not in used and sc.get(w2, 0) >= thr:
                    if prv is None or sc[w2] > sc[prv]:
                        prv = w2
            if not prv:
                break
            term = prv[0] + term; used.add(prv)
        terms.append((s, term))

    terms.sort(key=lambda x: -x[0])
    picked = []
    for s, t in terms:
        if len(t) < 2 or t in STOP:
            continue
        if any(t in p or p in t for p in picked):
            continue
        picked.append(t)
        if len(picked) >= topk:
            break
    return picked


def main(chapters_dir=CHDIR, out_dir=OUT, target=TARGET, overlap=OVERLAP,
         max_size=MAX_SIZE, book_specific=True, min_seg=40, min_chunk=60):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(chapters_dir) if f.endswith(".md"))
    print("章节文件:", len(files))

    records = []
    for fn in files:
        path = os.path.join(chapters_dir, fn)
        text = open(path, encoding="utf-8").read()
        head0 = text.split("\n")[0]
        if book_specific and fn.startswith("附录"):
            ch_no, ch_title = 99, "附录与后置资料"
        elif fn.startswith("第00章"):
            ch_no, ch_title = 0, "前言、译者序与目录"
        else:
            m = re.match(r"#\s*第(\d+)章\s*(.*)", head0)
            ch_no = int(m.group(1)) if m else 0
            ch_title = m.group(2).strip() if m else fn.replace(".md", "")

        # 目录页（仅主库：p.17-23 为纯页码索引，不参与切片）
        if book_specific and ch_no == 0:
            keep = []
            for blk in text.split("<!-- p."):
                if not blk.strip():
                    continue
                mm = re.match(r"(\d+)", blk)
                if mm and 17 <= int(mm.group(1)) <= 23:
                    continue
                keep.append(("<!-- p." + blk) if mm else blk)
            text = "".join(keep)

        text = repair_sections(text, ch_no)

        lines = text.split("\n")
        segs, cur_sec, cur_sec_t, buf = [], "", "", []
        page_now, sec_pages = None, []
        for line in lines:
            pm = PAGE_RE.search(line)
            if pm:
                page_now = int(pm.group(1))
                if not sec_pages or sec_pages[-1] != page_now:
                    sec_pages.append(page_now)
                continue
            sm = SEC_RE.match(line)
            if sm and len(line.strip()) <= 40:
                if buf:
                    segs.append((cur_sec, cur_sec_t, "\n".join(buf), list(sec_pages)))
                    buf = []
                cur_sec = f"{sm.group(1)}.{sm.group(2)}" + (f".{sm.group(3)}" if sm.group(3) else "")
                cur_sec_t = sm.group(4).strip()
                sec_pages = [page_now] if page_now else []
                buf.append(line)
            else:
                buf.append(line)
        if buf:
            segs.append((cur_sec, cur_sec_t, "\n".join(buf), list(sec_pages)))

        for sec, sec_t, body, pages in segs:
            body = body.strip()
            if len(body) < min_seg:
                continue
            sents = split_sentences(body)
            for c in pack(sents, target=target, overlap=overlap, max_size=max_size):
                c = c.strip()
                if len(c) < min_chunk:
                    continue
                records.append({
                    "id": "",
                    "chapter": ch_no,
                    "chapter_title": ch_title,
                    "section": sec,
                    "section_title": sec_t,
                    "page_start": min(pages) if pages else None,
                    "page_end": max(pages) if pages else None,
                    "text": c,
                })

    print("原始切片数:", len(records))

    N = len(records)
    df = collections.Counter()
    for r in records:
        t = set()
        for run in re.findall(r"[\u4e00-\u9fff]{2,}", r["text"]):
            t.update(run[i:i + 2] for i in range(len(run) - 1))
        t.update(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", r["text"]))
        df.update(t)
    print("bigram 词表规模:", len(df))

    for idx, r in enumerate(records, 1):
        q, grade = quality(r["text"])
        r["quality"] = q
        r["grade"] = grade
        r["n_chars"] = len(r["text"])
        r["keywords"] = keywords(r["text"], df, N)
        r["id"] = f"c{r['chapter']:02d}-{idx:04d}"

    with open(os.path.join(out_dir, "chunks.jsonl"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "chunks.txt"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(f"【{r['id']}】第{r['chapter']}章 {r['chapter_title']}"
                    + (f" > {r['section']} {r['section_title']}" if r["section"] else "")
                    + (f" (p.{r['page_start']})" if r["page_start"] else "") + "\n"
                    + r["text"] + "\n\n")

    g = collections.Counter(r["grade"] for r in records)
    lens = sorted(r["n_chars"] for r in records)
    print("\n=== 切片统计 ===")
    print("总数:", len(records))
    print("质量分布:", dict(g))
    if lens:
        print(f"长度 中位={lens[len(lens)//2]}  均值={sum(lens)//len(lens)}  "
              f"min={lens[0]}  max={lens[-1]}")
    print("按章:")
    by = collections.Counter(r["chapter"] for r in records)
    for c in sorted(by):
        print(f"  第{c:>3}章: {by[c]:>3} 片")
    return records


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="章节 → RAG 切片")
    ap.add_argument("--chapters-dir", default=CHDIR, help="章节 md 目录")
    ap.add_argument("--out-dir", default=OUT, help="切片输出目录")
    ap.add_argument("--target", type=int, default=TARGET, help="目标片长")
    ap.add_argument("--overlap", type=int, default=OVERLAP, help="重叠")
    ap.add_argument("--max-size", type=int, default=MAX_SIZE, help="硬上限")
    ap.add_argument("--book-specific", dest="book_specific", action="store_true", default=True,
                    help="启用《理解深度学习》专属逻辑（目录页裁剪/附录章号）")
    ap.add_argument("--no-book-specific", dest="book_specific", action="store_false",
                    help="通用语料：跳过主库专属逻辑")
    a = ap.parse_args()
    main(chapters_dir=a.chapters_dir, out_dir=a.out_dir, target=a.target,
         overlap=a.overlap, max_size=a.max_size, book_specific=a.book_specific)
