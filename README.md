# Source Code — Resource-Frugal Retrieval-Augmented Generation on Edge Devices

This package contains the **software** described in the accompanying
manuscript: a fully local retrieval-augmented generation (RAG) agent that turns
**scanned documents (image recognition / OCR) into a chat-able knowledge base
delivered through a Feishu (Lark) group-chat robot**.

It does **not** contain the LaTeX manuscript. The manuscript lives separately;
this archive is the reproducible code + data-construction + evaluation suite.

## What is included

| Path | Contents |
|---|---|
| `tools/` | The end-to-end pipeline: OCR → ingest → chapter split → chunking → BM25 retrieval → RAG answer → Feishu bot. |
| `public-corpus/` | Scripts that build the open, ~5-million-character evaluation corpus (`public5m`) from public sources, plus the evaluation harness that reproduces every table/figure in the paper. |
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
