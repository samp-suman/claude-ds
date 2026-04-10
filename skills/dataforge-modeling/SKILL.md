---
name: dataforge-modeling
description: >
  Machine learning modeling skill for DataForge. Handles parallel model training,
  evaluation, ranking, SHAP interpretation, and evaluation visualization. Can be
  used standalone or as part of a workflow. Triggers on: "train model", "model",
  "modeling", "fit model", "evaluate model", "interpret model", "SHAP",
  "feature importance", "leaderboard", "compare models".
user-invokable: true
argument-hint: "[train|evaluate|interpret|visualize] <dataset-path> <target-column>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Modeling Skill

> Model training (parallel), evaluation, ranking, SHAP interpretation, and visualization.

## Commands

| Command | What it does |
|---------|-------------|
| `/dataforge-modeling train <dataset> <target>` | Train all models in parallel, evaluate, rank |
| `/dataforge-modeling evaluate <project-dir>` | Re-rank existing trained models |
| `/dataforge-modeling interpret <project-dir>` | SHAP + feature importance for best model |
| `/dataforge-modeling visualize <project-dir>` | Generate evaluation plots (confusion matrix, ROC, etc.) |

---

## Shared Constants

```
SCRIPTS_DIR = ~/.claude/scripts
REFS_DIR    = ~/.claude/references
```

---

## COMMAND: `train`

### Step 1 — Verify Prerequisites

Check that `{OUTPUT_DIR}/data/processed/train.csv` exists.
- If missing: tell the user to run preprocessing first:
  `/dataforge-preprocess features <dataset> <target>`
- Do NOT attempt to train on raw data.

Read `{OUTPUT_DIR}/dataforge.config.json` for `problem_type` and `target_column`.

### Step 2 — Load Memory

```bash
python3 ~/.claude/scripts/memory_read.py --project-dir "{OUTPUT_DIR}"
```

Check:
- `best_pipelines` — seed hyperparameters from previous winning configs
- `failed_transforms` — skip models that previously failed (if `skip_in_future: true`)
- `experiments` — avoid running identical configurations

### Step 3 — Select Models

Load `~/.claude/references/model-catalog.md` to select models for `{PROBLEM_TYPE}`.

**Classification models:**
- `xgboost` — Robust tabular baseline
- `lightgbm` — Fast, accurate
- `randomforest` — Interpretable, handles imbalance
- `logistic` — Linear baseline
- `catboost` — Only if categorical_columns > 3
- `svm_rbf` — Only if dataset < 10k rows

**Regression models:**
- `xgboost`, `lightgbm`, `randomforest`, `linear`, `ridge`, `lasso`, `catboost`

**Clustering models:**
- `kmeans`, `dbscan`, `hierarchical` (no target needed)

### Step 4 — Train All Models (SINGLE PARALLEL BATCH)

**Spawn ALL model agents simultaneously in one response:**

```
Spawn in parallel:
- Agent(df-train-model): model=xgboost dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR} hyperparams={}
- Agent(df-train-model): model=lightgbm dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR} hyperparams={}
- Agent(df-train-model): model=randomforest dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR} hyperparams={}
- Agent(df-train-model): model=logistic dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR} hyperparams={}
```

Wait for ALL training agents to complete. Collect JSON results.

### Step 5 — Evaluate and Rank

Spawn agent: `df-evaluate`

```
Task: Evaluate and rank models for {PROJECT_NAME}
model_results: {JSON array of all training agent results}
problem_type: {PROBLEM_TYPE}
output_dir: {OUTPUT_DIR}
```

Agent writes `src/models/leaderboard.json` and updates memory.

### Step 5b — Expert Checkpoint: Modeling Review (Optional)

If running as part of a workflow, the workflow handles expert checkpoints.
When running standalone (`/dataforge-modeling train`), run the checkpoint here:

```bash
python3 ~/.claude/scripts/expert_triage.py \
  --stage modeling \
  --leaderboard "{OUTPUT_DIR}/src/models/leaderboard.json" \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --cache-dir "{OUTPUT_DIR}/data/interim/expert_cache" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/triage_modeling.json"
```

Based on `complexity_level`: skip / light (lead only) / full (all experts + lead).
If lead verdict is **block**: pause for user. Otherwise continue.

### Step 6 — Interpret + Visualize (Parallel)

Spawn BOTH simultaneously after evaluation:

```
Spawn in parallel:
- Agent(df-interpret): best_model={best_model_name} output_dir={OUTPUT_DIR} problem_type={PROBLEM_TYPE} dataset_path=data/processed/train.csv target_column={TARGET_COL}
- Agent(df-visualize): output_dir={OUTPUT_DIR} problem_type={PROBLEM_TYPE} best_model={best_model_name} dataset_path=data/processed/train.csv target_column={TARGET_COL}
```

### Step 7 — Write Source Files

Write `{OUTPUT_DIR}/src/model_training.py` — reproducible training code.
Write `{OUTPUT_DIR}/src/evaluation.py` — evaluation code.
Write `{OUTPUT_DIR}/src/inference.py` — prediction entry point for best model.

### Step 8 — Update Memory

```bash
python3 ~/.claude/scripts/memory_write.py \
  --project-dir "{OUTPUT_DIR}" \
  --file experiments \
  --mode append \
  --data '{experiment_json}'
```

### Step 9 — Print Leaderboard

```
Model Training Complete for {PROJECT_NAME}

Problem type: {PROBLEM_TYPE}

| Rank | Model       | {primary_metric} | CV Mean | CV Std |
|------|-------------|-------------------|---------|--------|
| 1    | lightgbm    | 0.923            | 0.918   | 0.012  |
| 2    | xgboost     | 0.918            | 0.915   | 0.014  |
| ...  | ...         | ...              | ...     | ...    |

Best model: {best_model} ({primary_metric}: {best_score})
SHAP top features: {top_3_features}
```

---

## COMMAND: `evaluate`

Re-rank existing models without retraining.

1. Verify `{OUTPUT_DIR}/src/models/` has `.pkl` files
2. Spawn `df-evaluate` agent
3. Print updated leaderboard

---

## COMMAND: `interpret`

Run SHAP interpretation on the best model.

1. Read `{OUTPUT_DIR}/src/models/leaderboard.json` to find best model
2. Spawn `df-interpret` agent
3. Present feature importance analysis:
   - Top 10 features by SHAP value
   - Direction of impact (positive/negative)
   - Domain-relevant observations

---

## COMMAND: `visualize`

Generate evaluation visualizations.

1. Read leaderboard to find best model
2. Spawn `df-visualize` agent
3. Report generated plots:
   - Classification: confusion matrix, ROC curve
   - Regression: residual plot, prediction vs actual
   - All: pairplot (if <= 8 features)

---

## PRIMARY METRICS BY PROBLEM TYPE

| Problem Type | Primary Metric | Higher = Better |
|-------------|---------------|----------------|
| binary_classification | roc_auc | Yes |
| multiclass_classification | f1_weighted | Yes |
| regression | r2 | Yes |
| clustering | silhouette_score | Yes |

Load `~/.claude/references/metric-guide.md` for interpretation help.

---

## PARALLEL EXECUTION RULES

1. Model training: always ONE single parallel batch (all models at once)
2. Interpret + Visualize: always run in parallel after evaluation
3. After parallel batch:
   - Collect all JSON results
   - Log `"status": "failure"` models to `memory/failed_transforms.json`
   - Continue with partial results (never abort full pipeline on one model failure)

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| Processed data missing | Tell user to run `/dataforge-preprocess features` first |
| All models fail | Report errors, suggest checking data quality |
| Single model fails | Log failure, continue with remaining models |
| SHAP fails | Fall back to native feature importance |
| Memory file corrupt | Warn user, reset from schema defaults, continue |
| Missing Python package | Show: `pip install -r requirements.txt` |
