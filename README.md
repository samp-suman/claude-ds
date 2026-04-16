# DataForge

Autonomous Data Science plugin for [Claude Code](https://claude.ai/claude-code). Drop in a dataset, walk away with a production-grade ML project — EDA, fitted sklearn pipelines, parallel model training, SHAP interpretation, a deployment app, and a polished HTML report.

---

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and working
- Python 3.9+
- (Optional) [Kaggle CLI](https://github.com/Kaggle/kaggle-api) for auto-downloading datasets

## Installation

### Global install (recommended)

Makes DataForge available in every project you open with Claude Code.

```bash
git clone https://github.com/samp-suman/claude-ds.git
cd claude-ds
bash install.sh --venv        # creates virtual env + installs dependencies
```

This copies all skills, agents, scripts, references, and schemas to `~/.claude/`, creates a `claude-ds-env` virtual environment with all Python dependencies, and seeds the knowledge base.

> **Important:** After installing, restart Claude Code (or reload the window) for the `/dataforge` command to become available. Skills are only discovered at startup.

If you prefer to manage dependencies yourself (e.g., in your own conda/venv):

```bash
pip install -r requirements.txt
bash install.sh               # install without --venv
```

### Project-level install

Makes DataForge available only in a specific project. Useful if you don't want it loaded globally or want to pin a specific version per project.

```bash
git clone https://github.com/samp-suman/claude-ds.git
cd claude-ds

# Install into a specific project
bash install.sh --project /path/to/your/project --venv

# Or cd into your project and run without a path (defaults to current directory)
cd /path/to/your/project
bash /path/to/claude-ds/install.sh --project --venv
```

This installs everything to `<your-project>/.claude/` instead of `~/.claude/`. The installer automatically adds `.claude/` to the project's `.gitignore` so plugin files aren't committed.

DataForge commands will only work when Claude Code is opened in that project directory.

> **Important:** Restart Claude Code after installing for skills to be discovered.

### Verify installation

```bash
# Global
ls ~/.claude/skills/ | grep dataforge
ls ~/.claude/agents/ | grep '^df-'

# Project-level
ls /path/to/your/project/.claude/skills/ | grep dataforge
```

### Uninstall

```bash
# Global
bash install.sh --uninstall

# Project-level
bash install.sh --uninstall --project /path/to/your/project

# Also remove the virtual env (optional)
rm -rf ~/.claude/dataforge/claude-ds-env
```

Your knowledge base at `~/.claude/dataforge/knowledge/` is preserved across uninstall/reinstall.

### Reset knowledge base

To wipe the knowledge base and start fresh from baseline seeds:

```bash
bash install.sh --reset-kb
```

This deletes all live KB entries (including researcher-fetched updates) and re-seeds from the baseline files in `references/seed-knowledge/`. Use this if the KB gets corrupted or you want a clean slate.

### Updating

After pulling new changes:

```bash
cd claude-ds
git pull

# Global (add --venv to also update venv packages)
bash install.sh --venv

# Project-level
bash install.sh --project /path/to/your/project --venv
```

---

## Quick start

Open Claude Code in any project directory and run:

```bash
# Full end-to-end pipeline (the most common command)
/dataforge run data/churn.csv Churn

# Explore a dataset without training models
/dataforge analyze data/sales.csv

# EDA only
/dataforge eda data/iris.csv

# Train models on already-preprocessed data
/dataforge train data/processed/train.csv target

# Generate a deployment app from an existing project
/dataforge deploy my-project/

# Generate an HTML report from an existing project
/dataforge report my-project/
```

### What `/dataforge run` does

When you run `/dataforge run <dataset> <target>`, DataForge executes this pipeline automatically:

```
Load data -> Validate -> Profile -> EDA -> Feature engineering -> Train models
-> Evaluate -> SHAP interpretation -> Visualize -> Deploy app -> HTML report
```

Everything runs autonomously. Models train in parallel. The output is a complete project directory with all artifacts.

---

## All commands

### Workflows (multi-step)

| Command | What it does |
|---------|-------------|
| `/dataforge run <dataset> <target>` | Full pipeline — dataset to deployed app |
| `/dataforge analyze <dataset>` | Data analysis without modeling |
| `/dataforge resume <project-dir>` | Resume an interrupted pipeline |

### Individual skills

| Command | What it does |
|---------|-------------|
| `/dataforge eda <dataset>` | Exploratory data analysis |
| `/dataforge preprocess <dataset> <target>` | Ingestion + validation + feature engineering |
| `/dataforge validate <dataset>` | Data quality checks only |
| `/dataforge train <dataset> <target>` | Train + evaluate models |
| `/dataforge deploy <project-dir>` | Generate Streamlit/FastAPI app |
| `/dataforge report <project-dir>` | Generate HTML/PDF report |
| `/dataforge status <project-dir>` | View experiment history |
| `/dataforge monitor <dir> --new-data <path>` | Drift detection |

### Knowledge base

| Command | What it does |
|---------|-------------|
| `/df-learn all` | Refresh the entire knowledge base |
| `/df-learn library --area sklearn` | Refresh one specific library |
| `/df-knowledge status` | Check freshness of each KB area |
| `/df-knowledge search "target encoding"` | Search the knowledge base |

### Flags

| Flag | Works with | Effect |
|------|-----------|--------|
| `--production` | `run`, `deploy` | Generates FastAPI app instead of Streamlit |
| `--force` | `run`, any skill | Re-run even if outputs already exist |
| `--web-search` | `learn` | Allow researcher agents to use web search |
| `--type tabular` | `run` | Override automatic track detection |

---

## Supported inputs

### Data formats

CSV, TSV, JSON, JSONL, Parquet, Excel (.xlsx/.xls), SQLite, SQLAlchemy URI, HTTP/HTTPS URL, Pickle, Kaggle dataset slug.

### Problem types (auto-detected)

| Problem | How it's detected | Models used |
|---------|------------------|-------------|
| Binary classification | Target has 2 unique values | LightGBM, XGBoost, RandomForest, Logistic, CatBoost |
| Multiclass | Target has 3-20 unique values | Same as binary |
| Regression | Target is float/int with >20 unique values | LightGBM, XGBoost, RandomForest, Ridge, Lasso |
| Clustering | No target column provided | KMeans, DBSCAN, Hierarchical |

---

## Generated project structure

After a full pipeline run, DataForge creates this project:

```
my-project/
├── PROJECT_PLAN.md                 # DS Design Document — approach, tracker, results
├── data/
│   ├── raw/                        # Original dataset
│   ├── interim/                    # Intermediate artifacts
│   └── processed/                  # Transformed features
├── artifacts/
│   ├── pipeline_tree.pkl           # Fitted preprocessor for tree models
│   └── pipeline_linear.pkl         # Fitted preprocessor for linear models
├── src/models/                     # Trained model .pkl files
├── reports/
│   ├── eda/                        # EDA plots
│   ├── shap/                       # SHAP interpretation plots
│   └── final_report.html           # Complete HTML report
├── app/
│   ├── app.py                      # Streamlit or FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
├── memory/
│   ├── experiments.json            # Run history
│   ├── decisions.md                # Why each choice was made
│   └── best_pipelines.json         # Winning configurations
├── dataforge.config.json           # Project configuration
└── CLAUDE.md                       # Auto-loads context in future sessions
```

---

## DS Design Document (PROJECT_PLAN.md)

Every DataForge run creates a `PROJECT_PLAN.md` in the project directory — a living DS Design Document that tracks the entire project lifecycle:

- **Problem statement** — dataset, target, problem type, domain
- **Data summary** — row/column counts, missing values, class balance
- **Approach** — preprocessing, feature engineering, and modeling strategies
- **Execution tracker** — stage-by-stage status with duration and notes (updated live as the pipeline runs)
- **Results** — best model, leaderboard, top SHAP features
- **Quality gates** — which checks passed/failed
- **Artifacts** — paths to all generated files
- **Decisions log** — why each choice was made

This document is updated after every pipeline stage, so you always have a clear picture of where the project stands and what approach was taken.

---

## Quality gates

DataForge enforces automatic quality checks throughout the pipeline. If a critical issue is found, the pipeline stops and tells you why.

| Check | When | Action |
|-------|------|--------|
| Too few rows (< 50) | Validation | Hard stop |
| Target column missing | Validation | Hard stop |
| Target leakage (corr >= 0.99) | Validation | Hard stop |
| Post-FE feature leakage (corr > 0.95) | After feature engineering | Hard stop |
| Test holdout not created | Before training | Hard stop |
| Class imbalance (> 10:1) | Validation | Warning + auto class_weight |
| High missing values (> 50%) | Validation | Warning |
| Duplicate rows (> 5%) | Validation | Warning |

---

## Skills reference

Each skill has its own README with detailed usage. Click to learn more:

| Skill | Purpose | Details |
|-------|---------|---------|
| [dataforge](skills/dataforge/) | Command router | Routes `/dataforge` commands to the right skill |
| [df-pipeline](skills/df-pipeline/) | Full pipeline workflow | End-to-end: dataset to deployed app |
| [df-analysis](skills/df-analysis/) | Analysis workflow | Understand data without modeling |
| [df-preprocess](skills/df-preprocess/) | Preprocessing | Ingestion, validation, profiling, feature engineering |
| [df-eda](skills/df-eda/) | Exploratory Data Analysis | Per-column stats, plots, correlations, domain insights |
| [df-modeling](skills/df-modeling/) | Model training | Parallel training, evaluation, SHAP, visualization |
| [df-experiment](skills/df-experiment/) | Experiment tracking | History, comparison, drift monitoring |
| [df-deploy](skills/df-deploy/) | Deployment | Streamlit/FastAPI app generation |
| [df-report](skills/df-report/) | Report generation | HTML/PDF reports with embedded plots |
| [df-learn](skills/df-learn/) | Knowledge refresh | Update KB from library changelogs, domain sources |
| [df-knowledge](skills/df-knowledge/) | Knowledge queries | Browse and search the knowledge base |

---

## Knowledge base

DataForge maintains a continuously-updated knowledge base at `~/.claude/dataforge/knowledge/` that keeps generated code current with library APIs and best practices.

**What's tracked:**
- **Libraries** — sklearn, xgboost, lightgbm, catboost, polars, pandas, optuna, shap
- **Domains** — healthcare, finance, marketing, retail, social, manufacturing, real-estate
- **Roles** — data scientist, ML engineer, data engineer, MLOps, statistician, AI researcher

**How it works:** Researcher agents fetch from whitelisted sources (changelogs, docs, thought-leader content), extract knowledge entries, and merge them into the live KB. The pipeline checks KB freshness before each run and refreshes stale areas automatically.

```bash
/df-knowledge status          # Check what's fresh/stale
/df-learn all                 # Refresh everything
/df-knowledge search "SHAP"   # Search across all areas
```

---

## Extending DataForge

| To add a... | What to do |
|-------------|-----------|
| New model | Edit `references/model-catalog.md` + `scripts/train.py` `get_model()`, then `bash install.sh` |
| New data source | Edit `scripts/ingest.py` `load_data()` + `detect_format()`, then `bash install.sh` |
| New skill | Create `skills/dataforge-{name}/SKILL.md` + add router entry, then `bash install.sh` |
| New domain expert | Create `agents/df-expert-{domain}.md` + seed knowledge in `references/seed-knowledge/domain/{domain}/`, then `bash install.sh` |
| New KB source | Add to `references/seed-knowledge/` or at runtime via `/df-learn --source <url>` |

---

## Architecture

For a detailed look at the system design, agent families, pipeline discipline, and data flow, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

For the full version history, see [CHANGELOG.md](CHANGELOG.md).
