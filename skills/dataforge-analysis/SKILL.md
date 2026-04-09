---
name: dataforge-analysis
description: >
  Data Analysis workflow for DataForge. Orchestrates a complete data analysis
  pipeline: ingest, validate, profile, preprocess, EDA, and report generation.
  Use when you want to understand a dataset without building models. Triggers on:
  "analyze dataset", "data analysis", "analyze data", "understand data",
  "explore dataset".
user-invokable: true
argument-hint: "<dataset-path> [target-column]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Data Analysis Workflow

> Complete data analysis pipeline: ingest -> validate -> profile -> EDA -> report.
> Use this when you want to understand a dataset without training models.

## Usage

```
/dataforge-analysis <dataset> [target]
/dataforge analyze <dataset> [target]
```

---

## ORCHESTRATION

This workflow delegates to atomic skills in sequence. It does NOT duplicate
any skill logic — it calls each skill and passes outputs forward.

### Step 0 — Parse Input

Extract from user's message:
- `DATASET_PATH`: path to the input data file
- `TARGET_COL`: target column name (optional — enhances analysis if provided)
- `PROJECT_NAME`: derive from dataset filename without extension
- `OUTPUT_DIR`: `{PROJECT_NAME}/` in the current working directory

If `DATASET_PATH` is missing: ask the user to provide it.

### Step 1 — Preprocessing (Ingest + Validate + Profile)

Invoke the `dataforge-preprocess` skill:

**If target provided:**
Run the full preprocessing pipeline:
1. Ingest: `python3 ~/.claude/scripts/ingest.py --source "{DATASET_PATH}" --output-dir "{OUTPUT_DIR}"`
2. Validate: Spawn `df-validate` agent with `dataset_path`, `target_column`, `output_dir`
   - **CRITICAL**: If exit_code 2 (HARD STOP) — report failure and stop
3. Profile: `python3 ~/.claude/scripts/data_profiler.py --data "{OUTPUT_DIR}/data/raw/{filename}" --output "{OUTPUT_DIR}/data/interim/profile.json" --target "{TARGET_COL}"`
4. Write `dataforge.config.json`

**If no target:**
Run ingest + profile only (no validation of target).

### Step 2 — Exploratory Data Analysis

Invoke the `dataforge-eda` skill:

1. Read column list from `profile.json`
2. Spawn `df-eda-column` agents in parallel (batches of <= 10) for per-column analysis
3. Spawn `df-eda-global` in parallel for correlation heatmap + target distribution
4. Merge results into `eda_summary.json`
5. Write `src/data_pipeline.py`

### Step 3 — Feature Engineering (Optional)

If target is provided, run feature engineering to produce `data/processed/train.csv`:
- Spawn `df-feature-column` agents in parallel based on EDA recommendations
- This prepares data for future modeling without running models now

### Step 4 — Report Generation

Invoke the `dataforge-report` skill in EDA-only mode:
- Spawn `df-report` agent with EDA-only context
- Generates `reports/final_report.html` with EDA sections only

### Step 5 — Print Summary

```
Data Analysis Complete for {PROJECT_NAME}

Dataset:    {n_rows} rows x {n_cols} columns
Problem:    {PROBLEM_TYPE} (auto-detected)
Target:     {TARGET_COL}

Key Findings:
- {n_missing} columns with missing values
- {n_skewed} skewed features
- {n_outlier_cols} columns with outliers
- Top correlations: {top_3_correlations}

Reports:    {OUTPUT_DIR}/reports/final_report.html
EDA plots:  {OUTPUT_DIR}/reports/eda/

Next steps:
- Train models: /dataforge-modeling train {OUTPUT_DIR}/data/processed/train.csv {TARGET_COL}
- Full pipeline: /dataforge run {DATASET_PATH} {TARGET_COL}
```

---

## RESUME SUPPORT

Check what already exists before running each step:
- `data/raw/` has files -> skip ingest
- `data/interim/validation_report.json` -> skip validate
- `data/interim/profile.json` -> skip profile
- `data/interim/eda_summary.json` -> skip EDA
- `reports/final_report.html` -> skip report

---

## ERROR HANDLING

Delegates error handling to the individual skills. This workflow only adds:
- If validation HARD STOPs: print the specific failure and suggest fixes
- If EDA fails partially: continue with available results
- If report fails: print summary to console instead
