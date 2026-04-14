---
area: ai-researcher
category: role
track: common
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area ai-researcher
status: seed
schema_version: 1.0
---

# AI Researcher — SOTA Awareness and Cross-track Inputs

> This role tracks fast-moving research and feeds insights to track-specific
> experts. Refresh aggressively (TTL 14d default).

## Tabular SOTA (as of seed date)

### [air-tab-001] Gradient boosted trees still dominate small-medium tabular
**Summary:** XGBoost / LightGBM / CatBoost are the stable triumvirate. Diff is small once tuned. CatBoost wins on heavy categorical, LightGBM on speed, XGBoost on regulated/audited environments.

### [air-tab-002] Tabular deep learning has not displaced GBDTs
**Summary:** TabNet, FT-Transformer, SAINT, NODE, and TabPFN are interesting but rarely beat tuned LGBM on real datasets <1M rows. TabPFN works zero-shot on small (<10k row) datasets and is improving fast.

### [air-tab-003] AutoML maturity
**Summary:** AutoGluon, FLAML, H2O AutoML reliably reach within 2-5% of expert-tuned models in <1 hour. Use as a strong baseline before manual work.

## DL SOTA (as of seed date - track populated in v0.5)

### [air-dl-001] Foundation models for vision
**Summary:** DINOv2 / SAM / EVA / CLIP variants for embeddings. timm catalogs the strongest backbones. Linear probing on a frozen DINOv2 often beats end-to-end finetuning of smaller models.

### [air-dl-002] LoRA / QLoRA dominance for finetuning
**Summary:** PEFT library makes parameter-efficient finetuning standard. r=8-16 rank, alpha=2*r, target attention modules. QLoRA (4-bit base) lets 7B-13B models train on a single 24GB GPU.

### [air-dl-003] Mixed precision + gradient checkpointing as defaults
**Summary:** bf16 over fp16 when supported (better range). Activation checkpointing trades 30% speed for 50% memory.

## RAG / LLM SOTA (skeleton; populated in v0.6)

### [air-rag-001] Hybrid retrieval beats dense alone
**Summary:** Dense (embeddings) + sparse (BM25) + reranker (bge-reranker-v2-m3 or Cohere rerank) consistently improves recall@k by 10-20%.

### [air-rag-002] Chunking strategy is high-leverage
**Summary:** Naive 512-token chunks lose context. Recursive splitting on natural boundaries + parent-document retrieval + small-to-big retrieval are the current best practices.

## Thought leaders to track

- **Karpathy** (karpathy.ai, twitter) - training recipes, transformer internals
- **Sebastian Raschka** (sebastianraschka.com, magazine.sebastianraschka.com) - clear ML pedagogy
- **Andrew Ng** (deeplearning.ai, The Batch newsletter) - applied ML
- **Chip Huyen** (huyenchip.com) - ML systems and design
- **Jeremy Howard** (fast.ai) - practical DL
- **Lilian Weng** (lilianweng.github.io) - LLM agents and alignment surveys
- **Simon Willison** (simonwillison.net) - LLM tooling and API patterns
- **Jerry Liu / Harrison Chase** - LlamaIndex / LangChain ecosystem
- **Yannic Kilcher** - paper explanations

## Key sources

- arxiv-sanity-lite, Papers with Code, Hugging Face Daily Papers
- distill.pub (archive)
- ACL anthology, NeurIPS / ICML / ICLR proceedings
- Anthropic / OpenAI / DeepMind / Meta FAIR / Google Research engineering blogs
- HuggingFace blog
