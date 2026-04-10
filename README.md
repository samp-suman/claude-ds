# DataForge — Autonomous Data Science Plugin for Claude Code

> **Repo:** `claude-ds` | **Plugin name:** `DataForge` | **Skill command:** `/dataforge`

DataForge is a Claude Code skill plugin that transforms any dataset into a complete,
production-grade Data Science project. Give it a CSV and a target column -- it handles
everything: EDA, feature engineering, parallel model training, SHAP interpretability,
Streamlit/FastAPI deployment, and a PDF report. Expert agents (senior data scientists,
statisticians, and domain specialists) review each stage to catch mistakes and
apply domain-specific best practices.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [All Commands](#all-commands)
6. [Skills & Workflows](#skills--workflows)
7. [Expert Agents](#expert-agents)
8. [What Gets Generated](#what-gets-generated)
9. [Parallel Execution](#parallel-execution)
10. [Memory System](#memory-system)
11. [Quality Gates](#quality-gates)
12. [Extending DataForge](#extending-dataforge)
13. [Development Workflow](#development-workflow)
14. [Changelog](#changelog)

---

## What It Does

```
You:        /dataforge run data/titanic.csv Survived
DataForge:  Ingest -> Validate -> EDA (parallel) -> Features (parallel)
            -> Train 5 models simultaneously -> Evaluate -> SHAP
            -> Streamlit app -> PDF report

Generated:  titanic/
            ├── src/models/lightgbm.pkl        <- Best model (ROC-AUC: 0.923)
            ├── app/app.py                     <- Runnable Streamlit app
            ├── reports/final_report.html      <- Full HTML report
            ├── memory/decisions.md            <- Why each choice was made
            └── CLAUDE.md                      <- Auto-loads context next session
```

---

## Architecture

DataForge follows a modular **skill + workflow** architecture:

```
┌──────────────────────────────────────────────────────┐
│  /dataforge <command>                                │
│  Router: parses command, delegates to skill/workflow  │
└──────────────┬───────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────┐
│  WORKFLOWS                                           │
│  dataforge-pipeline  (full end-to-end)               │
│  dataforge-analysis  (EDA without modeling)           │
└──────────────┬───────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────┐
│  SKILLS (atomic, independently invocable)            │
│  preprocess │ eda │ modeling │ experiment             │
│  deploy     │ report                                 │
└──────────────┬───────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────┐
│  EXPERT AGENTS (9 review + verify + guide)            │
│  methodology (DS, stats) + domain (6 domains) + lead │
└──────────────┬───────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────┐
│  AGENTS (12 execution agents for parallel work)      │
│  + SCRIPTS (16 Python CLI tools)                     │
└──────────────────────────────────────────────────────┘
```

```
claude-ds/                     <- Development repo (this repo)
├── skills/                    <- 9 skill/workflow directories
│   ├── dataforge/             <- Router
│   ├── dataforge-preprocess/  <- Atomic: ingest, validate, features
│   ├── dataforge-eda/         <- Atomic: EDA analysis + plots
│   ├── dataforge-modeling/    <- Atomic: train, evaluate, SHAP
│   ├── dataforge-experiment/  <- Atomic: tracking, comparison
│   ├── dataforge-deploy/      <- Atomic: Streamlit/FastAPI
│   ├── dataforge-report/      <- Atomic: HTML/PDF report
│   ├── dataforge-analysis/    <- Workflow: preprocess + EDA + report
│   └── dataforge-pipeline/    <- Workflow: full pipeline
├── agents/                    <- 21 agents (12 execution + 9 expert)
├── scripts/                   <- 16 Python CLI scripts
├── references/                <- 12 reference docs (6 general + 6 domain)
├── schema/                    <- JSON schemas
├── hooks/                     <- Pre/Post tool use hooks
├── extensions/                <- Kaggle, MLflow
├── docs/                      <- ARCHITECTURE.md, COMMANDS.md
├── requirements.txt
├── install.sh
└── CLAUDE.md                  <- Project constitution
```

---

## Installation

### Prerequisites

- Claude Code CLI installed
- Python 3.9+

### Step 1 -- Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/claude-ds.git
cd claude-ds
```

### Step 2 -- Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3 -- Install the plugin

```bash
bash install.sh
```

This copies all skills, agents, scripts, references, schema, and hooks to `~/.claude/`.

### Step 4 -- Restart Claude Code

Close and reopen Claude Code. The `/dataforge` command and all sub-skills will be available.

### Verify installation

```bash
ls ~/.claude/skills/ | grep dataforge
ls ~/.claude/agents/ | grep "^df-"
ls ~/.claude/scripts/
```

---

## Quick Start

```bash
cd ~/my-projects
claude

# Full pipeline
/dataforge run data/churn.csv Churn

# Just analyze (no modeling)
/dataforge analyze data/churn.csv Churn

# Just EDA
/dataforge eda data/churn.csv

# Train models on preprocessed data
/dataforge train data/processed/train.csv Churn

# Check history
/dataforge status churn/

# Resume interrupted pipeline
/dataforge resume churn/
```

---

## All Commands

| Command | Description |
|---------|------------|
| `/dataforge run <dataset> <target>` | Full pipeline -- ingest through report |
| `/dataforge analyze <dataset> [target]` | Data analysis without modeling |
| `/dataforge eda <dataset>` | EDA only -- parallel per-column + global |
| `/dataforge preprocess <dataset> <target>` | Preprocessing + feature engineering |
| `/dataforge train <dataset> <target>` | Train all models, evaluate, rank |
| `/dataforge validate <dataset>` | Data quality checks + leakage detection |
| `/dataforge deploy <project-dir>` | Generate Streamlit/FastAPI app |
| `/dataforge report <project-dir>` | Regenerate HTML/PDF report |
| `/dataforge status <project-dir>` | Show experiment history |
| `/dataforge resume <project-dir>` | Resume interrupted pipeline |
| `/dataforge monitor <dir> --new-data <path>` | Drift detection |
| `/dataforge compare <project-dir>` | Compare experiment runs |

### Flags

| Flag | Effect |
|------|--------|
| `--production` | Use FastAPI instead of Streamlit |

See `docs/COMMANDS.md` for full command reference with all sub-commands.

---

## Skills & Workflows

### Atomic Skills (independently invocable)

| Skill | Direct command | Purpose |
|-------|---------------|---------|
| `dataforge-preprocess` | `/dataforge-preprocess features <data> <target>` | Ingest, validate, profile, feature engineering |
| `dataforge-eda` | `/dataforge-eda <data>` | EDA: stats, plots, correlations, domain insights |
| `dataforge-modeling` | `/dataforge-modeling train <data> <target>` | Train, evaluate, interpret, visualize |
| `dataforge-experiment` | `/dataforge-experiment status <dir>` | Experiment tracking, comparison, drift |
| `dataforge-deploy` | `/dataforge-deploy <dir>` | Streamlit/FastAPI app generation |
| `dataforge-report` | `/dataforge-report <dir>` | HTML/PDF report generation |

### Workflows (composite)

| Workflow | Command | Steps |
|----------|---------|-------|
| `dataforge-analysis` | `/dataforge analyze <data>` | preprocess -> EDA -> report |
| `dataforge-pipeline` | `/dataforge run <data> <target>` | preprocess -> EDA -> modeling -> deploy -> report |

---

## Expert Agents

DataForge includes an expert review layer that catches mistakes a junior data
scientist would miss. Experts trigger adaptively based on data complexity.

### How It Works

```
Stage completes -> expert_triage.py (complexity score)
  score < 0.2:   skip (no review, no token cost)
  score 0.2-0.5: light (lead expert only)
  score > 0.5:   full (methodology + domain experts + lead)
```

Always full review with `--production`, first run, or explicit `--domain` flag.

### Expert Types

| Type | Agents | What They Check |
|------|--------|----------------|
| **Methodology** | Data Scientist, Statistician | Pipeline correctness, overfitting, leakage, statistical validity |
| **Domain** | Healthcare, Finance, Marketing, Retail, Social, Manufacturing | Domain-specific features, metrics, thresholds, regulatory concerns |
| **Lead** | Lead Expert | Collates all findings, applies auto-corrections, returns verdict |

### Supported Domains (auto-detected)

| Domain | Example Signals | Key Expertise |
|--------|----------------|---------------|
| Healthcare | patient, diagnosis, HbA1c, BMI | Clinical thresholds, HIPAA, sensitivity-focused metrics |
| Finance | transaction, credit, fraud, balance | Temporal splits, fair lending, Gini/KS metrics |
| Marketing | campaign, churn, CLV, conversion | RFM segmentation, cohort analysis, lift charts |
| Retail | product, order, inventory, price | Demand forecasting, price elasticity, stockout handling |
| Social | post, engagement, sentiment, follower | Engagement rates, bot detection, text preprocessing |
| Manufacturing | sensor, temperature, vibration, defect | Rolling aggregations, SPC, predictive maintenance |

### Checkpoints

| # | After Stage | Reviews |
|---|-------------|---------|
| 1 | Preprocessing | Imputation, encoding, feature drops, leakage |
| 2 | EDA | Distributions, correlations, outliers, domain patterns |
| 3 | Modeling | Train-test gap, metric selection, SHAP sanity |

### Verdicts

- **approve** -- pipeline continues
- **flag** -- continue, advisories logged to `memory/decisions.md`
- **block** -- pause, critical issue presented to user for review

---

## What Gets Generated

After a full pipeline run:

```
{project_name}/
├── CLAUDE.md                     <- Auto-loads context in future sessions
├── dataforge.config.json         <- Project config
├── Makefile                      <- make serve | make test
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/                      <- Original data (never modified)
│   ├── interim/                  <- profile, validation, EDA summary
│   └── processed/                <- train.csv (cleaned + engineered)
│
├── src/
│   ├── models/                   <- .pkl artifacts + leaderboard.json
│   ├── inference.py              <- Prediction entry point
│   ├── data_pipeline.py
│   ├── feature_engineering.py
│   ├── model_training.py
│   └── evaluation.py
│
├── reports/
│   ├── eda/                      <- Per-column plots + stats
│   ├── shap_summary.png          <- Feature importance
│   ├── confusion_matrix.png
│   ├── model_comparison.png
│   └── final_report.html         <- Master report
│
├── app/
│   ├── app.py                    <- Streamlit/FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
└── memory/
    ├── experiments.json           <- Run history
    ├── decisions.md               <- Why choices were made
    ├── failed_transforms.json     <- What didn't work
    └── best_pipelines.json        <- Winning configs
```

---

## Parallel Execution

| Stage | Parallelism |
|-------|------------|
| EDA | One agent per column (batch <= 10) |
| Feature engineering | One agent per column (batch <= 10) |
| **Model training** | **All models in one batch** |
| Interpret + Visualize | Both simultaneously |
| **Expert review (full)** | **Methodology + domain parallel, then lead** |
| Validate | Sequential (gate) |

---

## Memory System

Every generated project keeps persistent memory in `memory/`:

| File | Purpose |
|------|---------|
| `experiments.json` | Full record of every model run |
| `decisions.md` | Why each choice was made |
| `failed_transforms.json` | Bad transforms to skip next time |
| `best_pipelines.json` | Winning configs (seeds future runs) |

---

## Quality Gates

Validation runs before anything else:

| Check | Threshold | Action |
|-------|-----------|--------|
| Minimum rows | < 50 | HARD STOP |
| Target missing | Not found | HARD STOP |
| Target leakage | Correlation >= 0.99 | HARD STOP |
| Class imbalance | > 10:1 | Warning |
| High missing | > 50% per column | Warning |
| Duplicates | > 5% | Warning |

---

## Extending DataForge

### Add a new model

1. Add a row to `references/model-catalog.md`
2. Add a handler in `scripts/train.py`'s `get_model()` registry
3. Run `bash install.sh`

### Add a new data source

1. Add a format handler in `scripts/ingest.py`'s `load_data()` function
2. Add detection logic in `detect_format()`
3. Run `bash install.sh`

### Add a new skill

1. Create `skills/dataforge-{name}/SKILL.md`
2. Add routing entry in `skills/dataforge/SKILL.md`
3. Run `bash install.sh`

---

## Supported Problem Types

| Type | Detection | Models |
|------|----------|--------|
| Binary classification | Target <= 2 unique | LightGBM, XGBoost, RF, Logistic, CatBoost |
| Multiclass | Target 3-20 unique | Same, reports f1_weighted |
| Regression | Target float/int > 20 unique | LightGBM, XGBoost, RF, Ridge, Lasso, Linear |
| Clustering | No target column | KMeans, DBSCAN, Hierarchical |
| Time series | Datetime index + numeric target | LightGBM with lag features |

## Supported Input Formats

CSV, TSV, JSON, JSONL, Parquet, Excel (.xlsx/.xls), SQLite (.db/.sqlite),
SQLAlchemy URI, HTTP/HTTPS URL, Pickle, Kaggle slug

---

## Development Workflow

```bash
# 1. Edit source files in claude-ds/
# 2. Sync to ~/.claude/
bash install.sh

# 3. Test the change
/dataforge validate data/test.csv

# 4. Update CHANGELOG.md
# 5. Commit and push
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

Current version: **v0.3.0** (2026-04-10) -- Expert Agent Layer
