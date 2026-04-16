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

**How it works:**
1. User calls `/dataforge run <dataset> <target>` (or `/df` prefix)
2. Router skill (`df` or `dataforge` alias) receives command
3. Router parses command and delegates to appropriate skill:
   - `run` → `df-pipeline` (orchestrates all 7 stages)
   - `analyze` → `df-analysis` (workflow: preprocess→eda→report)
   - `eda` → `df-eda` (exploratory analysis only)
   - `preprocess` → `df-preprocess` (data prep only)
   - `train` → `df-modeling` (model training & evaluation)
   - `deploy` → `df-deploy` (production deployment)
   - `report` → `df-report` (generate reports)
   - `status` / `monitor` → `df-experiment` (tracking & drift)
   - `resume` → `df-pipeline` (resume from checkpoint)
   - `knowledge` → `df-knowledge` (knowledge base)
   - `learn` → `df-learn` (knowledge updates)

4. Delegated skill executes and returns JSON results
5. Results persist in project `memory/` folder
6. Router returns output to user

## Quick Commands

**Both prefixes work:** `/dataforge` and `/df` (interchangeable)

| Command | Execution Path | What it does |
|---------|---|---|
| `/dataforge run <dataset> <target>` | df-pipeline | Full end-to-end (preprocess → eda → features → model → deploy → report) |
| `/dataforge analyze <dataset>` | df-analysis | Data analysis (preprocess → eda → report, no modeling) |
| `/dataforge preprocess <dataset> <target>` | df-preprocess | Data ingestion, validation, quality gates |
| `/dataforge eda <dataset>` | df-eda | Exploratory analysis and profiling |
| `/dataforge train <dataset> <target>` | df-modeling | Train, evaluate, rank models |
| `/dataforge deploy <project-dir>` | df-deploy | Deploy to production (batch/online/streaming) |
| `/dataforge report <project-dir>` | df-report | Generate HTML/PDF report |
| `/dataforge status <project-dir>` | df-experiment | View experiment history and metrics |
| `/dataforge resume <project-dir>` | df-pipeline | Resume from checkpoint |
| `/dataforge monitor <dir> --new-data <path>` | df-experiment | Detect drift, trigger retraining |
| `/dataforge knowledge <query>` | df-knowledge | Search knowledge base |
| `/dataforge learn [scope]` | df-learn | Extract learnings from projects |

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
