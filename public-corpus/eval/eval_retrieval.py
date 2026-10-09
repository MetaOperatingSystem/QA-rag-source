#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_retrieval.py — 表IX（检索质量）与表X（参数敏感性 R@k 部分）

四种检索配置：
  A  BM25 uni+bigram（纯词法，无质量加权）        —— 消融基线
  B  BM25 unigram-only（纯词法，无质量加权）      —— 分词消融
  C  BM25 uni+bigram + 质量重加权（生产配置）     —— 与 retrieve.py 完全一致
  D  Dense（bge-small-zh-v1.5，本机 CPU 推理）    —— 可选升级对照

产出 eval/retrieval_results.json
"""
import json
import math
import os
import re
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
KB = os.path.dirname(PC)            # knowledge-base/
sys.path.insert(0, os.path.join(KB, "tools"))

from retrieve import tokenize, BM25  # noqa: E402

CHUNKS = os.path.join(KB, "chunks", "public5m", "chunks.jsonl")
QF = os.path.join(HERE, "questions.jsonl")
OUT = os.path.join(HERE, "retrieval_results.json")


# --------------------------------------------------------------------------
def tokenize_uni(text):
    """unigram-only 消融：只保留汉字单字 + 英文词 + 数字。"""
    toks = []
    for seg in re.findall(r"[\u4e00-\u9fff]+|[A-Za-z][A-Za-z0-9\-]*|[0-9]+(?:\.[0-9]+)?",
                          text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", seg):
            toks.extend(seg)
        else:
            toks.append(seg)
    return toks


class BM25Var:
    """与 retrieve.BM25 公式完全一致的参数化变体。

    use_quality=False  → 纯 BM25，无质量乘子、无 low 片过滤
    use_quality=True   → 生产配置（等价 retrieve.BM25.search 默认行为）
    """

    def __init__(self, records, tokenizer=tokenize):
        self.records = records
        self.tokenizer = tokenizer
        self.docs, self.df = [], Counter()
        for r in records:
            bread = (f"{r.get('chapter_title','')} {r.get('section_title','')} "
                     f"{r.get('section','')} 第{r.get('chapter')}章")
            content = f"{bread} {bread} {' '.join(r.get('keywords', []))} {r['text']}"
            t = tokenizer(content)
            self.docs.append(t)
            self.df.update(set(t))
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(1, self.N)
        self.tf = [Counter(d) for d in self.docs]
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
                    for w, n in self.df.items()}
        self.k1, self.b = 1.5, 0.75

    def rank(self, query, topk=None, use_quality=True):
        q = self.tokenizer(query)
        scores = []
        for i, tf in enumerate(self.tf):
            r = self.records[i]
            if use_quality and r.get("grade") == "low":
                continue
            dl = len(self.docs[i])
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if not f:
                    continue
                s += (self.idf.get(w, 0.0) * f * (self.k1 + 1)
                      / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)))
            if use_quality:
                s *= (0.85 + 0.15 * r.get("quality", 0.6))
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        idxs = [i for _, i in scores]
        return idxs[:topk] if topk else idxs


class Dense:
    """稠密检索：bge-small-zh-v1.5（CPU）+ 余弦相似。"""

    def __init__(self, records, model_dir=None):
        from sentence_transformers import SentenceTransformer
        self.records = records
        self.model = SentenceTransformer(model_dir or "BAAI/bge-small-zh-v1.5",
                                         device="cpu")
        texts = []
        for r in records:
            bread = f"{r.get('chapter_title','')}"
            texts.append(f"{bread} {r['text']}")
        t0 = time.time()
        self.emb = self.model.encode(texts, batch_size=64, normalize_embeddings=True,
                                     show_progress_bar=True)
        print(f"[dense] encoded {len(texts)} chunks in {time.time()-t0:.0f}s",
              file=sys.stderr)

    def rank(self, query, topk=None):
        qe = self.model.encode([query], normalize_embeddings=True)[0]
        sims = self.emb @ qe
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        return order[:topk] if topk else order


class _Wrapper:
    """把 (BM25Var, use_quality) 统一成 rank(query, topk) 接口。"""

    def __init__(self, bm, use_quality):
        self.bm, self.use_quality = bm, use_quality

    def rank(self, query, topk=None):
        return self.bm.rank(query, topk=topk, use_quality=self.use_quality)


# --------------------------------------------------------------------------
def load_questions():
    qs = [json.loads(l) for l in open(QF, encoding="utf-8") if l.strip()]
    return qs


def find_gold(records, anchor):
    """锚点所在切片 = 金标（含重叠片，任一命中即算命中）。"""
    return [i for i, r in enumerate(records) if anchor in r["text"]]


def main(which="all"):
    records = [json.loads(l) for l in open(CHUNKS, encoding="utf-8") if l.strip()]
    print(f"chunks: {len(records)}")
    qs = load_questions()
    in_scope = [q for q in qs if q["stratum"] in ("routine", "paraphrased")]
    oos = [q for q in qs if q["stratum"] == "out-of-scope"]

    # ---- 锚点校验 ----
    gold_map, anchor_report = {}, []
    for q in in_scope:
        g = find_gold(records, q["anchor"])
        gold_map[q["qid"]] = g
        anchor_report.append({"qid": q["qid"], "n_gold": len(g),
                              "gold_ids": [records[i]["id"] for i in g][:4]})
    bad = [a for a in anchor_report if a["n_gold"] == 0]
    print(f"anchor check: {len(anchor_report)-len(bad)}/{len(anchor_report)} ok, "
          f"{len(bad)} missing")
    for a in bad:
        print("  MISSING:", a["qid"])

    # ---- OOS 缺席校验 ----
    oos_report = []
    for q in oos:
        hits = []
        for k in q["absent_keys"]:
            n = sum(1 for r in records if k in r["text"])
            hits.append({"key": k, "chunks": n})
        oos_report.append({"qid": q["qid"], "check": hits})
    for r in oos_report:
        flag = any(h["chunks"] > 0 for h in r["check"])
        if flag:
            print("  OOS-LEAK:", r["qid"], r["check"])

    results = {"n_chunks": len(records), "n_questions": {"in_scope": len(in_scope),
                                                         "oos": len(oos)},
               "anchor_check": anchor_report, "oos_check": oos_report}

    # ---- BM25 变体 ----
    configs = {}
    if which in ("all", "bm25"):
        t0 = time.time()
        bm_prod = BM25Var(records)                          # C 生产（质量重加权）
        bm_plain = BM25Var(records)                         # A 纯词法
        bm_uni = BM25Var(records, tokenizer=tokenize_uni)   # B unigram
        print(f"[bm25] 3 variants built in {time.time()-t0:.1f}s", file=sys.stderr)
        configs["A_bm25_uni_bigram_plain"] = _Wrapper(bm_plain, use_quality=False)
        configs["B_bm25_unigram_only"] = _Wrapper(bm_uni, use_quality=False)
        configs["C_bm25_quality_reweight"] = _Wrapper(bm_prod, use_quality=True)

    if which in ("all", "dense"):
        local = os.path.join(PC, "models", "models", "BAAI--bge-small-zh-v1.5",
                             "snapshots", "master")
        try:
            configs["D_dense_bge"] = Dense(records, model_dir=local)
        except Exception as e:
            print(f"[dense] unavailable: {e}", file=sys.stderr)

    per_config = {}
    for name, engine in configs.items():
        recs = {"R@1": 0, "R@3": 0, "R@5": 0, "n": 0}
        lat = []
        details = []
        for q in in_scope:
            gold = set(gold_map[q["qid"]])
            if not gold:
                continue
            t0 = time.perf_counter()
            ranked = engine.rank(q["question"], topk=5)
            lat.append(time.perf_counter() - t0)
            pos = next((k + 1 for k, i in enumerate(ranked) if i in gold), None)
            recs["n"] += 1
            if pos is not None:
                recs["R@5"] += 1
                if pos <= 3:
                    recs["R@3"] += 1
                if pos == 1:
                    recs["R@1"] += 1
            details.append({"qid": q["qid"], "rank": pos})
        lat.sort()
        per_config[name] = {
            "R@1": recs["R@1"] / recs["n"], "R@3": recs["R@3"] / recs["n"],
            "R@5": recs["R@5"] / recs["n"], "n": recs["n"],
            "latency_ms_median": round(lat[len(lat)//2] * 1000, 1),
            "latency_ms_p95": round(lat[int(len(lat)*0.95)] * 1000, 1),
            "details": details,
        }
        print(f"{name}: R@1={per_config[name]['R@1']:.3f} R@3={per_config[name]['R@3']:.3f} "
              f"R@5={per_config[name]['R@5']:.3f}  "
              f"lat_med={per_config[name]['latency_ms_median']}ms "
              f"lat_p95={per_config[name]['latency_ms_p95']}ms")

    results["configs"] = per_config
    # 合并而非覆盖：bm25 / dense 分批运行时保留另一批的 configs
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            merged = old.get("configs", {})
            merged.update(per_config)
            results["configs"] = merged
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"saved -> {OUT}")


def _plain_rank_factory(bm):
    """闭包：复用 bm 的索引，但打分时不加质量项。"""
    def rank(query, topk=None):
        q = bm.tokenizer(query)
        scores = []
        for i, tf in enumerate(bm.tf):
            r = bm.records[i]
            if r.get("grade") == "low":
                continue
            dl = len(bm.docs[i])
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if not f:
                    continue
                s += (bm.idf.get(w, 0.0) * f * (bm.k1 + 1)
                      / (f + bm.k1 * (1 - bm.b + bm.b * dl / bm.avgdl)))
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        idxs = [i for _, i in scores]
        return idxs[:topk] if topk else idxs
    return rank


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
