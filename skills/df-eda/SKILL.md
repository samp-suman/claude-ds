---
name: df-eda
description: >
  Exploratory Data Analysis skill for DataForge. Performs parallel per-column
  statistical analysis, generates distribution plots, correlation heatmaps,
  target analysis, and domain-specific feature studies. Can be used standalone
  or as part of a workflow. Triggers on: "EDA", "exploratory", "analyze data",
  "data analysis", "distribution", "correlation", "feature study", "statistics".
user-invokable: true
argument-hint: "[column|global|summary] <dataset-path> [target-column]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — EDA Skill

> Exploratory Data Analysis: statistical profiling, distribution plots, correlation
> analysis, feature studies, and domain-specific insights.

## Commands

| Command | What it does |
|---------|-------------|
| `/df-eda <dataset>` | Full EDA: per-column parallel + global analysis |
| `/df-eda column <dataset> <col>` | Single-column deep dive |
| `/df-eda global <dataset> [target]` | Correlation heatmap, target distribution, missing matrix |
| `/df-eda summary <project-dir>` | Print EDA summary from existing results |

---

## Shared Constants

```
SCRIPTS_DIR = ~/.claude/scripts
REFS_DIR    = ~/.claude/references
```

---

## COMMAND: Full EDA (`/df-eda <dataset>`)

### Step 1 — Ensure Data is Available

Check if `{OUTPUT_DIR}/data/raw/` has files. If not:
```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/ingest.py \
  --source "{DATASET_PATH}" \
  --output-dir "{OUTPUT_DIR}"
```

### Step 2 — Profile Dataset

Check if `{OUTPUT_DIR}/data/interim/profile.json` exists. If not:
```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/data_profiler.py \
  --data "{OUTPUT_DIR}/data/raw/{filename}" \
  --output "{OUTPUT_DIR}/data/interim/profile.json"
```

Read the profile JSON to get column list and dtypes.

### Step 3 — Parallel Column EDA

Read column list from `profile.json`. Spawn one `df-eda-column` agent **per column**, in parallel batches of <= 10.

**Single parallel batch message** (all agents launched simultaneously):
```
Spawn in parallel:
- Agent(df-eda-column): dataset_path={raw_path} column_name=col1 output_dir={OUTPUT_DIR} mode=column
- Agent(df-eda-column): dataset_path={raw_path} column_name=col2 output_dir={OUTPUT_DIR} mode=column
... (up to 10 at once, then next batch)
```

Each column agent produces:
- `reports/eda/{column}_stats.json` — statistical summary
- `reports/eda/{column}_plot.png` — distribution visualization
- `recommended_transforms` — suggested preprocessing steps
- `flags` — quality issues (high_missing, skewed, outliers, id_like)

### Step 4 — Global Analysis (Parallel with Column EDA)

Spawn `df-eda-column` with `--mode=global` in the same parallel batch as the column agents:

```
Agent(df-eda-column): dataset_path={raw_path} mode=global target={TARGET_COL} output_dir={OUTPUT_DIR}
```

Global analysis produces:
- `reports/eda/correlation_heatmap.png` — feature correlations
- `reports/eda/target_distribution.png` — target variable distribution
- `reports/eda/missing_matrix.png` — missing value patterns
- `reports/eda/global_stats.json` — dataset-level statistics

### Step 5 — Merge Results

Collect all JSON results from column agents. Merge into `{OUTPUT_DIR}/data/interim/eda_summary.json`:

```json
{
  "n_columns_analyzed": 12,
  "columns": {
    "age": {
      "col_type": "numeric",
      "null_pct": 19.9,
      "n_unique": 88,
      "recommended_transforms": ["median_imputation", "standard_scaling"],
      "flags": ["missing"]
    }
  },
  "global": {
    "top_correlations": [...],
    "target_type": "binary",
    "n_missing_columns": 3,
    "n_high_cardinality": 1
  }
}
```

### Step 6 — Generate Data Pipeline

Write `{OUTPUT_DIR}/src/data_pipeline.py` based on EDA findings — a Python script that applies the recommended transforms when given raw data.

### Step 7 — Print Summary

Present findings to the user:
- Dataset shape and problem type
- Per-column findings table (type, missing%, unique, flags)
- Top correlations with target
- Recommended preprocessing actions
- Domain-specific observations

---

## COMMAND: Single Column (`/df-eda column <dataset> <col>`)

Spawn one `df-eda-column` agent for the specified column:

```
Agent(df-eda-column): dataset_path={DATASET_PATH} column_name={col} output_dir={OUTPUT_DIR} mode=column
```

Present a detailed analysis:
- Distribution type (normal, skewed, bimodal, uniform)
- Key statistics (mean, median, std, quartiles, skewness, kurtosis)
- Missing value analysis
- Outlier detection and impact
- Recommended transforms with reasoning
- If target exists: relationship with target (correlation, ANOVA, chi-square)

---

## COMMAND: Global Analysis (`/df-eda global <dataset> [target]`)

Spawn `df-eda-column` with `--mode=global`:

```
Agent(df-eda-column): dataset_path={DATASET_PATH} mode=global target={TARGET_COL} output_dir={OUTPUT_DIR}
```

Present:
- Correlation heatmap interpretation
- Top feature-target correlations
- Multicollinearity warnings (features correlated > 0.8 with each other)
- Missing value patterns
- Target distribution and balance

---

## COMMAND: Summary (`/df-eda summary <project-dir>`)

Read `{project-dir}/data/interim/eda_summary.json` and present a formatted summary.
No agents spawned — just reads and formats existing results.

---

## DOMAIN-SPECIFIC ANALYSIS

After completing the standard EDA, analyze the dataset with domain awareness:

### For Financial/Business Data
- Revenue/cost ratio analysis
- Time-based trends if date columns present
- Customer segmentation signals

### For Healthcare/Medical Data
- Feature interaction analysis (BMI = weight/height^2, etc.)
- Outlier clinical significance (not just statistical)
- Missing data patterns (MCAR/MAR/MNAR assessment)

### For E-commerce/Retail Data
- Purchase frequency distributions
- Price elasticity signals
- Category concentration analysis

### For General Tabular Data
- Feature interaction candidates (ratios, differences, products)
- Polynomial feature candidates (non-linear relationships)
- Binning candidates for continuous features

Record domain observations in the EDA summary under a `"domain_insights"` key.

---

## PARALLEL EXECUTION RULES

1. Column EDA agents: batch <= 10 per parallel invocation
2. Global analysis runs in parallel WITH column agents (same batch)
3. After every parallel batch:
   - Collect all JSON results
   - Log any `"status": "failure"` results
   - Continue with partial results
   - Validate merged result schema before proceeding

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| Dataset not found | Report path, suggest ingest first |
| Column not found | List available columns, ask user to pick |
| Plot generation fails | Log warning, continue without plot |
| Profile missing | Run profiler automatically |
| Script error | Show stderr, diagnose |
