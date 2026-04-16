---
name: dataforge-experiment
description: >
  Experiment tracking and monitoring skill for DataForge. View experiment history,
  compare runs, detect data/concept drift, and manage experiment memory. Triggers
  on: "experiment", "status", "compare models", "monitor", "drift", "experiment
  history", "what was tried".
user-invokable: true
argument-hint: "[status|compare|monitor|history] <project-dir>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Experiment Skill

> Experiment tracking, comparison, monitoring, and memory management.

## Commands

| Command | What it does |
|---------|-------------|
| `/dataforge-experiment status <project-dir>` | Print memory summary: experiments, decisions, best pipeline |
| `/dataforge-experiment compare <project-dir>` | Compare experiments across runs |
| `/dataforge-experiment monitor <project-dir> --new-data <path>` | Data/concept drift detection |
| `/dataforge-experiment history <project-dir>` | Full experiment timeline |

---

## COMMAND: `status`

Read all memory files and present a summary:

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/memory_read.py \
  --project-dir "{PROJECT_DIR}" \
  --file all
```

Present:
- **Best model**: name, metric, score
- **Total experiments**: count of runs
- **Last run**: timestamp
- **Key decisions**: from `memory/decisions.md`
- **Failed transforms**: what was tried and failed
- **Pipeline status**: which steps are complete

---

## COMMAND: `compare`

Read `memory/experiments.json` and present a comparison table:

```
Experiment Comparison for {PROJECT_NAME}

| Run ID | Timestamp  | Best Model | Score | Features | Notes |
|--------|-----------|------------|-------|----------|-------|
| run-1  | 2026-04-04 | lightgbm  | 0.923 | 11       | Initial |
| run-2  | 2026-04-05 | xgboost   | 0.931 | 14       | Added interaction features |
```

Highlight:
- Score improvements/regressions between runs
- What changed (features, hyperparams, preprocessing)
- Recommendations for next experiment

---

## COMMAND: `monitor`

Detect data drift and concept drift between training data and new data.

### Step 1 — Load Reference Data

Read `{PROJECT_DIR}/dataforge.config.json` for training data reference.
Load training distribution from `{PROJECT_DIR}/data/processed/train.csv`.

### Step 2 — Spawn Monitor Agent

```
Agent(df-monitor):
  output_dir: {PROJECT_DIR}
  new_data_path: {NEW_DATA_PATH}
  target_column: {TARGET_COL}
```

### Step 3 — Present Results

Report:
- Per-feature drift scores (KS statistic, PSI)
- Features that drifted significantly
- Concept drift assessment (if labels available)
- Recommendation: `stable` | `monitor` | `retrain`

If `recommendation == "retrain"`:
- Suggest: `/dataforge-modeling train {new_data} {target}`

---

## COMMAND: `history`

Read `memory/experiments.json` and present the full timeline:

- All runs chronologically
- Per-run details: models tried, best score, features used
- Progression chart: best score over time
- Decision log from `memory/decisions.md`

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| No memory directory | Report that no experiments have been run yet |
| Corrupt memory file | Warn user, show what's readable |
| New data format mismatch | Report schema differences vs training data |
| Monitor fails | Report error, suggest checking data format |
