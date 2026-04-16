---
name: df-preprocess
description: >
  Data preprocessing skill for DataForge. Handles data ingestion, validation,
  profiling, and feature engineering. Can be used standalone or as part of a
  workflow. Triggers on: "preprocess", "ingest", "validate data", "clean data",
  "feature engineering", "data cleaning", "data preparation".
user-invokable: true
argument-hint: "[ingest|validate|profile|features] <dataset-path> [target-column]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Preprocess Skill

> Data ingestion, validation, profiling, and feature engineering.

## Commands

| Command | What it does |
|---------|-------------|
| `/df-preprocess ingest <dataset>` | Load data into project `data/raw/` |
| `/df-preprocess validate <dataset> [target]` | Quality gate checks only |
| `/df-preprocess profile <dataset>` | Profile + auto-detect problem type |
| `/df-preprocess features <dataset> <target>` | Full: ingest + validate + profile + feature engineering |

---

## Shared Constants

```
SCRIPTS_DIR = ~/.claude/scripts
REFS_DIR    = ~/.claude/references
```

---

## COMMAND: `ingest`

### Step 1 — Parse Input

Extract:
- `DATASET_PATH`: path to the input data file
- `PROJECT_NAME`: derive from dataset filename without extension
- `OUTPUT_DIR`: `{PROJECT_NAME}/` in the current working directory

### Step 2 — Load Memory (if project exists)

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/memory_read.py --project-dir "{OUTPUT_DIR}"
```

If memory exists, note `failed_transforms` to avoid repeating.

### Step 3 — Ingest Data

Spawn agent: `df-ingest`

```
Task: Ingest dataset for {PROJECT_NAME}
source: {DATASET_PATH}
output_dir: {OUTPUT_DIR}
```

If ingest fails, report error and list supported formats. Stop.

---

## COMMAND: `validate`

### Step 1 — Parse Input

Same as ingest, plus extract `TARGET_COL`.

### Step 2 — Run Validation Gate

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

---

## COMMAND: `profile`

### Step 1 — Run Profiler

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/data_profiler.py \
  --data "{OUTPUT_DIR}/data/raw/{filename}" \
  --output "{OUTPUT_DIR}/data/interim/profile.json" \
  --target "{TARGET_COL}"
```

Read the output JSON to get: column list, dtypes, problem_type detection.

### Step 2 — Auto-detect Problem Type

- **Classification**: target has <= 20 unique values OR is string/bool dtype
- **Regression**: target is float/int with > 20 unique values
- **Clustering**: no target column provided
- **Time Series**: datetime index detected AND target is numeric

### Step 3 — Write Config

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
  "dataforge_skill_version": "2.0.0"
}
```

---

## COMMAND: `features`

Full preprocessing pipeline. Runs all steps in sequence.

### Step 1 — Ingest (if not already done)

Check if `{OUTPUT_DIR}/data/raw/` has files. If not, run the **ingest** command above.

### Step 2 — Validate (GATE)

Run the **validate** command above. Stop on HARD STOP.

### Step 3 — Profile

Run the **profile** command above.

### Step 4 — Load Feature References

Load `~/.claude/references/feature-recipes.md` for transform decision tree.

### Step 5 — Feature Engineering (Parallel Column Transforms)

Read column list from `profile.json`. Read EDA summary if available (`eda_summary.json`).

For each column with recommended transforms, spawn one `df-feature-column` agent in parallel batches of <= 10.

**Single parallel batch message** (all agents launched simultaneously):
```
Spawn in parallel:
- Agent(df-feature-column): dataset_path={raw_path} column_name=col1 transforms=["median_imputation","standard_scaling"] output_dir={OUTPUT_DIR} target_column={TARGET_COL}
- Agent(df-feature-column): dataset_path={raw_path} column_name=col2 transforms=["mode_imputation","one_hot_encoding"] output_dir={OUTPUT_DIR} target_column={TARGET_COL}
... (up to 10 at once, then next batch)
```

### Step 5b — Expert Checkpoint: Preprocessing Review (Optional)

If running as part of a workflow (pipeline or analysis), the workflow handles
expert checkpoints. When running standalone (`/df-preprocess features`),
run the checkpoint here:

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/domain_detect.py \
  --data "{OUTPUT_DIR}/data/raw/{filename}" \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/domain.json"

~/.claude/dataforge/dfpython ~/.claude/scripts/expert_triage.py \
  --stage preprocessing \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --validation "{OUTPUT_DIR}/data/interim/validation_report.json" \
  --cache-dir "{OUTPUT_DIR}/data/interim/expert_cache" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/triage_preprocessing.json"
```

Based on `complexity_level`: skip / light (lead only) / full (all experts + lead).
If lead verdict is **block**: pause for user. Otherwise continue.

### Step 6 — Assemble Processed Dataset

Collect all agent results. Write `{OUTPUT_DIR}/data/processed/train.csv`.
Write `{OUTPUT_DIR}/src/feature_engineering.py` based on applied transforms.

### Step 7 — Update Memory

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/memory_write.py \
  --project-dir "{OUTPUT_DIR}" \
  --file decisions \
  --mode append_md \
  --data "## Preprocessing\n{summary_of_transforms}"
```

Log any `"status": "failure"` results to `memory/failed_transforms.json`.

---

## QUALITY GATES

Load `~/.claude/references/quality-gates.md` for full rules.

**Hard stops** (exit code 2 — never override without explicit user confirmation):
- Fewer than 50 rows after cleaning
- Target column not found in dataset
- Target leakage: any feature with correlation > 0.99 with target

**Warnings** (exit code 1 — report and continue):
- Class imbalance > 10:1 (suggest SMOTE, report class_weight option)
- Any column > 50% missing (report, use median/mode imputation)
- Duplicate rows > 5% (report count, deduplicate automatically)
- Constant columns detected (report names, drop automatically)
- High-cardinality ID-like columns (report names, drop automatically)

---

## PARALLEL EXECUTION RULES

- Feature column agents: batch <= 10 per parallel invocation
- After every parallel batch:
  - Collect all JSON results
  - Log any `"status": "failure"` results to `memory/failed_transforms.json`
  - Continue with partial results (never abort on one column failure)

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| Dataset file not found | Report path, list supported formats, stop |
| Unsupported file format | List supported types, stop |
| Validation HARD STOP | Report exact failure, do NOT proceed, ask user to fix |
| Feature transform failure | Log to memory, skip column, continue with others |
| Memory file corrupt | Warn user, reset from schema defaults, continue |
| Python script error | Show stderr, diagnose, suggest fix |
| Missing Python package | Show: `pip install -r requirements.txt` |
