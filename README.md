# DataForge — Autonomous Data Science Plugin for Claude Code

> **Repo:** `claude-ds` | **Plugin name:** `DataForge` | **Skill command:** `/dataforge`

DataForge is a Claude Code skill plugin that transforms any dataset into a complete,
production-grade Data Science project. Give it a CSV and a target column — it handles
everything: EDA, feature engineering, parallel model training, SHAP interpretability,
Streamlit/FastAPI deployment, and a PDF report.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage — Step by Step](#usage--step-by-step)
5. [All Commands](#all-commands)
6. [What Gets Generated](#what-gets-generated)
7. [Parallel Execution](#parallel-execution)
8. [Memory System](#memory-system)
9. [Quality Gates](#quality-gates)
10. [Extending DataForge](#extending-dataforge)
11. [Development Workflow](#development-workflow)
12. [Changelog](#changelog)

---

## What It Does

```
You:        /dataforge run data/titanic.csv Survived
DataForge:  ✓ Ingest → ✓ Validate → ✓ EDA (parallel) → ✓ Features (parallel)
            → ✓ Train 5 models simultaneously → ✓ Evaluate → ✓ SHAP
            → ✓ Streamlit app → ✓ PDF report

Generated:  titanic/
            ├── src/models/lightgbm.pkl        ← Best model (ROC-AUC: 0.923)
            ├── app/app.py                     ← Runnable Streamlit app
            ├── reports/final_report.html      ← Full HTML report
            ├── memory/decisions.md            ← Why each choice was made
            └── CLAUDE.md                      ← Auto-loads context next session
```

---

## Architecture

```
~/.claude/
├── skills/dataforge/         ← Installed skill (source of truth: claude-ds/skills/)
│   ├── SKILL.md              ← Orchestrator brain
│   ├── requirements.txt
│   ├── scripts/              ← 14 Python execution scripts
│   ├── references/           ← 6 on-demand reference docs
│   ├── schema/               ← JSON Schema for config + memory files
│   ├── hooks/                ← PostToolUse + PreToolUse hooks
│   └── extensions/           ← Kaggle, MLflow
│
└── agents/                   ← 11 sub-agents (df-*.md)
    ├── df-eda-column.md      ← Spawned N times in parallel (one per column)
    ├── df-train-model.md     ← Spawned per model (all models simultaneously)
    └── ...

claude-ds/                    ← Development repo (this repo)
├── skills/                   ← Source for ~/.claude/skills/
├── agents/                   ← Source for ~/.claude/agents/df-*.md
├── install.sh                ← Sync dev → ~/.claude/
├── CHANGELOG.md
└── README.md
```

**Two layers:**
- **Layer 1 (Global Skill):** `~/.claude/skills/dataforge/` — installed once, works from any directory
- **Layer 2 (Generated Project):** Written into your working directory when you run a pipeline

---

## Installation

### Prerequisites

- Claude Code CLI installed
- Python 3.9+

### Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/claude-ds.git
cd claude-ds
```

### Step 2 — Install Python dependencies

```bash
pip install -r skills/dataforge/requirements.txt
```

### Step 3 — Install the plugin

```bash
bash install.sh
```

This copies all skill files to `~/.claude/skills/dataforge/` and agents to `~/.claude/agents/`.

### Step 4 — Restart Claude Code

Close and reopen Claude Code (or reload the window). The `/dataforge` command will now be available.

### Verify installation

```bash
# Should show the dataforge skill
ls ~/.claude/skills/dataforge/
ls ~/.claude/agents/ | grep "^df-"
```

---

## Usage — Step by Step

### Your first project

**1. Start Claude Code in a directory with your dataset:**
```bash
cd ~/my-projects
claude  # or open Claude Code IDE extension
```

**2. Run the full pipeline:**
```
/dataforge run data/churn.csv Churn
```

**3. Watch DataForge work:**
- It validates your data (hard stops on leakage or tiny datasets)
- Runs EDA in parallel — one agent per column simultaneously
- Trains XGBoost, LightGBM, RandomForest, LogisticRegression all at once
- Generates SHAP explanations and all plots
- Creates a Streamlit app and HTML/PDF report

**4. Explore the results:**
```bash
cd churn/
make serve        # Start Streamlit app → http://localhost:8501
make test         # Run generated tests
open reports/final_report.html
```

**5. Come back next session:**
```bash
cd churn/
claude            # CLAUDE.md auto-loads project context
/dataforge status .   # See experiment history
```

---

## All Commands

| Command | Description |
|---------|------------|
| `/dataforge run <dataset> <target>` | **Full pipeline** — ingest, validate, EDA, features, train all models, evaluate, interpret, visualize, deploy, report |
| `/dataforge eda <dataset>` | EDA only — profile + parallel per-column analysis + correlation heatmap |
| `/dataforge train <dataset> <target>` | Train all models in parallel, evaluate, update leaderboard |
| `/dataforge validate <dataset>` | Data quality checks + leakage detection only |
| `/dataforge deploy <project-dir>` | Generate Streamlit/FastAPI app for an existing project |
| `/dataforge report <project-dir>` | Regenerate HTML/PDF report from existing results |
| `/dataforge status <project-dir>` | Show memory: experiments, decisions, best pipeline |
| `/dataforge resume <project-dir>` | Resume an interrupted pipeline from last checkpoint |

### Flags

| Flag | Effect |
|------|--------|
| `--production` | Use FastAPI instead of Streamlit for deployment |
| (default) | Streamlit deployment |

### Examples

```
# Binary classification
/dataforge run data/titanic.csv Survived

# Regression
/dataforge run data/housing.csv SalePrice

# Clustering (no target)
/dataforge run data/customers.csv

# Production API
/dataforge run data/fraud.csv is_fraud --production

# EDA only (quick exploration)
/dataforge eda data/mydata.csv

# Resume after interruption
/dataforge resume titanic/

# Check what's been tried
/dataforge status titanic/

# Validate before sharing data
/dataforge validate data/newdata.csv
```

---

## What Gets Generated

After a full run, you get a complete project:

```
{project_name}/
├── CLAUDE.md                     ← Auto-loads context in future Claude sessions
├── dataforge.config.json         ← Project config (target, problem type, paths)
├── Makefile                      ← make train | make serve | make test
├── requirements.txt
├── README.md                     ← Project-specific documentation
│
├── data/
│   ├── raw/                      ← Original data (never modified)
│   ├── interim/                  ← profile.json, validation_report.json, eda_summary.json
│   └── processed/                ← train.csv (cleaned + engineered features)
│
├── src/
│   ├── data_pipeline.py
│   ├── feature_engineering.py
│   ├── model_training.py
│   ├── evaluation.py
│   ├── inference.py              ← Load model + predict on new data
│   ├── config.py
│   └── models/
│       ├── lightgbm.pkl          ← Best model artifact
│       ├── lightgbm_metrics.json
│       ├── xgboost.pkl
│       └── leaderboard.json      ← All models ranked by primary metric
│
├── notebooks/
│   ├── eda.ipynb
│   └── modeling.ipynb
│
├── app/
│   ├── app.py                    ← Streamlit or FastAPI app (runnable)
│   ├── requirements.txt
│   └── Dockerfile
│
├── reports/
│   ├── eda/                      ← Per-column plots + stats JSON
│   │   ├── age_plot.png
│   │   ├── correlation_heatmap.png
│   │   └── target_distribution.png
│   ├── shap_summary.png
│   ├── shap_bar.png
│   ├── confusion_matrix.png
│   ├── model_comparison.png
│   ├── final_report.html         ← Full embedded-image HTML report
│   └── final_report.pdf          ← PDF version (requires WeasyPrint)
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_inference.py
│   └── test_data_quality.py
│
└── memory/
    ├── experiments.json          ← All past runs with metrics
    ├── decisions.md              ← Why each choice was made (human-readable)
    ├── failed_transforms.json    ← Transforms that errored (skipped next run)
    └── best_pipelines.json       ← Top pipelines (seeds future runs)
```

---

## Parallel Execution

DataForge uses Claude Code's native `Agent` tool to spawn multiple sub-agents simultaneously:

| Stage | Parallelism |
|-------|------------|
| EDA | One `df-eda-column` agent per column (batch ≤ 10 at once) |
| Feature engineering | One `df-feature-column` agent per column (batch ≤ 10) |
| **Model training** | **All models in ONE parallel batch** — biggest time saving |
| Interpret + Visualize | Both run simultaneously after best model is selected |
| Validate | Sequential (must gate everything after it) |
| Deploy | Sequential (depends on trained model) |

For a dataset with 15 columns and 5 models, a linear pipeline would call 25 steps sequentially.
DataForge batches them: 2 EDA batches + 1 feature batch + 1 training batch = 4 rounds.

---

## Memory System

Every generated project keeps a persistent memory in `memory/`:

| File | Purpose |
|------|---------|
| `experiments.json` | Full record of every model run (config, metrics, artifact path) |
| `decisions.md` | Plain English log of why each choice was made |
| `failed_transforms.json` | Bad transforms to skip on future runs |
| `best_pipelines.json` | Top configurations (used to seed hyperparameters next time) |

Memory persists across Claude sessions because it lives in your project folder.
On the next run, DataForge reads memory first to skip redundant work.

---

## Quality Gates

Validation runs before anything else. **Hard stops halt the pipeline:**

| Check | Threshold | Action |
|-------|-----------|--------|
| Minimum rows | < 50 | HARD STOP |
| Target column | Not found | HARD STOP |
| Target variance | Only 1 unique value | HARD STOP |
| Target leakage | Correlation ≥ 0.99 with target | HARD STOP |
| Class imbalance | Ratio > 10:1 | Warning — sets class_weight='balanced' |
| High missing | Column > 50% null | Warning — imputes and notifies |
| Duplicate rows | > 5% | Warning — deduplicates automatically |

---

## Extending DataForge

### Add a new model

1. Add a row to `skills/dataforge/references/model-catalog.md`
2. Add a handler in `skills/dataforge/scripts/train.py`'s `get_model()` registry dict
3. Run `bash install.sh`

### Add a new data source

1. Add a format handler in `skills/dataforge/scripts/ingest.py`'s `load_data()` function
2. Add detection logic in `detect_format()`
3. Run `bash install.sh`

### Add a new deployment target

1. Add a row to `skills/dataforge/references/deploy-targets.md`
2. Add detection logic in `skills/dataforge/scripts/deploy_detect.py`
3. Update the `df-deploy` agent's instructions
4. Run `bash install.sh`

### Add a Kaggle dataset

```
/dataforge run kaggle:owner/dataset-name TargetColumn
```

Requires `pip install kaggle` and `~/.kaggle/kaggle.json` credentials.

### Enable MLflow tracking

```bash
pip install mlflow
mlflow server --host 0.0.0.0 --port 5000
export MLFLOW_TRACKING_URI=http://localhost:5000
```

---

## Development Workflow

When making changes to DataForge:

```bash
# 1. Edit source files in claude-ds/
# 2. Update CHANGELOG.md
# 3. Sync to ~/.claude/
bash install.sh

# 4. Test the change
/dataforge validate data/test.csv

# 5. Commit and push
git add .
git commit -m "feat: description of change"
git push
git tag v0.1.x && git push --tags
```

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## Supported Problem Types

| Type | Detection | Models Used |
|------|----------|------------|
| Binary classification | Target ≤ 2 unique values | LightGBM, XGBoost, RF, Logistic, CatBoost |
| Multiclass classification | Target 3–20 unique values | Same + reports f1_weighted |
| Regression | Target is float/int > 20 unique | LightGBM, XGBoost, RF, Ridge, Lasso, Linear |
| Clustering | No target column | KMeans, DBSCAN, Hierarchical |
| Time series | Datetime index + numeric target | LightGBM with lag features |

## Supported Input Formats

CSV, TSV, JSON, JSONL, Parquet, Excel (.xlsx/.xls), SQLite (.db/.sqlite),
SQLAlchemy URI (`sqlite:///db.sqlite?table=users`), HTTP/HTTPS URL, Pickle,
Kaggle slug (`kaggle:owner/dataset-name`)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

Current version: **v0.1.0** (2026-04-04) — Initial release
