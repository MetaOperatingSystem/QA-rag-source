# public-corpus — Open Evaluation Corpus Suite (all paper experiment scripts & data)

**Purpose.** Replace the copyrighted / privacy-sensitive scanned textbook
*Understanding Deep Learning* with a **fully public, traceable** corpus of
≈5 million characters (`public5m`), which backs every experimental number in
Tables 6 and 9–13 of the paper.

## Corpus composition (see SOURCES.en.md for per-item public URLs)

| Layer | Source | Count | Storage form |
|---|---|---|---|
| Public-domain ancient books | github.com/garychowcmu/daizhigev20 | 8 books (1 extra held in reserve) | text-PDF ×1, scanned-PDF ×2 (200 DPI + OCR), docx ×5 |
| State Council policy documents | www.gov.cn policy library | 180 docs | docx |
| National Bureau of Statistics communiqués | stats.gov.cn | 4 annual editions | xlsx ×4 + csv ×126 |

Total: 318 files / 7,591 logical pages (lines) / **4,976,658 Chinese characters**
/ 14,076 chunks (median 512 chars).

## Pipeline (run in order)

```bash
PY=/Users/suweibin/.workbuddy/binaries/python/envs/default/bin/python
unset PYTHONPATH   # required: isolate ROS2 workspace's lxml/cffi

$PY fetch_public_corpus.py     # 1. download 9 ancient books (jsDelivr CDN)
$PY fetch_gov_docs.py          # 2. crawl 180 State Council docs (gov.cn, ~4 min throttled)
$PY build_stats_tables.py      # 3. parse 4 annual statistical communiqués → xlsx + csv
$PY prepare_corpus.py          # 4. prepare heterogeneous source files (render PDF / scanned PDF / docx, ~8 min)
$PY merge_public5m.py          # 5. ingest → split chapters → merge → chunk → build index (OCR 1531 pages, ~10 min)
$PY finish_merge_stats.py      # 6. BM25 index + stats_build.json (if step 5 is interrupted at the indexing stage)
```

## Evaluation (table numbers map to the paper)

| Script | Paper table | Output |
|---|---|---|
| `eval/eval_retrieval.py [bm25\|dense]` | Table 9 retrieval quality (A/B/C/D four configs, R@1/3/5) | `retrieval_results.json` |
| `eval/eval_sensitivity.py` | Table 10 L×k grid R@k and chunk count | `sensitivity_retrieval.json` |
| `eval/eval_ask.py production no_refusal temp08 no_breadcrumb` | Table 11 faithfulness/refusal + Table 12 latency | `e2e_results.json` |
| `eval/eval_tgen.py` | Table 10 Tgen column (run on a dedicated server after e2e) | `tgen_results.json` |
| `eval/eval_throughput.py` | Table 13 deployment-node throughput + concurrency behaviour | `throughput_results.json` |
| `eval/cer_measure.py` | OCR robustness (per-page CER on synthetic scans, source text as ground truth) | `cer_results.json` |

Evaluation question set `eval/questions.jsonl`: 74 questions = 29 routine + 20
paraphrased + 20 out-of-scope (8 of which contain in-corpus distractor words,
forming a stricter refusal test). Each question carries a gold anchor and an
answer key. Human adjudication log: `eval/adjudication.json`.

## Key measured results (2026-09-23, model qwen2.5:7b-instruct-q4_K_M @ 192.168.1.75 Docker/Ollama)

- Retrieval (production config BM25 uni+bigram+quality reweight): R@1 0.735 / R@3 0.857 / **R@5 0.878**
  - unigram-only ablation: R@1 0.633 (bigram contributes +10.2 pp)
  - dense retrieval bge-small-zh-v1.5 (CPU): R@5 0.755 (domain-mismatch negative result)
- Sensitivity: L300 k3 R@3 0.816 (worst corner) → L800 k8 R@8 0.918 (best corner); increasing L shrinks the index 2.4×
- OCR: per-page CER median 0.72% (Liaozhai) / 0.81% (Fengshen) on synthetic scans
- End-to-end (production config, n=74): in-corpus hallucination rate 0% (post human adjudication), OOS refusal rate 100%, in-corpus refusal rate 10.2% (2 retrieval-miss + 3 refused despite having evidence)
- Latency: T_ret median 58 ms; model stage 15.6 s median (prefill 197 tok/s + decode 8.6 tok/s); Feishu API round-trip median 0.106 s
- Indexing: ingest 611 s (incl. OCR 1531 pages) / chunk 7.6 s / index 6.6 s / cache 117 MB

## Known pitfalls

- `merge_public5m.py` once mis-computed the KB path by one level (wrote output to `Claw/chapters/`) — fixed; if you see `knowledge-base/chapters/public5m` missing while `Claw/chapters/public5m` exists, this is the bug.
- Chapter-heading titles of the "Chapter N" style (`第X回`): `ingest.HEAD_RE` and `split_chapters.CH_HEAD` already support `[章篇部卷回]`; uppercase variants like `叁/两` are covered in `cn2int`.
- The table-of-contents block at the start of ancient-book source files generates many spurious chapters during splitting — handled by `prepare_corpus.drop_toc()`.
- `eval_ask.py` measured T_ret (0.38 s) inside the e2e process is inflated by process load; controlled re-measurement is 58 ms (use the controlled value).
