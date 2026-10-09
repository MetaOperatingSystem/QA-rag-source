#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段2（修正版）：章节日切分 + 页眉页脚清洗 -> chapters/*.md

判据（三重约束，抗正文交叉引用污染）：
  1. 候选行必须位于页首前 2 行（页眉物理位置）
  2. 候选行长度 <= 22（页眉短，正文长句被排除）
  3. 章号必须单调不减，且跃迁步长 <= 1（章序连续）
"""
import re, os, json

KB = "/Users/suweibin/WorkBuddy/Claw/knowledge-base"
SRC = os.path.join(KB, "full-text/理解深度学习_OCR全文.txt")
CHDIR = os.path.join(KB, "chapters")
os.makedirs(CHDIR, exist_ok=True)
os.makedirs(os.path.join(KB, ".cache"), exist_ok=True)

for f in os.listdir(CHDIR):
    os.remove(os.path.join(CHDIR, f))

raw = open(SRC, encoding="utf-8").read()
parts = re.split(r"<<<PAGE\s+(\d+)>>>\n", raw)
pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
TOTAL = max(pages)
print("载入页数:", len(pages), "最大页:", TOTAL)

D2H = str.maketrans("０１２３４５６７８９", "0123456789")
# 「章」的 OCR 变体：章 / 話 / 歲（已实证）
CH_HEAD = re.compile(r"^第\s*([0-9０-９]{1,2})\s*[章話歲草童]")
ROMAN = re.compile(r"^[IVXLCDM]{1,7}$")
SEC_NUM = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?[ 　]+(\S.{0,38})$")

# ---------- 1. 页眉章号识别（三重约束，序贯扫描） ----------
def header_ch(txt):
    for i, l in enumerate(txt.strip().split("\n")[:2]):
        s = l.strip()
        if len(s) > 22:
            continue
        m = CH_HEAD.match(s)
        if m:
            return int(m.group(1).translate(D2H))
    return None

page_ch = {}
cur = None
rejected = []
for n in range(1, TOTAL + 1):
    c = header_ch(pages[n])
    if c is not None:
        if cur is None or c == cur or c == cur + 1:
            cur = c
        else:
            rejected.append((n, c, cur))
    if n >= 24:                     # p1-23 为前置页，不参与正文分章
        page_ch[n] = cur

print("被拒绝的异常章号跃迁:", rejected)

# ---------- 1a. 初始章跨度 ----------
spans_early = {}
for n, c in page_ch.items():
    if c is None:
        continue
    spans_early.setdefault(c, []).append(n)
spans_early = {c: sorted(v) for c, v in spans_early.items()}
print("初始章序列:", sorted(spans_early))

# ---------- 1b. 基于小节号的边界精修 ----------
# 章末 1-2 页常无页眉（书名页），若其已属下一章内容，用小节号纠正
def dom_sec_ch(txt):
    """本页首个小节号的章前缀"""
    for l in txt.strip().split("\n"):
        m = SEC_NUM.match(l)
        if m:
            return int(m.group(1))
    return None

for c in range(1, 21):
    if c not in spans_early:
        continue
    pg = sorted(spans_early[c]); s, e = pg[0], pg[-1]
    if c + 1 not in spans_early:
        continue
    cand = [p for p in pg if dom_sec_ch(pages[p]) == c + 1]
    if not cand:
        continue
    p0 = min(cand)
    if p0 <= s:
        continue
    # p0 之后不应再出现本 c 的小节
    tail = [p for p in range(p0, e + 1) if dom_sec_ch(pages[p]) == c]
    if tail:
        continue
    print(f"  边界精修: 第{c}章 末页 {e} -> {p0-1}；第{c+1}章 起始 {spans_early[c+1][0]} -> {p0}")
    spans_early[c] = [p for p in pg if p < p0]
    spans_early[c + 1] = sorted(set(spans_early[c + 1]) | set(range(p0, e + 1)))

# ---------- 2. 附录 / 后置部分 ----------
APP_START = None
for n in range(400, TOTAL + 1):
    head = "\n".join(pages[n].strip().split("\n")[:6])
    if re.search(r"附录\s*[ABC]", head) or re.match(r"^附录\s*[ABC]", pages[n].strip()):
        APP_START = n
        break
print("附录起始页:", APP_START)

# 附录之后不再归属正文章节（同时裁剪已算好的跨度）
if APP_START:
    for n in range(APP_START, TOTAL + 1):
        page_ch[n] = None
    for c in list(spans_early):
        trimmed = [p for p in spans_early[c] if p < APP_START]
        if trimmed:
            spans_early[c] = trimmed
        else:
            del spans_early[c]

# ---------- 3. 由精修后的跨度重建 页->章 ----------
spans = {c: sorted(v) for c, v in spans_early.items()}
for n in list(page_ch):
    page_ch[n] = None
for c, pg in spans.items():
    for n in pg:
        page_ch[n] = c

# 校验连续性
seq = sorted(spans)
print("\n章 | 起-止 | 页数 | 状态")
ok = True
for c in seq:
    pg = spans[c]
    s, e = min(pg), max(pg)
    gap = [x for x in range(s, e + 1) if x not in pg]
    contig = "连续" if not gap else f"缺{len(gap)}页"
    print(f"{c:>3} | p{s}-{e} | {len(pg):>3} | {contig}")
print("章序列:", seq, "连续递增:", seq == list(range(1, max(seq) + 1)))

# ---------- 4. 清洗 ----------
TITLES = {1:"引言",2:"监督学习",3:"浅层神经网络",4:"深型神经网络",5:"损失函数",
          6:"模型训练",7:"梯度与参数初始化",8:"性能评估",9:"正则化",10:"卷积网络",
          11:"残差网络",12:"变换器",13:"图神经网络",14:"无监督学习",15:"生成式对抗网络",
          16:"标准化流",17:"变分自编码器",18:"扩散模型",19:"强化学习",
          20:"为什么深度网络有效",21:"深度学习和伦理"}
TITLES[4] = "深度神经网络"   # 修正 OCR

def clean_page(txt, ch_no, is_start):
    out = []
    for l in txt.strip().split("\n"):
        s = l.strip()
        if not s:
            out.append(""); continue
        if re.fullmatch(r"\d{1,3}", s) or ROMAN.fullmatch(s):
            continue
        if s in ("理解深度学习", "目录", "前言"):
            continue
        m = CH_HEAD.match(s)
        if m and not is_start and len(s) <= 22:
            continue
        # 章首页：保留标题行，但去除重复的书名行
        out.append(l)
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out).strip()

# ---------- 5. 输出 ----------
index = []
for c in seq:
    pg = spans[c]
    s, e = min(pg), max(pg)
    title = TITLES.get(c, "")
    body = []
    for n in range(s, e + 1):
        if page_ch.get(n) != c or n not in pages:
            continue
        t = clean_page(pages[n], c, is_start=(n == s))
        if t:
            body.append(f"<!-- p.{n} -->\n{t}")
    text = f"# 第{c}章 {title}\n\n" + "\n\n".join(body) + "\n"
    fn = os.path.join(CHDIR, f"第{c:02d}章_{title}.md")
    open(fn, "w", encoding="utf-8").write(text)
    index.append({"章号": c, "标题": title, "起页": s, "止页": e,
                  "页数": len(pg), "字符数": len(text), "文件": os.path.basename(fn)})

# 前置页
front = []
for n in range(1, 24):
    front.append(f"<!-- p.{n} -->\n{pages[n].strip()}")
open(os.path.join(CHDIR, "第00章_前言译者序与目录.md"), "w", encoding="utf-8").write(
    "# 前言、译者序与目录\n\n" + "\n\n".join(front) + "\n")
index.insert(0, {"章号": 0, "标题": "前言、译者序与目录", "起页": 1, "止页": 23,
                 "页数": 23, "字符数": sum(len(pages[n]) for n in range(1, 24)),
                 "文件": "第00章_前言译者序与目录.md"})

# 附录
if APP_START:
    app = []
    for n in range(APP_START, TOTAL + 1):
        t = clean_page(pages[n], None, is_start=False)
        if t:
            app.append(f"<!-- p.{n} -->\n{t}")
    txt = "# 附录与后置资料\n\n" + "\n\n".join(app) + "\n"
    open(os.path.join(CHDIR, "附录.md"), "w", encoding="utf-8").write(txt)
    index.append({"章号": 99, "标题": "附录与后置资料", "起页": APP_START, "止页": TOTAL,
                  "页数": TOTAL - APP_START + 1, "字符数": len(txt), "文件": "附录.md"})

json.dump(index, open(os.path.join(KB, "_ocr/chapter_index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("\n=== 最终章节 ===")
for i in index:
    print(f"  {i['章号']:>2} {i['标题']:<18} p{i['起页']}-{i['止页']}  {i['字符数']:>7,}字")
print("\n章节文件数:", len(index), " 总字符:", f"{sum(i['字符数'] for i in index):,}")
