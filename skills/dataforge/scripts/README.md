# DataForge Scripts — CLI Reference

All scripts use a narrow CLI interface and print a JSON result as the last line of stdout.

**Exit codes:** `0` = success, `1` = warning/partial, `2` = fatal error

---

## ingest.py — Data Loader

Loads any supported data format into `data/raw/`.

```bash
python ingest.py \
  --source <path_or_uri> \
  --output-dir <project_dir> \
  [--table <table_name>]      # For multi-table databases
```

**Supported sources:**
- File paths: `.csv`, `.tsv`, `.json`, `.jsonl`, `.parquet`, `.xlsx`, `.xls`, `.db`, `.sqlite`, `.pkl`
- DB URIs: `sqlite:///path/to/db.sqlite?table=users`, `postgresql://user:pass@host/db`
- URLs: `https://example.com/data.csv`

**Outputs:** `data/raw/{filename}`, `data/interim/profile_raw.json`

---

## profile.py — Dataset Profiler

Computes per-column stats and detects problem type.

```bash
python profile.py \
  --data <dataset_path> \
  --output <profile.json_path> \
  [--target <target_column>]
```

**Output JSON fields:** `n_rows`, `n_cols`, `columns`, `problem_type`, `column_profiles`, `target_correlations`, `class_balance`

**Problem type detection:**
- `binary_classification` — target has ≤ 2 unique values or is bool
- `multiclass_classification` — target has 3–20 unique values or is string
- `regression` — target is float/int with > 20 unique values
- `clustering` — no target column provided
- `time_series` — DatetimeIndex + numeric target

---

## validate.py — Quality Gate

Runs 9 validation checks. Exit code 2 = HARD STOP (pipeline must halt).

```bash
python validate.py \
  --data <dataset_path> \
  --target <target_column> \
  --output-dir <project_dir>
```

**Checks:** min_samples (< 50 → HARD STOP), target_exists, target_variance, target_leakage (≥ 0.99 corr → HARD STOP), class_imbalance (> 10:1 → WARNING), high_missing (> 50% → WARNING), duplicate_rows (> 5% → WARNING), constant_columns, id_like_columns

**Outputs:** `data/interim/validation_report.json`, `data/interim/.validation_passed` (sentinel, exit 0/1 only)

---

## eda.py — EDA Script

Per-column analysis or global overview.

```bash
# Per-column mode
python eda.py \
  --data <dataset_path> \
  --column <col_name> \
  --output <output_dir> \
  --mode column

# Global mode (heatmap + target distribution + missing matrix)
python eda.py \
  --data <dataset_path> \
  --output <output_dir> \
  --mode global \
  [--target <target_column>]
```

**Per-column outputs:** `reports/eda/{col}_stats.json`, `reports/eda/{col}_plot.png`
**Global outputs:** `reports/eda/correlation_heatmap.png`, `reports/eda/target_distribution.png`, `reports/eda/missing_matrix.png`, `reports/eda/global_stats.json`

---

## features.py — Feature Engineering

Applies transforms to a single column.

```bash
python features.py \
  --data <dataset_path> \
  --column <col_name> \
  --transforms '["median_imputation", "log_transform", "standard_scaling"]' \
  --output-dir <project_dir> \
  [--target <target_column>]
```

**Available transforms:**
`median_imputation`, `mode_imputation`, `log_transform`, `yeo_johnson_transform`,
`standard_scaling`, `clip_outliers`, `one_hot_encoding`, `label_encoding`,
`target_encoding`, `extract_year`, `extract_month`, `extract_dayofweek`,
`consider_dropping`, `drop`

**Output:** Appends to `data/interim/feature_transforms.json`

---

## train.py — Model Trainer

Trains one model with 5-fold CV. Called in parallel by multiple agents.

```bash
python train.py \
  --model <model_name> \
  --data <processed_csv> \
  --target <target_column> \
  --problem <problem_type> \
  --output-dir <project_dir> \
  [--hyperparams '{"n_estimators": 300}'] \
  [--test-size 0.2]
```

**Classification models:** `xgboost`, `lightgbm`, `randomforest`, `logistic`, `catboost`, `svm_rbf`
**Regression models:** `xgboost`, `lightgbm`, `randomforest`, `linear`, `ridge`, `lasso`, `catboost`
**Clustering models:** `kmeans`, `dbscan`, `hierarchical`

**Outputs:** `src/models/{model}.pkl`, `src/models/{model}_metrics.json`, `src/models/{model}_cv_results.json`

---

## evaluate.py — Model Ranker

Reads all `*_metrics.json` files and ranks by primary metric.

```bash
python evaluate.py \
  --output-dir <project_dir> \
  --problem <problem_type>
```

**Primary metrics:** `roc_auc` (binary), `f1_weighted` (multiclass), `r2` (regression), `silhouette_score` (clustering)

**Outputs:** `src/models/leaderboard.json`, `reports/model_comparison.png`

---

## interpret.py — SHAP Interpretability

Generates SHAP explanations for the best model.

```bash
python interpret.py \
  --model-path <pkl_path> \
  --data <processed_csv> \
  --target <target_column> \
  --problem <problem_type> \
  --output-dir <project_dir>
```

**Outputs:** `reports/shap_summary.png`, `reports/shap_bar.png`, `reports/feature_importance.png`, `reports/shap_values.json`

**Note:** Samples 500 rows for SHAP (performance). Falls back to native feature importance if SHAP fails.

---

## visualize.py — Visualization Suite

Generates problem-type-appropriate evaluation plots.

```bash
python visualize.py \
  --output-dir <project_dir> \
  --problem <problem_type> \
  [--model-path <pkl_path>] \
  [--data <processed_csv>] \
  [--target <target_column>]
```

**Classification outputs:** `reports/confusion_matrix.png`, `reports/roc_curve.png`
**Regression outputs:** `reports/residual_plot.png` (includes prediction vs actual)
**All types (if ≤ 8 features):** `reports/pairplot.png`

---

## deploy_detect.py — Deployment Target Selector

Heuristically selects Streamlit / FastAPI / Flask.

```bash
python deploy_detect.py \
  --problem-type <type> \
  [--production] \
  [--model-size-mb <size>] \
  --output <deploy_config.json>
```

**Decision rules:** `--production` → FastAPI, time_series → Streamlit, model > 500MB → FastAPI, default → Streamlit

---

## report.py — Report Assembler

Assembles all artifacts into a single-file HTML report.

```bash
python report.py \
  --output-dir <project_dir> \
  --project-name <name> \
  --problem-type <type> \
  --best-model <model_name> \
  --best-metric <metric_name> \
  --best-score <float> \
  [--deploy-target streamlit]
```

**Outputs:** `reports/final_report.html`, `reports/final_report.pdf` (if WeasyPrint installed)

---

## memory_read.py — Memory Reader

Reads memory files and returns a consolidated JSON.

```bash
python memory_read.py \
  --project-dir <project_dir> \
  [--file experiments|decisions|failed_transforms|best_pipelines|all]
```

---

## memory_write.py — Memory Writer (Concurrent-Safe)

Writes to memory files with file locking.

```bash
python memory_write.py \
  --project-dir <project_dir> \
  --file <experiments|decisions|failed_transforms|best_pipelines> \
  --mode <append|update|merge|reset|append_md> \
  --data '<json_string_or_text>'
```

**Modes:**
- `append` — add item to primary array in JSON file
- `update` — merge dict into top-level JSON
- `merge` — deep recursive merge
- `reset` — overwrite entire file
- `append_md` — append text to a Markdown file
