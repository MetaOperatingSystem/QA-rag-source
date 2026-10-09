# public-corpus — 公开语料评测套件（论文实验全部脚本与数据）

目的：以**全部公开可溯源**的 ≈500 万字语料（public5m）替换含版权/隐私风险的
《理解深度学习》扫描件，支撑论文表 6、表 9–13 的全部实验数字。

## 语料构成（详见 SOURCES.md，含逐条公开 URL）

| 层 | 来源 | 数量 | 入库形式 |
|---|---|---|---|
| 公有领域古籍 | github.com/garychowcmu/daizhigev20 | 8 本（另 1 本备查） | 文字版PDF×1、扫描版PDF×2（200DPI+OCR）、docx×5 |
| 国务院政策文件 | www.gov.cn 政策文件库 | 180 篇 | docx |
| 国家统计局公报 | stats.gov.cn | 2022–2025 四个年度 | xlsx×4 + csv×126 |

合计：318 文件 / 7,591 逻辑页（行）/ **4,976,658 汉字** / 14,076 切片（中位 512 字）。

## 流水线（按序执行）

```bash
PY=/Users/suweibin/.workbuddy/binaries/python/envs/default/bin/python
unset PYTHONPATH   # 必须：隔离 ROS2 工作区的 lxml/cffi

$PY fetch_public_corpus.py     # 1. 下载 9 本古籍（jsDelivr CDN）
$PY fetch_gov_docs.py          # 2. 抓取 180 篇国务院公文（gov.cn，限速 ~4 分钟）
$PY build_stats_tables.py      # 3. 解析 4 个年度统计公报 → xlsx + csv
$PY prepare_corpus.py          # 4. 制备异构源文件（渲染 PDF/扫描 PDF/docx，约 8 分钟）
$PY merge_public5m.py          # 5. 摄入→分章→合并→切片→建库（OCR 1531 页，约 10 分钟）
$PY finish_merge_stats.py      # 6. BM25 索引 + stats_build.json（若 5 在索引阶段中断）
```

## 评测（表号对应论文）

| 脚本 | 论文表 | 产出 |
|---|---|---|
| `eval/eval_retrieval.py [bm25\|dense]` | 表9 检索质量（A/B/C/D 四配置 R@1/3/5） | `retrieval_results.json` |
| `eval/eval_sensitivity.py` | 表10 L×k 网格 R@k 与切片数 | `sensitivity_retrieval.json` |
| `eval/eval_ask.py production no_refusal temp08 no_breadcrumb` | 表11 忠实度/拒答 + 表12 时延 | `e2e_results.json` |
| `eval/eval_tgen.py` | 表10 Tgen 列（须在 e2e 后独占服务器跑） | `tgen_results.json` |
| `eval/eval_throughput.py` | 表13 部署节点吞吐 + 并发行为 | `throughput_results.json` |
| `eval/cer_measure.py` | OCR 鲁棒性（合成扫描版逐页 CER，源文本即真值） | `cer_results.json` |

评测题集 `eval/questions.jsonl`：74 题 = routine 29 + paraphrased 20 + out-of-scope 20
（其中 8 题含语料内干扰词，构成更严格的拒答测试）。每题带金标锚点与答案键。
人工裁决记录：`eval/adjudication.json`。

## 关键实测结果（2026-09-23，模型 qwen2.5:7b-instruct-q4_K_M @ 192.168.1.75 Docker/Ollama）

- 检索（生产配置 BM25 uni+bigram+质量重加权）：R@1 0.735 / R@3 0.857 / **R@5 0.878**
  - unigram-only 消融：R@1 0.633（bigram 贡献 +10.2pp）
  - 稠密检索 bge-small-zh-v1.5(CPU)：R@5 0.755（域失配负结果）
- 敏感性：L300 k3 R@3 0.816（最差角）→ L800 k8 R@8 0.918（最好角）；L 增大索引缩小 2.4×
- OCR：合成扫描版逐页 CER 中位 0.72%（聊斋）/ 0.81%（封神）
- 端到端（生产配置，n=74）：库内 HR=0%（人工裁决后），OOS 拒答率 100%，
  库内拒答率 10.2%（其中 2 题检索未中、3 题有据仍拒答）
- 时延：T_ret 58ms 中位；模型阶段 15.6s 中位（prefill 197 tok/s + 解码 8.6 tok/s）；
  飞书 API 往返 0.106s 中位
- 建库：摄入 611s（含 OCR 1531 页）/ 切片 7.6s / 索引 6.6s / 缓存 117MB

## 已知坑

- `merge_public5m.py` 曾把 KB 路径算错一层（产物写到 `Claw/chapters/`）——已修复；
  若发现 `knowledge-base/chapters/public5m` 不存在而 `Claw/chapters/public5m` 存在即此坑。
- 章回体「第X回」标题：`ingest.HEAD_RE` 与 `split_chapters.CH_HEAD` 已支持 `[章篇部卷回]`；
  「叁/两」等大写变体已入 `cn2int`。
- 古籍源文件开头的目录块会在分章时产生大量伪章——`prepare_corpus.drop_toc()` 已处理。
- `eval_ask.py` 在 e2e 进程内测得的 T_ret（0.38s）受进程负载膨胀；受控复测 58ms（以受控值为准）。
