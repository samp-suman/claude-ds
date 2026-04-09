# DataForge Commands Reference

## Router Commands (`/dataforge`)

| Command | Delegates to | Description |
|---------|-------------|-------------|
| `/dataforge run <dataset> <target>` | dataforge-pipeline | Full end-to-end pipeline |
| `/dataforge analyze <dataset> [target]` | dataforge-analysis | Data analysis without modeling |
| `/dataforge eda <dataset>` | dataforge-eda | EDA only |
| `/dataforge preprocess <dataset> <target>` | dataforge-preprocess | Preprocessing only |
| `/dataforge train <dataset> <target>` | dataforge-modeling | Train + evaluate models |
| `/dataforge deploy <project-dir>` | dataforge-deploy | Generate deployment app |
| `/dataforge report <project-dir>` | dataforge-report | Generate HTML/PDF report |
| `/dataforge validate <dataset>` | dataforge-preprocess | Data quality checks only |
| `/dataforge status <project-dir>` | dataforge-experiment | View experiment history |
| `/dataforge resume <project-dir>` | dataforge-pipeline | Resume interrupted pipeline |
| `/dataforge monitor <dir> --new-data <path>` | dataforge-experiment | Drift detection |
| `/dataforge compare <project-dir>` | dataforge-experiment | Compare experiment runs |

---

## Skill Commands (directly invocable)

### dataforge-preprocess

| Command | Description |
|---------|-------------|
| `/dataforge-preprocess ingest <dataset>` | Load data into project data/raw/ |
| `/dataforge-preprocess validate <dataset> [target]` | Quality gate checks only |
| `/dataforge-preprocess profile <dataset>` | Profile + auto-detect problem type |
| `/dataforge-preprocess features <dataset> <target>` | Full: ingest + validate + profile + feature engineering |

### dataforge-eda

| Command | Description |
|---------|-------------|
| `/dataforge-eda <dataset>` | Full EDA: per-column parallel + global analysis |
| `/dataforge-eda column <dataset> <col>` | Single-column deep dive |
| `/dataforge-eda global <dataset> [target]` | Correlation heatmap, target distribution, missing matrix |
| `/dataforge-eda summary <project-dir>` | Print EDA summary from existing results |

### dataforge-modeling

| Command | Description |
|---------|-------------|
| `/dataforge-modeling train <dataset> <target>` | Train all models in parallel, evaluate, rank |
| `/dataforge-modeling evaluate <project-dir>` | Re-rank existing trained models |
| `/dataforge-modeling interpret <project-dir>` | SHAP + feature importance for best model |
| `/dataforge-modeling visualize <project-dir>` | Generate evaluation plots |

### dataforge-experiment

| Command | Description |
|---------|-------------|
| `/dataforge-experiment status <project-dir>` | Print memory summary |
| `/dataforge-experiment compare <project-dir>` | Compare experiments across runs |
| `/dataforge-experiment monitor <dir> --new-data <path>` | Drift detection |
| `/dataforge-experiment history <project-dir>` | Full experiment timeline |

### dataforge-deploy

| Command | Description |
|---------|-------------|
| `/dataforge-deploy <project-dir>` | Generate Streamlit app (default) |
| `/dataforge-deploy <project-dir> --production` | Generate FastAPI app with Docker |

### dataforge-report

| Command | Description |
|---------|-------------|
| `/dataforge-report <project-dir>` | Full report (EDA + models + SHAP) |
| `/dataforge-report eda <project-dir>` | EDA-only report |

---

## Workflow Commands (directly invocable)

### dataforge-analysis

```
/dataforge-analysis <dataset> [target]
```

Steps: ingest -> validate -> profile -> EDA (parallel) -> feature engineering -> report

### dataforge-pipeline

```
/dataforge-pipeline <dataset> <target> [--production]
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
/dataforge-modeling train data/processed/train.csv Survived

# Check experiment history
/dataforge status titanic/

# Resume after interruption
/dataforge resume titanic/

# Monitor for drift
/dataforge monitor titanic/ --new-data data/new_batch.csv

# Validate before sharing data
/dataforge validate data/newdata.csv

# Single-column deep dive
/dataforge-eda column data/titanic.csv Age

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
| `df-ingest` | Data ingestion | dataforge-preprocess |
| `df-validate` | Quality gate (exit codes) | dataforge-preprocess, dataforge-pipeline |
| `df-eda-column` | Per-column EDA (parallel) | dataforge-eda |
| `df-eda-global` | Global EDA (heatmap, target dist) | dataforge-eda |
| `df-feature-column` | Per-column feature engineering | dataforge-preprocess |
| `df-train-model` | Single model training (parallel) | dataforge-modeling |
| `df-evaluate` | Model ranking + leaderboard | dataforge-modeling |
| `df-interpret` | SHAP interpretation | dataforge-modeling |
| `df-visualize` | Evaluation plots | dataforge-modeling |
| `df-deploy` | Deployment app generation | dataforge-deploy |
| `df-report` | Report assembly | dataforge-report |
| `df-monitor` | Drift detection | dataforge-experiment |
