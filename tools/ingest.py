#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第一步（统一摄入）：把异构源 → 规范化全文，供下游分章 / 切片。

这是知识库管线的「第一步」。除原有的扫描版 PDF（走 macOS Vision OCR）外，
本脚本额外适配以下源类型（自动识别，亦可用 --type 强制）：

  类型            说明                      抽取方式
  --------------- ------------------------- ---------------------------------
  scanned-pdf     扫描版 PDF（无文字层）    macOS Vision OCR（ocr.swift）
  text-pdf        文字版 PDF（有文字层）    PyMuPDF 逐页抽取
  docx            Word 2007+（.docx）       python-docx（正文 + 表格）
  doc             旧版 Word（.doc）         macOS textutil 转文本（仅 macOS）
  xlsx / xls      Excel 工作簿             openpyxl / pandas
  csv             CSV 文本表               pandas
  txt / md        纯文本 / Markdown        直接读取（保留结构，合成页锚点）

规范化输出格式（与下游 build_chapters / build_chunks 契约一致）：
  - 通用块分隔符：  <<<PAGE n>>>   （n 为顺序 1-based 逻辑页）
  - 电子表专用：    <<<SHEET 名称>>>   每个工作表一行，其后按行 <<<PAGE r>>>
  - 行内页锚点：    <!-- p.n -->      （由 build_chapters 写入章节 md，便于回溯）

产物：
  <kb>/full-text/<name>_全文.txt    规范化全文
  <kb>/full-text/<name>.meta.json   源类型 / 抽取方式 / 页数 / 字符数 等

用法：
  python3 ingest.py 路径/某书.pdf
  python3 ingest.py 某表.xlsx --name 销售数据
  python3 ingest.py 讲义.docx --type docx
  python3 ingest.py 某书.pdf --ocr-bin ../tools/ocr   # 指定已编译的 OCR 二进制
"""
import os, sys, re, json, argparse, subprocess, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)
FULLTEXT = os.path.join(KB, "full-text")
os.makedirs(FULLTEXT, exist_ok=True)

# 逻辑页合成粒度（非分页源按此切分，使下游页锚点有意义）
PAGE_BUDGET = 2000

# 标题行：遇到则另起一页（保证「第 N 章」等章标题落在页首，便于分章识别）
# 注意：允许行首全角/半角空白（章回体小说正文回目带缩进）；含「回」（章回体）
# 与「叁」（封神演义用大写数字）变体。
HEAD_RE = re.compile(
    r"^[ \t　]*第\s*[\d０-９零一二三四五六七八九十百叁两]+\s*[章篇部卷回]|"
    r"^[ \t　]*Chapter\s+\d+|^[ \t　]*#{1,3}\s+|"
    r"^[ \t　]*卷\s*[一二三四五六七八九十]+\s|"
    r"^第\d+\s*节\s|^Section\s+\d+", re.IGNORECASE)

EXT2TYPE = {
    ".pdf": "pdf", ".docx": "docx", ".doc": "doc",
    ".xlsx": "xlsx", ".xls": "xls", ".csv": "csv",
    ".txt": "txt", ".md": "md", ".markdown": "md",
}


def sanitize(name):
    # 保留中英文与数字，其余替换为下划线
    s = re.sub(r"[\\/:*?\"<>|'\s]+", "_", name).strip("._")
    return s or "corpus"


# --------------------------------------------------------------------------- 抽取：扫描 PDF（Vision OCR）
def extract_scanned_pdf(path, name, ocr_bin):
    """扫描版 PDF → 调 ocr.swift（macOS Vision）。直接写到目标全文文件。"""
    binp = ocr_bin or os.path.join(HERE, "ocr")
    if not os.path.exists(binp):
        # 尝试现场编译
        swift = os.path.join(HERE, "ocr.swift")
        if not os.path.exists(swift):
            raise RuntimeError("未找到 ocr.swift，无法编译 OCR 二进制")
        print(f"[OCR] 现场编译 ocr.swift …", file=sys.stderr)
        r = subprocess.run(["swiftc", "-O", "-o", binp, swift],
                            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("swiftc 编译 ocr.swift 失败:\n" + r.stderr)
    # 取总页数
    import fitz
    doc = fitz.open(path)
    total = doc.page_count
    doc.close()
    out = os.path.join(FULLTEXT, f"{name}_全文.txt")
    print(f"[OCR] 扫描版 PDF，共 {total} 页，调用 Vision OCR（可能需要数分钟）…",
          file=sys.stderr)
    r = subprocess.run([binp, path, out, "1", str(total), "200"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("OCR 执行失败:\n" + (r.stderr or r.stdout))
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        raise RuntimeError("OCR 未产出有效全文")
    return out, {"method": "vision-ocr", "pages": total}


# --------------------------------------------------------------------------- 抽取：文字 PDF
def extract_text_pdf(path):
    import fitz
    doc = fitz.open(path)
    blocks = []
    for i in range(doc.page_count):
        t = doc[i].get_text("text")
        t = t.strip()
        if not t:
            t = "[本页无文字层]"
        blocks.append(t)
    doc.close()
    return blocks, {"method": "pymupdf-text", "pages": len(blocks)}


# --------------------------------------------------------------------------- 抽取：Word .docx
def extract_docx(path):
    import docx
    d = docx.Document(path)
    paras = []
    for p in d.paragraphs:
        txt = p.text.strip()
        if txt:
            paras.append(txt)
    # 表格 → 竖线分隔文本，内联
    for ti, tbl in enumerate(d.tables):
        rows = []
        for row in tbl.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            rows.append(" | ".join(cells))
        if rows:
            paras.append(f"[表格 {ti+1}]\n" + "\n".join(rows))
    text = "\n".join(paras)
    blocks = paginate(text)
    return blocks, {"method": "python-docx", "pages": len(blocks)}


# --------------------------------------------------------------------------- 抽取：旧版 Word .doc
def extract_doc(path):
    if shutil.which("textutil") is None:
        raise RuntimeError(".doc 为旧版二进制格式，仅 macOS 可用 textutil 转换；"
                           "请先另存为 .docx 后重试")
    r = subprocess.run(["textutil", "-convert", "txt", "-stdout", path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("textutil 转换 .doc 失败:\n" + (r.stderr or ""))
    blocks = paginate(r.stdout)
    return blocks, {"method": "textutil-doc", "pages": len(blocks)}


# --------------------------------------------------------------------------- 抽取：Excel / CSV
def _rows_to_blocks(sheet_name, header, rows):
    """把一张表转成若干 <<<PAGE r>>> 块（每行一个逻辑页）。"""
    blocks = []
    for ri, row in enumerate(rows, 1):
        cells = [(str(c).strip() if c is not None else "") for c in row]
        # 跳过全空行
        if not any(cells):
            continue
        if header:
            lines = []
            for ci, val in enumerate(cells):
                col = header[ci] if ci < len(header) else f"列{ci+1}"
                lines.append(f"{col}: {val}")
            body = "\n".join(lines)
        else:
            body = " | ".join(cells)
        blocks.append((ri, body, sheet_name))
    return blocks


def extract_excel(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    pages = []          # (page_no, text, sheet)
    sheets_meta = []
    pn = 0
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        # 首行若全为非空文本，视为表头
        first = rows[0]
        header = None
        if all(isinstance(c, str) and c.strip() for c in first if c is not None):
            header = [str(c).strip() for c in first]
            data = rows[1:]
        else:
            data = rows
        blocks = _rows_to_blocks(ws.title, header, data)
        for ri, body, _ in blocks:
            pn += 1
            pages.append((pn, body, ws.title))
        sheets_meta.append({"sheet": ws.title, "rows": len(blocks)})
    wb.close()
    return pages, {"method": "openpyxl", "pages": pn, "sheets": sheets_meta}


def extract_csv(path):
    import pandas as pd
    df = pd.read_csv(path)
    cols = [str(c) for c in df.columns]
    rows = df.where(df.notna(), None).values.tolist()
    blocks = _rows_to_blocks("CSV", cols, rows)
    pages = [(ri, body, "CSV") for ri, body, _ in blocks]
    return pages, {"method": "pandas-csv", "pages": len(pages),
                   "sheets": [{"sheet": "CSV", "rows": len(pages)}]}


# --------------------------------------------------------------------------- 工具：纯文本分页
def paginate(text):
    """把无页结构的长文本切成逻辑页：遇章/节标题另起一页，并受 PAGE_BUDGET 限制。"""
    lines = text.split("\n")
    blocks, buf, n = [], [], 0

    def flush():
        nonlocal buf, n
        if buf:
            b = "\n".join(buf).strip()
            if b:
                blocks.append(b)
            buf, n = [], 0

    for ln in lines:
        if HEAD_RE.match(ln) and buf:   # 标题行：先把前文收尾，再让标题独占新页首
            flush()
        buf.append(ln)
        n += len(ln) + 1
        if n >= PAGE_BUDGET:
            flush()
    flush()
    return blocks


def _resplit_block(text):
    """块内若含非首行标题，则在标题处拆成多块（保证标题落在页首）。"""
    lines = text.split("\n")
    out, cur = [], []
    for ln in lines:
        if HEAD_RE.match(ln) and cur:
            out.append("\n".join(cur).strip())
            cur = []
        cur.append(ln)
    if cur:
        out.append("\n".join(cur).strip())
    return [b for b in out if b]


# --------------------------------------------------------------------------- 写出
def write_outputs(name, pages, meta, source_type):
    """pages: list of (page_no, text) 或 (page_no, text, sheet)

    先按标题行把每个块再拆开（保证「第 N 章」等标题落在页首），
    再顺序编号写出，使下游分章识别稳定。
    """
    expanded = []  # (sheet_or_None, text)
    for item in pages:
        if len(item) == 3:
            _, txt, sheet = item
            for sub in _resplit_block(txt):
                expanded.append((sheet, sub))
        else:
            _, txt = item
            for sub in _resplit_block(txt):
                expanded.append((None, sub))

    full = os.path.join(FULLTEXT, f"{name}_全文.txt")
    out = []
    chars = 0
    cur_sheet = None
    for i, (sheet, txt) in enumerate(expanded, 1):
        if sheet is not None and sheet != cur_sheet:
            out.append(f"\n<<<SHEET {sheet}>>>\n")
            cur_sheet = sheet
        out.append(f"\n<<<PAGE {i}>>>\n{txt}")
        chars += len(txt)
    with open(full, "w", encoding="utf-8") as f:
        f.write("".join(out).strip() + "\n")
    meta.update({"name": name, "source_type": source_type, "pages": len(expanded),
                 "chars": chars, "created_at": datetime.datetime.now().isoformat(timespec="seconds")})
    with open(os.path.join(FULLTEXT, f"{name}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return full, chars


# --------------------------------------------------------------------------- 主流程
def detect_type(path, forced):
    ext = os.path.splitext(path)[1].lower()
    if forced:
        return forced
    if ext == ".pdf":
        return "pdf"
    return EXT2TYPE.get(ext, "txt")


def run(path, name=None, forced=None, ocr_bin=None):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    st = detect_type(path, forced)
    name = name or sanitize(os.path.splitext(os.path.basename(path))[0])
    print(f"[摄入] 源: {os.path.basename(path)}  类型: {st}  语料名: {name}", file=sys.stderr)

    if st == "pdf":
        # 区分扫描版 / 文字版
        import fitz
        doc = fitz.open(path)
        sample = "".join(doc[i].get_text("text") for i in range(min(doc.page_count, 8)))
        doc.close()
        if len(sample.strip()) < 30:
            full, m = extract_scanned_pdf(path, name, ocr_bin)
            meta = m
            # 扫描版直接由 ocr 写出全文，这里仅回读统计
            chars = sum(len(l) for l in open(full, encoding="utf-8"))
            meta["chars"] = chars
        else:
            blocks, m = extract_text_pdf(path)
            full, chars = write_outputs(name, [(i + 1, b) for i, b in enumerate(blocks)], m, "text-pdf")
            meta = m
    elif st == "docx":
        blocks, m = extract_docx(path)
        full, chars = write_outputs(name, [(i + 1, b) for i, b in enumerate(blocks)], m, "docx")
        meta = m
    elif st == "doc":
        blocks, m = extract_doc(path)
        full, chars = write_outputs(name, [(i + 1, b) for i, b in enumerate(blocks)], m, "doc")
        meta = m
    elif st == "xlsx":
        pages, m = extract_excel(path)
        full, chars = write_outputs(name, pages, m, "xlsx")
        meta = m
    elif st == "xls":
        # 优先 openpyxl（xlsx 扩展）；xls 二进制回退 pandas+xlrd
        try:
            pages, m = extract_excel(path)
        except Exception:
            import pandas as pd
            import openpyxl  # noqa
            xls = pd.ExcelFile(path, engine="xlrd")
            pages = []
            pn = 0
            sheets_meta = []
            for s in xls.sheet_names:
                df = xls.parse(s)
                cols = [str(c) for c in df.columns]
                rows = df.where(df.notna(), None).values.tolist()
                bl = _rows_to_blocks(s, cols, rows)
                for ri, body, _ in bl:
                    pn += 1
                    pages.append((pn, body, s))
                sheets_meta.append({"sheet": s, "rows": len(bl)})
            m = {"method": "pandas-xlrd", "pages": pn, "sheets": sheets_meta}
        full, chars = write_outputs(name, pages, m, "xls")
        meta = m
    elif st == "csv":
        pages, m = extract_csv(path)
        full, chars = write_outputs(name, pages, m, "csv")
        meta = m
    else:  # txt / md
        text = open(path, encoding="utf-8", errors="ignore").read()
        # 若已是带 <<<PAGE>>> 标记的规范化文本，则原样保留
        if "<<<PAGE" in text:
            full = os.path.join(FULLTEXT, f"{name}_全文.txt")
            with open(full, "w", encoding="utf-8") as f:
                f.write(text if text.endswith("\n") else text + "\n")
            npages = len(re.findall(r"<<<PAGE\s+\d+>>>", text))
            meta = {"method": "passthrough", "pages": npages}
            chars = len(text)
        else:
            blocks = paginate(text)
            full, chars = write_outputs(name, [(i + 1, b) for i, b in enumerate(blocks)],
                                        {"method": "raw-text"}, "txt")
            meta = {"method": "raw-text", "pages": len(blocks)}

    with open(os.path.join(FULLTEXT, f"{name}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[摄入] 完成 → {os.path.relpath(full, KB)}  "
          f"字符数={chars:,}  逻辑页数/行数={meta.get('pages')}  方式={meta.get('method')}",
          file=sys.stderr)
    return full, meta


def main():
    ap = argparse.ArgumentParser(description="多源摄入（第一步）：异构源 → 规范化全文")
    ap.add_argument("source", help="源文件路径（pdf/docx/doc/xlsx/xls/csv/txt/md）")
    ap.add_argument("--name", help="语料名（默认取文件名，决定输出目录与文件前缀）")
    ap.add_argument("--type", choices=["auto", "pdf", "docx", "doc", "xlsx", "xls",
                                        "csv", "txt", "md"], default="auto",
                    help="强制源类型（默认按扩展名+内容自动识别）")
    ap.add_argument("--ocr-bin", help="已编译的 ocr 二进制路径（扫描 PDF 用）")
    a = ap.parse_args()
    forced = None if a.type == "auto" else a.type
    run(a.source, name=a.name, forced=forced, ocr_bin=a.ocr_bin)


if __name__ == "__main__":
    main()
