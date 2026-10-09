# Reproduction Guide

**Paper:** *Resource-Frugal Retrieval-Augmented Generation on Edge Devices: Optimization Strategies and Quantified Evaluation for Group-Chat Administrative Question Answering*.

This document explains how to reproduce the system and the experimental results
reported in the paper from the source code in this package. It covers two layers:

1. **Deployment pipeline** — from a scanned document (image recognition) to a
   working Feishu group-chat robot (Section 3 of the paper).
2. **Experimental reproduction** — rebuilding the open `public5m` evaluation
   corpus and regenerating the retrieval / QA / latency / throughput tables and
   figures (Sections 4 and 5).

All commands assume a **POSIX shell** with **Python 3.10+** and, for the OCR
stage, **macOS** with the Swift toolchain. Paths are relative to the package
root (the directory containing this file).

---

## 1. Environment

### 1.1 Python dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the core stack: `PyMuPDF` (PDF text), `python-docx`,
`openpyxl`, `pandas`, `xlrd` (heterogeneous ingestion), and `lark-oapi` (Feishu
WebSocket bot). `matplotlib`/`numpy` are only needed for figure regeneration.

### 1.2 Model backend

The generation stage uses a local, 4-bit-quantized 7B model exposed through an
OpenAI-compatible endpoint.

```bash
# On the machine that will serve the model (needs a GPU or sufficient CPU/RAM):
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve            # listens on http://0.0.0.0:11434
```

The default endpoint is `http://192.168.1.75:11434` (override with the
`KB_OLLAMA_URL` environment variable or `KB_OLLAMA_URL` in `bot_config.py`).
`ask.py` auto-detects `openai` / `ollama` / `llamacpp` backends; no change is
required for standard Ollama.

> **Note:** a *true* local Ollama deployment is recommended over a rate-limited
> cloud proxy, because `feishu_bot.py` is concurrency-limited and retries on HTTP
> 429/500.

### 1.3 OCR toolchain (macOS only)

`tools/ocr.swift` uses Apple's **Vision** framework and is compiled with
`swiftc` (Xcode Command Line Tools):

```bash
xcode-select --install                      # if swiftc is missing
swiftc -O -o tools/ocr tools/ocr.swift      # produces tools/ocr
```

A prebuilt `tools/ocr` (macOS) is already shipped. On non-macOS hosts, any OCR
that emits plain text per page works — save it as `<name>_全文.txt` under
`full-text/` and ingest with `--type txt` (see §2.2).

---

## 2. Stage 1 — Image recognition (OCR) → normalized full text

A scanned PDF has **no text layer**, so the first step is OCR. The pipeline
normalizes every source into a single contract: page blocks delimited by
`<<<PAGE n>>>` (and `<<<SHEET name>>>` for spreadsheets).

### 2.1 One-shot ingestion (recommended)

`tools/ingest.py` auto-detects the source type and, for scanned PDFs, compiles
and runs the Vision OCR automatically:

```bash
python3 tools/ingest.py path/to/scanned_book.pdf --name mybook
# also supports: .docx .doc .xlsx .xls .csv .txt .md (--type to force)
```

Output:

```
full-text/mybook_全文.txt        # normalized full text with <<<PAGE n>>> markers
full-text/mybook.meta.json       # source type / method / page & char counts
```

### 2.2 Manual OCR (if you prefer to drive it directly)

```bash
# total pages of the PDF, then:
./tools/ocr <pdf> full-text/mybook_全文.txt 1 <total_pages> 200
```

`200` is the DPI (200 DPI already saturates Vision accuracy for this corpus).

> Non-macOS alternative: run any external OCR, save the result under
> `full-text/`, then `python3 tools/ingest.py full-text/mybook_全文.txt --name mybook --type txt`.

---

## 3. Stage 2 — Build the searchable knowledge base

### 3.1 One command (recommended)

`tools/build_corpus.py` chains ingest → chapter split → chunking → index cache:

```bash
python3 tools/build_corpus.py path/to/scanned_book.pdf --name mybook
```

Artifacts (namespaced by corpus name, never overwriting the main base):

```
full-text/mybook_全文.txt
chapters/mybook/第NN章_标题.md
chunks/mybook/chunks.jsonl          # RAG index (records + TF-IDF keywords + quality grade)
chunks/mybook/bm25.pkl              # BM25 cache
```

### 3.2 Step by step (equivalent to the above)

```bash
python3 tools/ingest.py scanned_book.pdf --name mybook
python3 tools/split_chapters.py full-text/mybook_全文.txt --name mybook
python3 tools/build_chunks.py \
        --chapters-dir chapters/mybook \
        --out-dir chunks/mybook --no-book-specific
python3 tools/retrieve.py "test query" --corpus mybook --rebuild
```

Chunk parameters (in `build_chunks.py`): `TARGET=500` chars, `OVERLAP=90`,
`MAX_SIZE=900`. For arbitrary (non-textbook) sources the one-shot
`build_corpus.py` already uses the generic defaults (`target=400`, `overlap=60`,
`min-seg=12`) suitable for short tables/sections.

---

## 4. Stage 3 — Retrieval (BM25)

`tools/retrieve.py` is a **zero-dependency** Chinese-optimized BM25 retriever
(Character unigram + bigram混合 tokenization, no jieba needed).

```bash
python3 tools/retrieve.py "什么是反向传播" -k 5
python3 tools/retrieve.py "位置编码" --corpus mybook -k 3
python3 tools/retrieve.py "卷积" --chapter 10
python3 tools/retrieve.py "注意力" --all --json     # merge main base + all sub-corpora
```

The first run builds `chunks/.../bm25.pkl` automatically; `--rebuild` forces
re-indexing after you change the chunk files.

---

## 5. Stage 4 — Generation (RAG answer)

`tools/ask.py` is the RAG core shared by both the CLI and the Feishu bot. It
retrieves top-`k` chunks, assembles a constrained context, and queries the 7B
model with a short, rule-based prompt that **forces a refusal** when the
material is insufficient (this clause carries the paper's safety margin).

```bash
python3 tools/ask.py "反向传播的正向传递和反向传递分别做什么？"
python3 tools/ask.py "解释残差连接" -k 6 --temp 0.1
python3 tools/ask.py "卷积的不变性与等变性" --chapter 10
python3 tools/ask.py "扩散模型如何逐步加噪" --show-context   # inspect the context
python3 tools/ask.py "你的问题" --no-stream                 # non-streaming output
```

Key defaults tuned for the 4-bit 7B model: `top_k=6`, `temperature=0.2`,
`num_predict=512`, context budget `4000` chars. The prompt, refusal rule, and
streaming/retry logic are all in `ask.py` (no external dependencies beyond the
HTTP call to the model endpoint).

---

## 6. Stage 5 — Feishu (Lark) group-chat deployment

The robot answers when a group member **@mentions** it. It uses **Feishu's
WebSocket long-connection mode**, which means **no public IP, no tunnel, and no
signature verification** are required — the bot only needs outbound Internet
access to Feishu.

### 6.1 Create a Feishu "enterprise self-built app"

1. Open <https://open.feishu.cn/> → *Developer Console* → create an
   **enterprise self-built app**.
2. Copy **App ID** and **App Secret** (填入 `bot_config.py`).
3. *Permissions* → enable `im:message`, `im:message:send_as_bot`,
   `im:message.receive_v1`.
4. *Event Subscriptions* → choose **"Use long connection to receive events"**
   (关键：不要选 Webhook) → add event `im.message.receive_v1`.
5. Publish a version and add the bot to your group.

### 6.2 Configure credentials

```bash
cp tools/bot_config.example.py tools/bot_config.py
# edit tools/bot_config.py  → set FEISHU_APP_ID / FEISHU_APP_SECRET / KB_OLLAMA_URL
# OR use environment variables (takes precedence):
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export KB_OLLAMA_URL=http://192.168.1.75:11434
```

> `feishu_notify.py` (one-way Webhook push) **requires** a populated
> `bot_config.py`; `feishu_bot.py` accepts env vars alone.

### 6.3 Run

```bash
bash tools/run_bot.sh            # isolates PYTHONPATH, then runs feishu_bot.py
```

`run_bot.sh` wraps the managed Python interpreter and unsets `PYTHONPATH` to
avoid cffi conflicts in the `lark-oapi` dependency chain. The bot blocks on the
WebSocket; the console prints `APP_ID=cli_aa… 模型=qwen2.5:7b …` and keeps the
connection alive with automatic reconnect.

**3-second rule:** the event handler (`do_message`) only parses and dispatches,
returning immediately; the actual model inference runs in a background thread
pool and is sent back via the *reply-message* API. Set `BOT_MAX_CONCURRENCY=1`
when the backend rate-limits.

Local self-check (no Feishu needed): `python3 tools/ask.py "your question" -k 5`.

---

## 7. Experimental reproduction — the `public5m` corpus

The paper's evaluation uses a fully **open**, ~5-million-character, 318-source
corpus (`public5m`) that mimics a college office's annual document load **without
any private or copyrighted material**. Its provenance is documented in
`public-corpus/SOURCES.md`.

### 7.1 Rebuild the corpus (optional; ~500 MB of public downloads)

```bash
cd public-corpus
python3 fetch_public_corpus.py      # pulls the listed public sources
python3 prepare_corpus.py           # normalize / dedupe
python3 merge_public5m.py           # assemble the unified public5m corpus
python3 build_stats_tables.py       # regenerate the statistics tables
```

The result is `chunks/public5m/chunks.jsonl`, the index consumed by the
evaluation harness.

### 7.2 Regenerate the paper's tables & figures

All numbers are read from the evaluation JSON files produced below; the figures
are vector PDFs generated by `make_figures.py`.

```bash
cd public-corpus/eval

python3 eval_retrieval.py      # Table IX (retrieval quality) + Table X R@k part
                               #   → retrieval_results.json
python3 eval_ask.py            # Table XI (faithfulness/refusal) + Table XII (latency)
                               #   → e2e_results.json
python3 eval_sensitivity.py    # Table X parameter sensitivity (chunk size / T_gen)
                               #   → sensitivity_retrieval.json
python3 eval_tgen.py           # Table XIII generation-time decomposition
                               #   → tgen_results.json
python3 eval_throughput.py     # Table XIII concurrency / throughput
                               #   → throughput_results.json
python3 cer_measure.py         # character-error-rate sanity check on OCR output

python3 make_figures.py        # Figs. 3–7 (vector PDF) → ./figures/
python3 make_setup_figure.py   # deployment photo figure   → ./figures/
```

`questions.jsonl` (shipped) is the fixed evaluation question set; the harness
queries the same `qwen2.5:7b-instruct-q4_K_M` endpoint. The ablations reported
in the paper (`production` vs `no_refusal` vs `temp08` vs `no_breadcrumb`) are
selected inside `eval_ask.py`; retrieval ablations (BM25 uni+bigram / unigram /
+dense) inside `eval_retrieval.py`.

---

## 8. Repository layout

```
QA-rag-source/
├── README.md                  # package overview
├── reproduction.md            # this file
├── requirements.txt
├── tools/
│   ├── ocr.swift / ocr        # macOS Vision OCR (source + prebuilt)
│   ├── ingest.py              # Stage 1: heterogeneous source → normalized full text
│   ├── split_chapters.py      # Stage 2a: full text → chapters
│   ├── build_chunks.py        # Stage 2b: chapters → RAG chunks (BM25-ready)
│   ├── build_chapters.py      # textbook-specific chapter builder (optional)
│   ├── build_corpus.py        # Stage 1+2 one-shot orchestrator
│   ├── retrieve.py            # Stage 3: BM25 retriever (zero-dependency)
│   ├── ask.py                 # Stage 4: RAG answer core (shared by CLI + bot)
│   ├── feishu_bot.py          # Stage 5: Feishu WebSocket long-connection bot
│   ├── feishu_notify.py       # one-way Webhook push (auxiliary)
│   ├── feishu_bot_webhook.py  # archived Webhook variant (reference)
│   ├── run_bot.sh             # launcher (PYTHONPATH isolation)
│   ├── README_bot.md          # Feishu setup details
│   └── bot_config.example.py  # credentials TEMPLATE (no secrets shipped)
├── public-corpus/
│   ├── README.md, SOURCES.md  # corpus provenance & build scripts
│   ├── fetch_*.py, prepare_corpus.py, merge_public5m.py, build_stats_tables.py, …
│   └── eval/
│       ├── eval_*.py, cer_measure.py   # evaluation harness
│       ├── make_figures.py, make_setup_figure.py
│       └── questions.jsonl             # fixed evaluation question set
└── full-text/ chapters/ chunks/         # generated at runtime (placeholders here)
```

---

## 9. Known limitations & notes

- **OCR is macOS-only.** `ocr.swift` depends on Apple's Vision framework. On
  other platforms, substitute any OCR and ingest the text with `--type txt`.
- **Formula distortion.** Scanned math formulas are distorted by OCR (e.g.
  `∂l/∂β` → `0l.10B.`). The chunker tags low-quality fragments (`grade=low`)
  and the retriever filters them by default. Verify derivations against the
  original document; every chunk carries its source page number for this.
- **Hard-coded root path.** In the published repository some scripts referenced
  an absolute path; in *this* package `build_chunks.py` resolves the knowledge
  base root relative to its own location, so the archive is portable as shipped.
- **No secrets in the package.** `bot_config.py` is intentionally absent; use
  `bot_config.example.py` (copy + fill) or environment variables.
- **Reproducibility of numbers.** Throughput/latency figures depend on the host
  GPU and the (rate-limited) model endpoint; absolute timings will vary, but the
  *trends* (refusal clause = safety margin; BM25 bigram +10.2pp R@1; concurrency
  plateau at c=2) are stable across runs.
