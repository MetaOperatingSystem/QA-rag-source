# Source Code — Resource-Frugal Retrieval-Augmented Generation on Edge Devices

> ### ▶ What this repository is for
> This repository provides the **complete, reproducible software** accompanying our paper *"Resource-Frugal Retrieval-Augmented Generation on Edge Devices: Optimization Strategies and Quantified Evaluation for Group-Chat Administrative Question Answering"*. It implements a **fully on-premise RAG (retrieval-augmented generation) agent** that converts **scanned / image-based documents into a citation-backed, chat-able knowledge base**, and serves it through a **Feishu (Lark) group-chat robot** for college administrative question answering. The system runs entirely on a single commodity edge device — **no cloud services, no dense-retrieval / embedding stack, and no GPU for indexing** — using a purely lexical (CJK unigram+bigram BM25) index and a 4-bit quantized language model. It ships the OCR → ingestion → chapter splitting → chunking → retrieval → generation → Feishu-bot pipeline together with the evaluation suite that reproduces every table and figure in the paper from a fully public ~5-million-character corpus. The LaTeX manuscript is **not** included.

This package contains the **software** described in the accompanying
manuscript: a fully local retrieval-augmented generation (RAG) agent that turns
**scanned documents (image recognition / OCR) into a chat-able knowledge base
delivered through a Feishu (Lark) group-chat robot**.

It does **not** contain the LaTeX manuscript. The manuscript lives separately;
this archive is the reproducible code + data-construction + evaluation suite.

## Authors

| # | Author | Affiliation | ORCID |
|---|--------|-------------|-------|
| 1 | Yanchun Kong (孔艳春) | College of Architectural Engineering, Kunming Metallurgy University, Kunming 650033, Yunnan, China | [0000-0002-9827-7432](https://orcid.org/0000-0002-9827-7432) |
| 2 | Guiwen Zhao (赵贵文) | College of Mathematics and Computer Science, Dali University, Dali 671003, Yunnan, China | — |
| 3 | Donglian Liu (刘东莲) | College of Architectural Engineering, Kunming Metallurgy University, Kunming 650033, Yunnan, China | — |
| 4 | Weibin Su (苏为斌)\* | College of Mathematics and Computer Science, Dali University, Dali 671003, Yunnan, China | [0000-0002-3433-4848](https://orcid.org/0000-0002-3433-4848) |

\* **Corresponding author**: Weibin Su — **swb@dali.edu.cn**

## Conflict of Interest

The authors declare no conflict of interest.

## Open Source & License

This repository is released as open source to support reproducible research:

- **Source code** is distributed under the [MIT License](LICENSE).
- **Evaluation corpus** (`public-corpus/`): every document is drawn from fully
  public sources — public-domain ancient texts, official Chinese government open
  releases, and national statistical communiqués. No copyrighted or private
  institutional documents are included. See `public-corpus/SOURCES.md` (中文) and
  `public-corpus/SOURCES.en.md` (English) for the complete provenance registry.
  Users are responsible for complying with the terms of those upstream sources.
- **No secrets shipped**: `tools/bot_config.example.py` is a template; real
  Feishu credentials are never committed.

## What is included

| Path | Contents |
|---|---|
| `tools/` | The end-to-end pipeline: OCR → ingest → chapter split → chunking → BM25 retrieval → RAG answer → Feishu bot. |
| `public-corpus/` | Scripts that build the open, ~5-million-character evaluation corpus (`public5m`) from public sources, plus the evaluation harness that reproduces every table/figure in the paper. (Docs: `README.md` / `README.en.md`, `SOURCES.md` / `SOURCES.en.md`) |
| `full-text/`, `chapters/`, `chunks/` | Generated at runtime; shipped empty as placeholders. |
| `reproduction.md` | **The complete, step-by-step reproduction guide (English).** |
| `requirements.txt` | Python dependencies. |
| `tools/bot_config.example.py` | Feishu credentials template (real secrets are **never** shipped). |

## Pipeline at a glance

```
 scanned PDF ──(ocr.swift / Vision OCR)──▶ full-text ──(split_chapters)──▶ chapters
                                                                                    │
                                                                                    ▼
        Feishu @mention ──▶ feishu_bot.py ──▶ answer() ──▶ retrieve.py (BM25) + ask.py (qwen2.5:7b) ──▶ reply
```

## Reproduce

Read **`reproduction.md`**. In short:

```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b-instruct-q4_K_M            # backend model
python3 tools/build_corpus.py path/to/scanned.pdf # image recognition → searchable KB
python3 tools/ask.py "your question"              # local RAG answer
bash tools/run_bot.sh                             # (optional) Feishu group-chat bot
```

## Security note

`tools/bot_config.example.py` is a template. Copy it to `tools/bot_config.py`
and insert your own Feishu **App ID / App Secret**. Never commit the populated
file. The shipped code never contains live credentials.
