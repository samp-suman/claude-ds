# dataforge-preprocess

Data ingestion, validation, profiling, and feature engineering. Handles everything from loading raw data to producing clean, transformed features ready for modeling.

## Usage

```
/dataforge-preprocess ingest <dataset>              # Load data into project data/raw/
/dataforge-preprocess validate <dataset> [target]   # Run quality gate checks
/dataforge-preprocess profile <dataset>             # Profile + auto-detect problem type
/dataforge-preprocess features <dataset> <target>   # Feature engineering (parallel per-column)
```

Or via the router:

```
/dataforge preprocess <dataset> <target>            # Runs all four steps in sequence
/dataforge validate <dataset>                       # Quality checks only
```

## What it does

1. **Ingest** — Loads CSV, TSV, JSON, JSONL, Parquet, Excel, SQLite, HTTP URLs, Pickle, or Kaggle slugs into `data/raw/`.
2. **Validate** — Checks minimum rows, target existence, target leakage, class imbalance, missing values, duplicates, constant columns, and ID-like columns. Exit code 2 = hard stop, 1 = warnings, 0 = pass.
3. **Profile** — Generates per-column statistics, detects problem type (binary/multiclass/regression/clustering), and computes target correlations.
4. **Features** — Applies per-column transforms in parallel (imputation, scaling, encoding, datetime extraction, outlier clipping) and assembles fitted sklearn Pipelines.

## Supported data formats

CSV, TSV, JSON, JSONL, Parquet, Excel (.xlsx/.xls), SQLite, SQLAlchemy URI, HTTP/HTTPS URL, Pickle, Kaggle dataset slug.
