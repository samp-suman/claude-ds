---
name: df-report
description: >
  Report generation skill for DataForge. Assembles all generated artifacts (EDA
  plots, model leaderboard, SHAP charts, evaluation plots) into a polished
  HTML report with embedded images. Optionally converts to PDF. Triggers on:
  "report", "generate report", "PDF", "HTML report", "final report".
user-invokable: true
argument-hint: "[eda] <project-dir>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Report Skill

> Generate HTML/PDF reports from existing DataForge project results.

## Commands

| Command | What it does |
|---------|-------------|
| `/df-report <project-dir>` | Full report: EDA + models + SHAP + evaluation |
| `/df-report eda <project-dir>` | EDA-only report |

---

## COMMAND: Full Report

### Step 1 — Verify Artifacts

Check `{PROJECT_DIR}` for:
- `data/interim/eda_summary.json` — EDA results
- `src/models/leaderboard.json` — model rankings
- `reports/` — plots (shap, confusion matrix, etc.)

### Step 2 — Read Config

Read `{PROJECT_DIR}/dataforge.config.json` for project metadata.
Read `{PROJECT_DIR}/src/models/leaderboard.json` for best model.

### Step 3 — Generate Report

Spawn agent: `df-report`

```
Task: Generate final report for {PROJECT_NAME}
output_dir: {PROJECT_DIR}
problem_type: {PROBLEM_TYPE}
best_model: {best_model_name}
best_metric: {primary_metric}
best_score: {best_score}
```

### Step 4 — Print Summary

```
Report generated for {PROJECT_NAME}

HTML:  {PROJECT_DIR}/reports/final_report.html
PDF:   {PROJECT_DIR}/reports/final_report.pdf (if WeasyPrint installed)
```

---

## COMMAND: EDA Report

Same as full report but:
- Only includes EDA sections (no model results)
- Does not require trained models
- Only requires `eda_summary.json` and `reports/eda/` plots

Pass `--eda-only` context to the `df-report` agent.

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| No EDA results | Tell user to run EDA first |
| No model results | For full report, tell user to run modeling first. For EDA report, proceed without. |
| WeasyPrint missing | Generate HTML only, note PDF requires `pip install weasyprint` |
| Plot files missing | Generate report with available plots, note missing ones |
