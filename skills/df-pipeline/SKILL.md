---
name: df-pipeline
description: >
  Full end-to-end pipeline workflow for DataForge. Orchestrates all skills in
  sequence: preprocess, EDA, modeling, deployment, and report. This is the
  main workflow invoked by /dataforge run. Triggers on: "run pipeline",
  "full pipeline", "build pipeline", "end to end", "ml project".
user-invokable: true
argument-hint: "<dataset-path> <target-column> [--production]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Full Pipeline Workflow

> End-to-end: ingest -> validate -> profile -> EDA -> features -> train -> evaluate
> -> interpret -> visualize -> deploy -> report.

## Usage

```
/df-pipeline <dataset> <target> [--production]
/dataforge run <dataset> <target> [--production]
```

---

## ORCHESTRATION

This workflow delegates to atomic skills in sequence. Each step uses the
outputs from previous steps. The workflow handles inter-skill coordination.

### Step 0 — Parse Input + Role Detection

**Parse user input:**
- `DATASET_PATH`: path to the input data file
- `TARGET_COL`: target column name (REQUIRED for pipeline)
- `USER_GOAL`: user's stated goal/intent (e.g., "predict churn for our SaaS product")
- `PROJECT_NAME`: derive from dataset filename without extension
- `OUTPUT_DIR`: `{PROJECT_NAME}/` in the current working directory
- `PRODUCTION_FLAG`: true if user said "production" or "api" or "--production"

If `DATASET_PATH` or `TARGET_COL` is missing: ask the user. If `USER_GOAL` unclear, ask for clarification.

**Spawn role detection agent (in parallel with downstream work):**
```
Agent(df-expert-role): 
  user_goal={USER_GOAL}
  output_dir={OUTPUT_DIR}
  problem_type=(to be detected)
```
This agent infers the user's role (data_analyst | ml_engineer | product_ds | researcher | analytics_engineer)
and returns role_context.json. This is used at each downstream stage to adjust output style and technique focus.

### Step 0b — Create DS Design Document (PROJECT_PLAN.md)

Create `{OUTPUT_DIR}/PROJECT_PLAN.md` using the template from
`~/.claude/references/project-plan-template.md`. Fill in what's known so far:
- `{PROJECT_NAME}`, `{DATASET_PATH}`, `{TARGET_COL}`, `{TIMESTAMP}`
- Set `{STATUS}` to "In Progress"
- Set all stage statuses to "Pending"

**After EVERY subsequent stage completes**, update `PROJECT_PLAN.md`:
- Mark the stage status as "Done" with duration and any notes
- Fill in newly available data (row count after ingest, problem type after profile,
  model results after training, etc.)
- If a stage fails or triggers a hard stop, mark it as "Failed" with the reason

At pipeline end, set `{STATUS}` to "Complete" and fill in the Results section
(best model, leaderboard, SHAP features, quality gates, artifacts).

This document serves as the **living project plan** — a DS Design Document that
tracks the approach, decisions, and outcomes for the entire project.

### Step 1 — Load Memory (if project exists)

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/memory_read.py --project-dir "{OUTPUT_DIR}"
```

If memory exists:
- Check `failed_transforms` to avoid repeating bad transforms
- Check `best_pipelines` to seed hyperparameter search
- Check `experiments` to skip identical configurations

### Step 2 — Preprocessing (Ingest + Validate + Profile + Features)

**Ingest:**
```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/ingest.py \
  --source "{DATASET_PATH}" \
  --output-dir "{OUTPUT_DIR}"
```

If ingest fails, report error and stop.

**Validate (GATE):**
Spawn agent: `df-validate`
```
Task: Validate dataset for {PROJECT_NAME}
dataset_path: {OUTPUT_DIR}/data/raw/{filename}
target_column: {TARGET_COL}
output_dir: {OUTPUT_DIR}
```

**CRITICAL**: If exit_code 2 (HARD STOP) — report failure and STOP.

**Profile:**
```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/data_profiler.py \
  --data "{OUTPUT_DIR}/data/raw/{filename}" \
  --output "{OUTPUT_DIR}/data/interim/profile.json" \
  --target "{TARGET_COL}"
```

Auto-detect problem type. Write `dataforge.config.json`.

### Step 2b — Expert Checkpoint: Domain + Role Context

**Claude-native domain and role reasoning (replace script-based detection):**

Read profile.json and raw data sample (first 1000 rows). Claude reasons:

```
DOMAIN DETECTION (infer from column names, value patterns, data semantics):
  - Check for domain signals: finance (account, balance, fraud), healthcare (diagnosis, lab, vital),
    retail (price, inventory, SKU), marketing (customer, purchase, segment), manufacturing (sensor, equipment, maintenance),
    logistics (demand, lead_time, delivery), social (user, post, engagement)
  → Confident domain classification with rationale
  → OR "general" if no strong domain signals

ROLE CONTEXT (from Step 0 role_context.json):
  - Read role_context.json generated in Step 0
  → Role: data_analyst | ml_engineer | product_ds | researcher | analytics_engineer
  → Technique adjustments based on role

OUTPUT: domain_context.json with:
{
  "detected_domain": "finance | healthcare | retail | marketing | manufacturing | logistics | social | general",
  "domain_confidence": "high | medium | low",
  "domain_reasoning": "<one sentence explaining signals>",
  "detected_role": "<from role_context.json>",
  "combined_context": "<how domain + role interact>",
  "technique_priorities": "<priority adjustments from domain + role>",
  "expert_agents_to_spawn": ["df-expert-finance", "df-expert-lead", ...]
}
```

Write domain_context.json to `{OUTPUT_DIR}/data/interim/expert_cache/domain_context.json`.

**Expert triage (complexity routing):**

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/expert_triage.py \
  --stage preprocessing \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --domain-context "{OUTPUT_DIR}/data/interim/expert_cache/domain_context.json" \
  --cache-dir "{OUTPUT_DIR}/data/interim/expert_cache" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/triage_preprocessing.json" \
  {--production if PRODUCTION_FLAG}
```

Read `triage_preprocessing.json`. Based on `complexity_level`:

- **skip**: Log "expert review skipped (low complexity)", continue.
- **light**: Spawn only `df-expert-lead` with `complexity_level=light` to do a quick review.
- **full**: Spawn methodology + domain experts in parallel, then lead:
  ```
  Spawn in parallel:
  - Agent(df-expert-datascientist): stage=preprocessing output_dir={OUTPUT_DIR}
  - Agent(df-expert-statistician): stage=preprocessing output_dir={OUTPUT_DIR}
  - Agent(df-expert-{DOMAIN}): stage=preprocessing output_dir={OUTPUT_DIR}
    (only if DOMAIN != "general"; e.g., df-expert-finance, df-expert-healthcare, etc.)
  - Agent(df-expert-role): validate role context if domain conflicts with stated goal
  ```
  Collect findings. Spawn `df-expert-lead` with all findings + domain_context + role_context.

If lead verdict is **block**: pause pipeline, present blocks to user.
If lead verdict is **flag** or **approve**: apply auto-corrections, log advisories, continue.

### Step 3 — Exploratory Data Analysis

Read column list from `profile.json`.

Spawn per-column EDA agents in parallel (batches of <= 10):
```
Spawn in parallel:
- Agent(df-eda-column): dataset_path={raw_path} column_name=col1 output_dir={OUTPUT_DIR} mode=column
- Agent(df-eda-column): dataset_path={raw_path} column_name=col2 output_dir={OUTPUT_DIR} mode=column
...
```

Also spawn global EDA in same batch:
```
Agent(df-eda-global): dataset_path={raw_path} target={TARGET_COL} output_dir={OUTPUT_DIR}
```

Merge results into `eda_summary.json`. Write `src/data_pipeline.py`.

### Step 3b — Expert Checkpoint: EDA Review

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/expert_triage.py \
  --stage eda \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --eda-summary "{OUTPUT_DIR}/reports/eda/eda_summary.json" \
  --cache-dir "{OUTPUT_DIR}/data/interim/expert_cache" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/triage_eda.json"
```

Same expert flow as Step 2b: skip / light / full based on `complexity_level`.

For **full**: use `SendMessage` to continue previously spawned methodology and
domain experts (they already have preprocessing context). Spawn lead fresh.

If lead verdict is **block**: pause for user. Otherwise continue.

### Step 4 — Feature Engineering

Read EDA summary. For each column with `recommended_transforms`, spawn
`df-feature-column` agents in parallel (batches of <= 10).

Collect results. Write `data/processed/train.csv` and `src/feature_engineering.py`.

### Step 5 — Model Training (All Models in Parallel)

Load `~/.claude/references/model-catalog.md` to select models for `{PROBLEM_TYPE}`.

Spawn ALL model agents simultaneously in one response:
```
Spawn in parallel:
- Agent(df-train-model): model=xgboost dataset_path=data/processed/train.csv target={TARGET_COL} problem_type={PROBLEM_TYPE} output_dir={OUTPUT_DIR}
- Agent(df-train-model): model=lightgbm ...
- Agent(df-train-model): model=randomforest ...
- Agent(df-train-model): model=logistic ...
```

Wait for ALL to complete. Collect JSON results.

### Step 6 — Evaluate

Spawn agent: `df-evaluate`
```
Task: Evaluate and rank models for {PROJECT_NAME}
model_results: {JSON array of training results}
problem_type: {PROBLEM_TYPE}
output_dir: {OUTPUT_DIR}
```

Write `src/model_training.py` and `src/evaluation.py`.

### Step 6b — Expert Checkpoint: Modeling Review

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/expert_triage.py \
  --stage modeling \
  --leaderboard "{OUTPUT_DIR}/src/models/leaderboard.json" \
  --profile "{OUTPUT_DIR}/data/interim/profile.json" \
  --cache-dir "{OUTPUT_DIR}/data/interim/expert_cache" \
  --output "{OUTPUT_DIR}/data/interim/expert_cache/triage_modeling.json"
```

Same expert flow as Step 2b: skip / light / full based on `complexity_level`.

For **full**: use `SendMessage` to continue previously spawned experts. They now
have full pipeline context (preprocessing + EDA + modeling findings).

If lead verdict is **block**: pause for user. Otherwise continue.

### Step 7 — Interpret + Visualize (Parallel)

Spawn BOTH simultaneously:
```
Spawn in parallel:
- Agent(df-interpret): best_model={best_model} output_dir={OUTPUT_DIR} problem_type={PROBLEM_TYPE} dataset_path=data/processed/train.csv target_column={TARGET_COL}
- Agent(df-visualize): output_dir={OUTPUT_DIR} problem_type={PROBLEM_TYPE} best_model={best_model} dataset_path=data/processed/train.csv target_column={TARGET_COL}
```

Write `src/inference.py`.

### Step 8 — Deploy

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/deploy_detect.py \
  --problem-type "{PROBLEM_TYPE}" \
  --output "{OUTPUT_DIR}/data/interim/deploy_config.json"
```

Add `--production` if `PRODUCTION_FLAG` is set.

Spawn agent: `df-deploy`
```
Task: Generate deployment app for {PROJECT_NAME}
deploy_config: {deploy_config.json contents}
output_dir: {OUTPUT_DIR}
best_model: {best_model}
target_column: {TARGET_COL}
project_name: {PROJECT_NAME}
```

### Step 9 — Report

Spawn agent: `df-report`
```
Task: Generate final report for {PROJECT_NAME}
output_dir: {OUTPUT_DIR}
problem_type: {PROBLEM_TYPE}
best_model: {best_model}
best_metric: {primary_metric}
best_score: {best_score}
```

### Step 10 — Write CLAUDE.md + Final Memory

Write `{OUTPUT_DIR}/CLAUDE.md`:

```markdown
# DataForge Project: {PROJECT_NAME}

This is a DataForge-managed Data Science project.

## Quick Context
- Problem type: {PROBLEM_TYPE}
- Target column: {TARGET_COL}
- Best model: {BEST_MODEL} ({BEST_METRIC_NAME}: {BEST_METRIC_VALUE})
- Deployment: {DEPLOY_TARGET} -- run `make serve`
- Last run: {TIMESTAMP}

## Working in This Project
1. Read `dataforge.config.json` for project configuration
2. Read `memory/decisions.md` for why choices were made
3. Run `/df-experiment status .` to see full experiment history
4. Run `/dataforge run . {TARGET_COL}` to retrain

## File Conventions
- `data/raw/` -- original data, never modify
- `src/models/` -- trained model artifacts (.pkl) + metrics JSON
- `src/inference.py` -- entry point for predictions on new data
- `reports/` -- all plots and generated reports
- `memory/` -- experiment history, decisions, failed transforms
```

Update memory:
```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/memory_write.py \
  --project-dir "{OUTPUT_DIR}" \
  --file decisions \
  --mode append_md \
  --data "## Run Complete\n{summary}"
```

### Step 11 — Print Summary

```
DataForge complete for {PROJECT_NAME}

Problem type:  {PROBLEM_TYPE}
Best model:    {best_model} ({metric_name}: {metric_value})
Deployment:    {deploy_target} -> {OUTPUT_DIR}/app/app.py
Report:        {OUTPUT_DIR}/reports/final_report.html

Run:  cd {OUTPUT_DIR} && make serve
Test: cd {OUTPUT_DIR} && make test
```

---

## RESUME MODE

When invoked with `/dataforge resume <project-dir>`:

1. Read `{OUTPUT_DIR}/dataforge.config.json` to restore project state
2. Check what exists to determine last completed step:

| Checkpoint | Step to resume from |
|------------|-------------------|
| `data/raw/` has files | Skip ingest |
| `data/interim/validation_report.json` exists | Skip validate |
| `data/interim/profile.json` exists | Skip profile |
| `data/interim/eda_summary.json` exists | Skip EDA |
| `data/processed/train.csv` exists | Skip features |
| `src/models/` has .pkl files | Skip training |
| `src/models/leaderboard.json` exists | Skip evaluate |
| `reports/shap_summary.png` exists | Skip interpret |
| `app/app.py` exists | Skip deploy |
| `reports/final_report.html` exists | Skip report |

3. Resume from the next incomplete step.

---

## QUALITY GATES

Load `~/.claude/references/quality-gates.md` for full rules.

**Hard stops** (exit code 2 — never override without explicit user confirmation):
- Fewer than 50 rows after cleaning
- Target column not found
- Target leakage (correlation >= 0.99)

---

## PARALLEL EXECUTION RULES

1. Column EDA and feature agents: batch <= 10 per parallel invocation
2. Model training: always one single parallel batch (all models at once)
3. Interpret + Visualize: always run in parallel
4. Ingest + Validate: sequential (validate gates everything after it)
5. Profile -> EDA -> Features -> Train: sequential stages, parallel within each stage

After every parallel batch:
- Collect all JSON results
- Log any `"status": "failure"` results to `memory/failed_transforms.json`
- Continue with partial results
- Validate merged result schema before proceeding

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| Dataset not found | Report path, list formats, stop |
| Validation HARD STOP | Report failure, do NOT proceed |
| Model training failure | Log, skip model, continue with others |
| Agent timeout | Report stage, offer `/dataforge resume` |
| Missing package | Show: `pip install -r requirements.txt` |
