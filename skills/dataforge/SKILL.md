---
name: dataforge
description: >
  Autonomous Data Science project generator. Given a dataset and problem statement,
  generates a complete production-grade DS project: EDA, feature engineering,
  multi-model training (parallel), evaluation, SHAP interpretation, deployment
  (Streamlit/FastAPI/Flask), and PDF report. Triggers on: "data science", "train
  model", "build pipeline", "analyze dataset", "predict", "classification",
  "regression", "clustering", "EDA", "feature engineering", "dataforge",
  "run pipeline", "ml project", "machine learning project".
user-invokable: true
argument-hint: "[command] [dataset-path] [target-column]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Autonomous Data Science Pipeline

> Transforms raw datasets into complete, production-grade Data Science projects.

## Commands

| Command | What it does |
|---------|-------------|
| `/dataforge run <dataset> <target>` | Full pipeline: ingest → validate → EDA → features → train → evaluate → interpret → visualize → deploy → report |
| `/dataforge eda <dataset>` | EDA only: profile, parallel per-column analysis, correlation heatmap, report |
| `/dataforge train <dataset> <target>` | Train all models in parallel, evaluate, rank, write to memory |
| `/dataforge deploy <project-dir>` | Generate Streamlit/FastAPI/Flask app for an existing project |
| `/dataforge report <project-dir>` | Regenerate HTML/PDF report from existing results |
| `/dataforge validate <dataset>` | Data quality checks + leakage detection only |
| `/dataforge status <project-dir>` | Print memory summary: experiments, decisions, best pipeline |
| `/dataforge resume <project-dir>` | Resume an interrupted pipeline from last checkpoint |

---

## ORCHESTRATION — `/dataforge run`

Follow these steps **exactly** in order. Read `references/` files on-demand (only when needed).

### Step 0 — Parse Input

Extract from user's message:
- `DATASET_PATH`: path to the input data file
- `TARGET_COL`: target column name (may be absent for clustering)
- `PROJECT_NAME`: derive from dataset filename without extension (e.g., `titanic.csv` → `titanic`)
- `OUTPUT_DIR`: `{PROJECT_NAME}/` in the current working directory
- `PRODUCTION_FLAG`: true if user said "production" or "api" or "--production"

If `DATASET_PATH` is missing: ask the user to provide it. Do NOT proceed without a dataset.

### Step 1 — Load Memory (if project exists)

```bash
python3 ~/.claude/skills/dataforge/scripts/memory_read.py --project-dir "{OUTPUT_DIR}"
```

Read the output. If memory exists:
- Check `failed_transforms` to avoid repeating bad transforms
- Check `best_pipelines` to seed hyperparameter search
- Check `experiments` to skip identical configurations

### Step 2 — Ingest

```bash
python3 ~/.claude/skills/dataforge/scripts/ingest.py \
  --source "{DATASET_PATH}" \
  --output-dir "{OUTPUT_DIR}"
```

Reads: any format (CSV, JSON, Parquet, Excel, SQLite URI, HTTP URL).
Writes: `{OUTPUT_DIR}/data/raw/{filename}`, `{OUTPUT_DIR}/data/interim/profile_raw.json`.

If ingest fails, report the error clearly. List supported formats. Stop.

### Step 3 — Validate (GATE — must pass before anything else)

Spawn agent: `df-validate`

```
Task: Validate dataset for {PROJECT_NAME}
dataset_path: {OUTPUT_DIR}/data/raw/{filename}
target_column: {TARGET_COL}
output_dir: {OUTPUT_DIR}
```

**CRITICAL**: If the agent returns `"exit_code": 2` (HARD STOP):
- Report the specific validation failure to the user
- Do NOT proceed to any further steps
- Ask the user to resolve the issue and try again

If `"exit_code": 1` (warnings): report warnings to user, then continue.

### Step 4 — Profile

```bash
python3 ~/.claude/skills/dataforge/scripts/data_profiler.py \
  --data "{OUTPUT_DIR}/data/raw/{filename}" \
  --output "{OUTPUT_DIR}/data/interim/profile.json"
```

Read the output JSON to get: column list, dtypes, problem_type detection.

Auto-detect problem type:
- **Classification**: target has ≤ 20 unique values OR is string/bool dtype
- **Regression**: target is float/int with > 20 unique values
- **Clustering**: no target column provided
- **Time Series**: datetime index detected AND target is numeric

Load `references/model-catalog.md` to confirm model selection for detected problem type.

Write `{OUTPUT_DIR}/dataforge.config.json`:
```json
{
  "schema_version": "1.0",
  "project_name": "{PROJECT_NAME}",
  "created_at": "{ISO_TIMESTAMP}",
  "dataset": {
    "raw_path": "data/raw/{filename}",
    "processed_path": "data/processed/train.csv",
    "target_column": "{TARGET_COL}",
    "problem_type": "{PROBLEM_TYPE}",
    "n_rows": 0,
    "n_features": 0
  },
  "deployment": {
    "target": "streamlit",
    "app_path": "app/app.py"
  },
  "dataforge_skill_version": "1.0.0"
}
```

### Step 5 — EDA (Parallel Column Analysis)

Read column list from `profile.json`. Spawn one `df-eda-column` agent **per column**, in parallel batches of ≤ 10.

**Single parallel batch message** (all agents launched simultaneously):
```
Spawn in parallel:
- Agent(df-eda-column): dataset_path={raw_path} column_name=col1 output_dir={OUTPUT_DIR}
- Agent(df-eda-column): dataset_path={raw_path} column_name=col2 output_dir={OUTPUT_DIR}
... (up to 10 at once, then next batch)
```

Also spawn (in parallel with column agents):
- Agent(df-eda-column) with `--mode=global` for correlation heatmap + target distribution

Collect all JSON results. Merge into `{OUTPUT_DIR}/data/interim/eda_summary.json`.
Write `{OUTPUT_DIR}/src/data_pipeline.py` based on EDA findings.

### Step 6 — Feature Engineering (Parallel Column Transforms)

Read EDA summary. For each column with `recommended_transforms`, spawn one `df-feature-column` agent in parallel batches of ≤ 10.

Collect results. Write `{OUTPUT_DIR}/src/feature_engineering.py`.
Save processed dataset to `{OUTPUT_DIR}/data/processed/train.csv`.

### Step 7 — Model Training (All Models in Parallel — SINGLE BATCH)

Load `references/model-catalog.md` to select models for `{PROBLEM_TYPE}`.

**Spawn ALL model agents simultaneously in one response**:

For classification:
- Agent(df-train-model): model=xgboost dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR}
- Agent(df-train-model): model=lightgbm ...
- Agent(df-train-model): model=randomforest ...
- Agent(df-train-model): model=logistic ...
- Agent(df-train-model): model=catboost ... (only if categorical columns > 3)

For regression: replace logistic with linear, add ridge, lasso.
For clustering: kmeans, dbscan, hierarchical (no target needed).

Wait for ALL training agents to complete. Collect JSON results.

### Step 8 — Evaluate

Spawn agent: `df-evaluate`

```
Task: Evaluate and rank models for {PROJECT_NAME}
model_results: {JSON array of all training agent results}
problem_type: {PROBLEM_TYPE}
output_dir: {OUTPUT_DIR}
```

Agent ranks models, writes `src/models/leaderboard.json`, updates memory.
Write `{OUTPUT_DIR}/src/model_training.py` and `{OUTPUT_DIR}/src/evaluation.py`.

### Step 9 — Interpret + Visualize (Parallel)

Spawn BOTH simultaneously:

- Agent(df-interpret): best_model={best_model_name} output_dir={OUTPUT_DIR}
- Agent(df-visualize): output_dir={OUTPUT_DIR} problem_type={PROBLEM_TYPE}

Write `{OUTPUT_DIR}/src/inference.py` with the best model loaded.

### Step 10 — Deploy

```bash
python3 ~/.claude/skills/dataforge/scripts/deploy_detect.py \
  --problem-type "{PROBLEM_TYPE}" \
  --production {PRODUCTION_FLAG} \
  --output "{OUTPUT_DIR}/data/interim/deploy_config.json"
```

Spawn agent: `df-deploy`

```
Task: Generate deployment app for {PROJECT_NAME}
deploy_config: {deploy_config.json contents}
output_dir: {OUTPUT_DIR}
```

### Step 11 — Report

Spawn agent: `df-report`

```
Task: Generate final report for {PROJECT_NAME}
output_dir: {OUTPUT_DIR}
problem_type: {PROBLEM_TYPE}
best_model: {best_model_name}
best_metric: {best_metric_value}
```

### Step 12 — Write CLAUDE.md + Final Memory

Write `{OUTPUT_DIR}/CLAUDE.md` (see template below).

```bash
python3 ~/.claude/skills/dataforge/scripts/memory_write.py \
  --project-dir "{OUTPUT_DIR}" \
  --file decisions \
  --mode append \
  --data "{decisions_json}"
```

Print a clean summary to the user:
```
DataForge complete for {PROJECT_NAME}

Problem type:  {PROBLEM_TYPE}
Best model:    {best_model} ({metric_name}: {metric_value})
Deployment:    {deploy_target} → {OUTPUT_DIR}/app/app.py
Report:        {OUTPUT_DIR}/reports/final_report.html

Run:  cd {OUTPUT_DIR} && make serve
Test: cd {OUTPUT_DIR} && make test
```

---

## CLAUDE.md TEMPLATE

Write this into `{OUTPUT_DIR}/CLAUDE.md` after every full run:

```markdown
# DataForge Project: {PROJECT_NAME}

This is a DataForge-managed Data Science project.

## Quick Context
- Problem type: {PROBLEM_TYPE}
- Target column: {TARGET_COL}
- Best model: {BEST_MODEL} ({BEST_METRIC_NAME}: {BEST_METRIC_VALUE})
- Deployment: {DEPLOY_TARGET} — run `make serve`
- Last run: {TIMESTAMP}

## Working in This Project
1. Read `dataforge.config.json` for project configuration
2. Read `memory/decisions.md` for why choices were made — check it before suggesting changes
3. Run `/dataforge status .` to see full experiment history
4. Run `/dataforge resume .` to continue from last checkpoint

## File Conventions
- `data/raw/` — original data, never modify
- `src/models/` — trained model artifacts (.pkl) + metrics JSON
- `src/inference.py` — entry point for predictions on new data
- `reports/` — all plots and generated reports
- `memory/` — experiment history, decisions, failed transforms

## Adding New Models
Run: `/dataforge train data/processed/train.csv {TARGET_COL}`
DataForge will retrain all models and update the leaderboard.
```

---

## ORCHESTRATION — `/dataforge eda`

1. Steps 0–1 (parse + memory load)
2. Step 2 (ingest)
3. Step 4 (profile only)
4. Step 5 (EDA — all columns in parallel)
5. Spawn df-visualize for EDA plots
6. Spawn df-report for EDA-only report
7. Print summary

---

## ORCHESTRATION — `/dataforge train`

1. Steps 0–1 (parse + memory)
2. Skip ingest if `data/processed/train.csv` exists; otherwise run full ingest + validate + profile + features
3. Step 7 (parallel model training)
4. Step 8 (evaluate)
5. Update memory
6. Print leaderboard

---

## ORCHESTRATION — `/dataforge resume`

1. Read `{OUTPUT_DIR}/dataforge.config.json` to restore project state
2. Read `{OUTPUT_DIR}/memory/experiments.json` to find last completed step
3. Resume from the next incomplete step in the full run sequence
4. Continue to completion

Checkpoint detection (check what exists):
- `data/raw/` has files → ingest done
- `data/interim/validation_report.json` exists → validate done
- `data/interim/profile.json` exists → profile done
- `data/interim/eda_summary.json` exists → EDA done
- `data/processed/train.csv` exists → features done
- `src/models/` has .pkl files → training done
- `src/models/leaderboard.json` exists → evaluate done
- `reports/shap_summary.png` exists → interpret done
- `app/app.py` exists → deploy done
- `reports/final_report.html` exists → report done

---

## QUALITY GATES

Load `references/quality-gates.md` for full rules.

**Hard stops** (exit code 2 — never override without explicit user confirmation):
- Fewer than 50 rows after cleaning
- Target column not found in dataset
- Target leakage: any feature with correlation > 0.99 with target

**Warnings** (exit code 1 — report and continue):
- Class imbalance > 10:1 (suggest SMOTE, report class_weight option)
- Any column > 50% missing (report, use median/mode imputation unless user says otherwise)
- Duplicate rows > 5% (report count, deduplicate automatically)
- Constant columns detected (report names, drop automatically)
- High-cardinality ID-like columns (report names, drop automatically)

---

## PARALLEL EXECUTION RULES

1. Column EDA and feature agents: batch ≤ 10 per parallel invocation
2. Model training: always one single parallel batch (all models at once)
3. Interpret + Visualize: always run in parallel
4. Ingest + Validate: sequential (validate gates everything after it)
5. Profile → EDA → Features → Train: sequential stages, parallel within each stage

After every parallel batch:
- Collect all JSON results
- Log any `"status": "failure"` results to `memory/failed_transforms.json`
- Continue with partial results (never abort the full pipeline on one model/column failure)
- Validate merged result schema before proceeding

---

## REFERENCE FILES (load on-demand)

| File | Load when |
|------|----------|
| `references/model-catalog.md` | After problem type detection (Step 4) |
| `references/feature-recipes.md` | During feature engineering (Step 6) |
| `references/metric-guide.md` | During evaluation (Step 8) |
| `references/deploy-targets.md` | During deployment (Step 10) |
| `references/leakage-patterns.md` | During validation (Step 3) |
| `references/quality-gates.md` | During validation (Step 3) |

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| Dataset file not found | Report path, list supported formats (CSV, JSON, Parquet, Excel, SQLite URI, HTTP URL), stop |
| Unsupported file format | List supported types, stop |
| Validation HARD STOP | Report exact failure, do NOT proceed, ask user to fix |
| Model training failure | Log to `memory/failed_transforms.json`, skip model, continue with others |
| Memory file corrupt | Warn user, reset from schema defaults, continue |
| Python script error | Show stderr, diagnose, suggest fix, do not retry blindly |
| Agent timeout | Report which stage timed out, offer `/dataforge resume` |
| Missing Python package | Show install command: `pip install -r ~/.claude/skills/dataforge/requirements.txt` |
