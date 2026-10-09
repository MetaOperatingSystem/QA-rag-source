#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 检索器 —— 零第三方依赖，可直接运行在 Python 3.8+

面向中文优化：采用「汉字 unigram + bigram + 英文词」混合切分，
无需 jieba 等分词器即可获得接近分词方案的召回效果。

用法:
    python retrieve.py "什么是反向传播"
    python retrieve.py "transformer 的位置编码" -k 6
    python retrieve.py "卷积网络" --chapter 10
    python retrieve.py "扩散模型" --json        # 输出 JSON，供其他程序调用
"""
import json, os, sys, math, argparse, re, pickle
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.dirname(HERE)
CHUNKS = os.path.join(KB, "chunks", "chunks.jsonl")
CACHE = os.path.join(KB, ".cache", "bm25.pkl")


def corpus_path(name):
    """语料名 → 其切片文件路径（chunks/<name>/chunks.jsonl）。"""
    return os.path.join(KB, "chunks", name, "chunks.jsonl")


def _all_corpus_paths():
    """主库 + 所有子语料。"""
    paths = []
    if os.path.exists(CHUNKS):
        paths.append(CHUNKS)
    import glob
    for p in sorted(glob.glob(os.path.join(KB, "chunks", "*", "chunks.jsonl"))):
        paths.append(p)
    return paths


def _records_from(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

CJK = r"\u4e00-\u9fff"
TOKEN_RE = re.compile(rf"[{CJK}]|[A-Za-z][A-Za-z0-9\-]*|[0-9]+(?:\.[0-9]+)?")


def tokenize(text):
    """中文: unigram + bigram；英文/数字: 整词"""
    toks = []
    for seg in re.findall(rf"[{CJK}]+|[A-Za-z][A-Za-z0-9\-]*|[0-9]+(?:\.[0-9]+)?", text.lower()):
        if re.fullmatch(rf"[{CJK}]+", seg):
            toks.extend(seg)                                  # unigram
            toks.extend(seg[i:i+2] for i in range(len(seg)-1))  # bigram
        else:
            toks.append(seg)
    return toks


class BM25:
    def __init__(self, records, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.records = records
        self.docs = []
        self.df = Counter()
        for r in records:
            # 索引内容 = 面包屑 + 关键词（重复一次以加权） + 正文
            bread = f"{r.get('chapter_title','')} {r.get('section_title','')} {r.get('section','')} 第{r.get('chapter')}章"
            content = f"{bread} {bread} {' '.join(r.get('keywords', []))} {r['text']}"
            t = tokenize(content)
            self.docs.append(t)
            self.df.update(set(t))
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(1, self.N)
        self.tf = [Counter(d) for d in self.docs]
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
                    for w, n in self.df.items()}

    @classmethod
    def from_cache(cls, d, k1=1.5, b=0.75):
        """从纯数据重建索引（规避 pickle 依赖 __main__ 类对象的限制）"""
        obj = cls.__new__(cls)
        obj.k1, obj.b = k1, b
        obj.records, obj.docs = d["records"], d["docs"]
        obj.N = len(obj.docs)
        obj.avgdl = sum(len(x) for x in obj.docs) / max(1, obj.N)
        obj.tf = [Counter(x) for x in obj.docs]
        df = Counter()
        for x in obj.docs:
            df.update(set(x))
        obj.df = df
        obj.idf = {w: math.log(1 + (obj.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        return obj

    def search(self, query, topk=5, chapter=None, min_grade=True):
        q = tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            r = self.records[i]
            if chapter is not None and r.get("chapter") != chapter:
                continue
            if min_grade and r.get("grade") == "low":
                continue
            dl = len(self.docs[i])
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if not f:
                    continue
                idf = self.idf.get(w, 0.0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            # 质量轻微加权
            s *= (0.85 + 0.15 * r.get("quality", 0.6))
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [(self.records[i], s) for s, i in scores[:topk]]


def load(force=False, chunks_path=None, cache_path=None, all_corpora=False):
    """加载（或重建）检索索引。

    参数：
      chunks_path  显式切片路径（默认主库 chunks/chunks.jsonl）
      cache_path   显式缓存路径（默认 .cache/bm25.pkl）
      all_corpora  合并 主库 + 所有子语料 为一个索引
    缓存只序列化纯数据（records + 分词结果），不序列化类实例，
    以保证被 ask.py 等其他模块 import 时也能正常反序列化。
    """
    if all_corpora:
        paths = _all_corpus_paths()
        if not paths:
            print("未找到任何切片文件", file=sys.stderr); sys.exit(1)
        records = []
        for p in paths:
            records += _records_from(p)
        print(f"[检索] 合并 {len(paths)} 个语料，共 {len(records)} 片", file=sys.stderr)
        return BM25(records)

    cp = chunks_path or CHUNKS
    if not os.path.exists(cp):
        print("未找到切片文件:", cp, file=sys.stderr); sys.exit(1)
    cpath = cache_path or CACHE
    if not force and os.path.exists(cpath):
        try:
            mt_c = os.path.getmtime(cpath)
            if os.path.getmtime(cp) < mt_c:
                with open(cpath, "rb") as f:
                    d = pickle.load(f)
                return BM25.from_cache(d)
        except Exception:
            pass                      # 缓存损坏则回落到重建
    records = _records_from(cp)
    bm = BM25(records)
    os.makedirs(os.path.dirname(cpath), exist_ok=True)
    try:
        with open(cpath, "wb") as f:
            pickle.dump({"records": bm.records, "docs": bm.docs}, f, protocol=4)
    except Exception:
        pass
    return bm


def format_ctx(hits, max_chars=3000):
    """组装上下文，控制在预算内（为 4bit 小模型留出生成空间）"""
    out, used = [], 0
    for i, (r, s) in enumerate(hits, 1):
        head = f"[{i}] 第{r['chapter']}章 {r['chapter_title']}"
        if r.get("section"):
            head += f" > {r['section']} {r.get('section_title','')}"
        if r.get("page_start"):
            head += f" (原书 p.{r['page_start']})"
        block = f"{head}\n{r['text']}"
        if used + len(block) > max_chars:
            break
        out.append(block)
        used += len(block)
    return "\n\n".join(out), len(out)


def main():
    ap = argparse.ArgumentParser(description="《理解深度学习》BM25 检索（支持多语料）")
    ap.add_argument("query", help="检索问题")
    ap.add_argument("-k", "--topk", type=int, default=5)
    ap.add_argument("--chapter", type=int, default=None, help="限定章号")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--full", action="store_true", help="显示完整正文")
    ap.add_argument("--rebuild", action="store_true", help="重建索引缓存")
    ap.add_argument("--corpus", help="指定子语料名（chunks/<name>/chunks.jsonl）")
    ap.add_argument("--chunks", help="显式切片文件路径")
    ap.add_argument("--all", action="store_true", help="合并主库 + 所有子语料检索")
    a = ap.parse_args()

    cp = a.chunks or (corpus_path(a.corpus) if a.corpus else CHUNKS)
    if not a.all and not os.path.exists(cp):
        print("未找到切片文件:", cp, file=sys.stderr); sys.exit(1)

    if a.all:
        bm = load(all_corpora=True, force=a.rebuild)
    else:
        cache = None
        if a.corpus:
            cache = os.path.join(KB, "chunks", a.corpus, "bm25.pkl")
        bm = load(force=a.rebuild, chunks_path=cp, cache_path=cache)
    hits = bm.search(a.query, topk=a.topk, chapter=a.chapter)

    if a.json:
        print(json.dumps([{k: r[k] for k in
                           ("id", "chapter", "chapter_title", "section", "section_title",
                            "page_start", "keywords", "text")} | {"score": round(s, 3)}
                          for r, s in hits], ensure_ascii=False, indent=2))
        return

    print(f"查询: {a.query}   命中: {len(hits)}\n" + "=" * 70)
    for i, (r, s) in enumerate(hits, 1):
        head = f"[{i}] 第{r['chapter']}章 {r['chapter_title']}"
        if r.get("section"):
            head += f" > {r['section']} {r.get('section_title','')}"
        if r.get("page_start"):
            head += f"  (原书 p.{r['page_start']})"
        print(f"\n{head}")
        print(f"    score={s:.2f}  id={r['id']}  质量={r.get('grade')}  "
              f"关键词: {', '.join(r.get('keywords', [])[:6])}")
        body = r["text"] if a.full else r["text"][:180] + ("…" if len(r["text"]) > 180 else "")
        print("    " + body.replace("\n", "\n    "))


if __name__ == "__main__":
    main()
