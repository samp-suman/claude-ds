# DataForge — Autonomous Data Science Pipeline

> Claude Code plugin that transforms raw datasets into complete, production-grade
> Data Science projects with parallel model training, SHAP interpretation, and
> deployment app generation.

## Architecture

DataForge follows a modular **skill + workflow** architecture:

### Core Skills (10 enhanced atomic skills)

| Skill | Purpose |
|-------|---------|
| `df-preprocess` | Data ingestion, validation, quality gates, incremental processing |
| `df-eda` | Exploratory analysis (parallel per-column + global) |
| `df-feature-architect` | Domain feature engineering, encoding, selection, store design |
| `df-modeling` | Model training, evaluation, interpretation, fairness |
| `df-deploy` | Model serving (batch/online/streaming), optimization, monitoring |
| `df-experiment` | Tracking, drift detection, performance monitoring |
| `df-pipeline` | End-to-end orchestration, stage gates, decisions |
| `df-analysis` | Workflow: preprocess + EDA + report |
| `df-knowledge` | Live knowledge base (read-only) |
| `df-learn` | Knowledge base updates, learning extraction |

### Infrastructure Skills (3 new agent-driven skills)

| Skill | Purpose |
|-------|---------|
| `df-llm-orchestrator` | LLM model selection, caching, evaluation, guardrails, routing |
| `df-mlops-pipeline` | CI/CD, orchestration, event-driven workflows, streaming pipelines |
| `df-distributed-training` | Multi-GPU training, parallel processing, hyperparameter search |

### Specialized Skills (2 domain-specific)

| Skill | Purpose |
|-------|---------|
| `df-rag-orchestrator` | RAG pipeline, chunking, embedding, retrieval, generation |
| `df-report` | HTML/PDF report generation |

### Router

`df` skill parses `/dataforge <command>` and delegates to the appropriate skill or workflow.

## Quick Commands

| Command | What it does |
|---------|-------------|
| `/dataforge run <dataset> <target>` | Full end-to-end pipeline |
| `/dataforge analyze <dataset>` | Data analysis without modeling |
| `/dataforge eda <dataset>` | EDA only |
| `/dataforge preprocess <dataset> <target>` | Preprocessing only |
| `/dataforge train <dataset> <target>` | Train + evaluate models |
| `/dataforge deploy <project-dir>` | Generate deployment app |
| `/dataforge report <project-dir>` | Generate HTML/PDF report |
| `/dataforge validate <dataset>` | Data quality checks only |
| `/dataforge status <project-dir>` | View experiment history |
| `/dataforge resume <project-dir>` | Resume interrupted pipeline |
| `/dataforge monitor <dir> --new-data <path>` | Drift detection |

## Directory Layout

```
claude-ds/
├── skills/                        # 15 skills (SKILL.md + README.md each)
│   ├── df/                        # Router (parses commands, delegates)
│   ├── df-preprocess/             # Core: data ingestion + validation
│   ├── df-eda/                    # Core: exploratory analysis
│   ├── df-feature-architect/      # Core: feature engineering + selection
│   ├── df-modeling/               # Core: training + evaluation + interpretation
│   ├── df-deploy/                 # Core: model serving + optimization
│   ├── df-experiment/             # Core: tracking + drift detection
│   ├── df-pipeline/               # Core: orchestration + stage gates
│   ├── df-analysis/               # Core: workflow (preprocess→EDA→report)
│   ├── df-llm-orchestrator/       # Infrastructure: LLM systems
│   ├── df-mlops-pipeline/         # Infrastructure: CI/CD + orchestration
│   ├── df-distributed-training/   # Infrastructure: multi-GPU training
│   ├── df-rag-orchestrator/       # Specialized: RAG systems
│   ├── df-knowledge/              # Core: knowledge base (read-only)
│   ├── df-learn/                  # Core: knowledge updates
│   └── df-report/                 # Specialized: reporting
├── agents/                        # Expert agents (triggered adaptively)
├── scripts/                       # Python CLI tools (all computation)
├── references/                    # Reference docs (domain + general)
├── schema/                        # JSON schemas (config, memory)
├── docs/                          # Architecture, commands, design docs
├── .analysis-tmp/                 # Temporary analysis files (not git-tracked)
├── requirements.txt               # Python dependencies
├── install.sh                     # Installation script
├── CHANGELOG.md                   # Version history
├── CLAUDE.md                      # This file (project instructions)
└── README.md                      # Installation + usage guide
```

## Conventions

**Architecture Principles:**
- Agent-driven decision making (not script heuristics)
- Domain detection → agent-based (analyzes project context, selects tools)
- Researcher/learning systems → agent-driven (autonomous knowledge extraction)
- Skills are atomic, independently invocable, composable

**Implementation:**
- Scripts are standalone CLI tools; support shell invocation
- Agents communicate via JSON-in, JSON-out contract
- Memory persists in project folder (`memory/` directory)
- Quality gates: exit code 2 = HARD STOP, exit code 1 = warnings, exit code 0 = pass
- Each SKILL.md documents: purpose, when-to-use, responsibilities, scenarios, anti-patterns, checklist
- Decision logging: every choice tracked with rationale for reproducibility
- Lineage tracking: all transformations documented with audit trail

**Scale & Optimization:**
- Parallel execution: column operations batch ≤ 10; model training single batch
- Distributed training: multi-GPU support via df-distributed-training skill
- Caching: prompt caching (LLM), feature store caching (inference)
- Reference files: loaded on-demand, never all at startup

## Installation

```bash
bash install.sh              # Install to ~/.claude/
bash install.sh --uninstall  # Remove
pip install -r requirements.txt
```

## Working on This Repo

- Read `docs/ARCHITECTURE.md` for system design
- Read `docs/COMMANDS.md` for all commands reference
- Read `CHANGELOG.md` before making changes
- Always update CHANGELOG.md after changes
- Test changes with: `/dataforge run titanic.csv Survived`
- Scripts must not import from each other (standalone CLI tools)
- Run `bash install.sh` after any changes to sync to `~/.claude/`
