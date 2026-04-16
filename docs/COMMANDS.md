# DataForge Commands Reference

## Router Commands (`/dataforge`)

| Command | Delegates to | Description |
|---------|-------------|-------------|
| `/dataforge run <dataset> <target>` | df-pipeline | Full end-to-end pipeline |
| `/dataforge analyze <dataset> [target]` | df-analysis | Data analysis without modeling |
| `/dataforge eda <dataset>` | df-eda | EDA only |
| `/dataforge preprocess <dataset> <target>` | df-preprocess | Preprocessing only |
| `/dataforge train <dataset> <target>` | df-modeling | Train + evaluate models |
| `/dataforge deploy <project-dir>` | df-deploy | Generate deployment app |
| `/dataforge report <project-dir>` | df-report | Generate HTML/PDF report |
| `/dataforge validate <dataset>` | df-preprocess | Data quality checks only |
| `/dataforge status <project-dir>` | df-experiment | View experiment history |
| `/dataforge resume <project-dir>` | df-pipeline | Resume interrupted pipeline |
| `/dataforge monitor <dir> --new-data <path>` | df-experiment | Drift detection |
| `/dataforge compare <project-dir>` | df-experiment | Compare experiment runs |

---

## Skill Commands (directly invocable)

### df-preprocess

| Command | Description |
|---------|-------------|
| `/df-preprocess ingest <dataset>` | Load data into project data/raw/ |
| `/df-preprocess validate <dataset> [target]` | Quality gate checks only |
| `/df-preprocess profile <dataset>` | Profile + auto-detect problem type |
| `/df-preprocess features <dataset> <target>` | Full: ingest + validate + profile + feature engineering |

### df-eda

| Command | Description |
|---------|-------------|
| `/df-eda <dataset>` | Full EDA: per-column parallel + global analysis |
| `/df-eda column <dataset> <col>` | Single-column deep dive |
| `/df-eda global <dataset> [target]` | Correlation heatmap, target distribution, missing matrix |
| `/df-eda summary <project-dir>` | Print EDA summary from existing results |

### df-modeling

| Command | Description |
|---------|-------------|
| `/df-modeling train <dataset> <target>` | Train all models in parallel, evaluate, rank |
| `/df-modeling evaluate <project-dir>` | Re-rank existing trained models |
| `/df-modeling interpret <project-dir>` | SHAP + feature importance for best model |
| `/df-modeling visualize <project-dir>` | Generate evaluation plots |

### df-experiment

| Command | Description |
|---------|-------------|
| `/df-experiment status <project-dir>` | Print memory summary |
| `/df-experiment compare <project-dir>` | Compare experiments across runs |
| `/df-experiment monitor <dir> --new-data <path>` | Drift detection |
| `/df-experiment history <project-dir>` | Full experiment timeline |

### df-deploy

| Command | Description |
|---------|-------------|
| `/df-deploy <project-dir>` | Generate Streamlit app (default) |
| `/df-deploy <project-dir> --production` | Generate FastAPI app with Docker |

### df-report

| Command | Description |
|---------|-------------|
| `/df-report <project-dir>` | Full report (EDA + models + SHAP) |
| `/df-report eda <project-dir>` | EDA-only report |

---

## Workflow Commands (directly invocable)

### df-analysis

```
/df-analysis <dataset> [target]
```

Steps: ingest -> validate -> profile -> EDA (parallel) -> feature engineering -> report

### df-pipeline

```
/df-pipeline <dataset> <target> [--production]
```

Steps: memory load -> ingest -> validate -> profile -> EDA -> features -> train (parallel) -> evaluate -> interpret + visualize -> deploy -> report -> CLAUDE.md

---

## Flags

| Flag | Effect |
|------|--------|
| `--production` | Use FastAPI instead of Streamlit for deployment |

---

## Examples

```
# Binary classification - full pipeline
/dataforge run data/titanic.csv Survived

# Regression
/dataforge run data/housing.csv SalePrice

# Clustering (no target)
/dataforge run data/customers.csv

# Production API deployment
/dataforge run data/fraud.csv is_fraud --production

# Quick EDA exploration
/dataforge eda data/mydata.csv

# Just preprocessing
/dataforge preprocess data/churn.csv Churn

# Train models on preprocessed data
/df-modeling train data/processed/train.csv Survived

# Check experiment history
/dataforge status titanic/

# Resume after interruption
/dataforge resume titanic/

# Monitor for drift
/dataforge monitor titanic/ --new-data data/new_batch.csv

# Validate before sharing data
/dataforge validate data/newdata.csv

# Single-column deep dive
/df-eda column data/titanic.csv Age

# Regenerate report
/dataforge report titanic/
```

---

## Scripts Reference

All scripts in `scripts/` are standalone CLI tools. See `scripts/README.md` for
full CLI interface documentation.

| Script | Purpose |
|--------|---------|
| `ingest.py` | Multi-format data loader |
| `data_profiler.py` | Dataset profiler + problem type detection |
| `validate.py` | Quality gates (exit codes 0/1/2) |
| `eda.py` | Per-column + global EDA analysis |
| `features.py` | Per-column feature transforms |
| `train.py` | Model training with 5-fold CV |
| `evaluate.py` | Model ranking + leaderboard |
| `interpret.py` | SHAP feature importance |
| `visualize.py` | Evaluation plots |
| `deploy_detect.py` | Deployment target selection |
| `report.py` | HTML/PDF report assembly |
| `memory_read.py` | Memory file reader |
| `memory_write.py` | Concurrent-safe memory writer |

---

## Agents Reference

| Agent | Purpose | Spawned by |
|-------|---------|-----------|
| `df-ingest` | Data ingestion | df-preprocess |
| `df-validate` | Quality gate (exit codes) | df-preprocess, df-pipeline |
| `df-eda-column` | Per-column EDA (parallel) | df-eda |
| `df-eda-global` | Global EDA (heatmap, target dist) | df-eda |
| `df-feature-column` | Per-column feature engineering | df-preprocess |
| `df-train-model` | Single model training (parallel) | df-modeling |
| `df-evaluate` | Model ranking + leaderboard | df-modeling |
| `df-interpret` | SHAP interpretation | df-modeling |
| `df-visualize` | Evaluation plots | df-modeling |
| `df-deploy` | Deployment app generation | df-deploy |
| `df-report` | Report assembly | df-report |
| `df-monitor` | Drift detection | df-experiment |
