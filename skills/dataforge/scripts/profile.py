#!/usr/bin/env python3
"""
DataForge — Dataset Profiler

Reads the raw dataset and produces a rich profile JSON used by the orchestrator
to plan EDA, feature engineering, and model selection.

Usage:
    python profile.py --data <path> --output <profile.json>

Exit codes:
    0  Success
    2  Fatal error
"""
import argparse
import json
import sys
from pathlib import Path


def load_df(path: str):
    import pandas as pd
    p = path.lower()
    if p.endswith(".parquet") or p.endswith(".pq"):
        return pd.read_parquet(path)
    if p.endswith(".csv"):
        return pd.read_csv(path)
    if p.endswith(".json"):
        return pd.read_json(path)
    if p.endswith(".xlsx") or p.endswith(".xls"):
        return pd.read_excel(path)
    # fallback
    return pd.read_csv(path)


def detect_problem_type(df, target_col: str) -> str:
    """Detect the ML problem type from target column characteristics."""
    if not target_col or target_col not in df.columns:
        return "clustering"
    col = df[target_col]
    if str(col.dtype) in ("bool", "boolean"):
        return "binary_classification"
    if str(col.dtype) == "object" or col.nunique() <= 20:
        return "binary_classification" if col.nunique() == 2 else "multiclass_classification"
    # Check for datetime index → time series
    datetime_index = isinstance(df.index, __import__("pandas").DatetimeIndex)
    if datetime_index:
        return "time_series"
    return "regression"


def profile_column(series) -> dict:
    """Compute per-column statistics."""
    import numpy as np
    import pandas as pd

    dtype_str = str(series.dtype)
    n = len(series)
    n_null = int(series.isnull().sum())
    null_pct = round(n_null / n * 100, 2) if n > 0 else 0.0
    n_unique = int(series.nunique())
    cardinality = round(n_unique / n, 4) if n > 0 else 0.0

    result = {
        "dtype": dtype_str,
        "n_null": n_null,
        "null_pct": null_pct,
        "n_unique": n_unique,
        "cardinality": cardinality,
    }

    if dtype_str in ("object", "category", "string"):
        result["col_type"] = "categorical"
        mode_val = series.mode()
        result["mode"] = str(mode_val.iloc[0]) if len(mode_val) > 0 else None
        result["top_values"] = series.value_counts().head(10).to_dict()

    elif "datetime" in dtype_str:
        result["col_type"] = "datetime"
        result["min"] = str(series.min())
        result["max"] = str(series.max())

    elif "bool" in dtype_str:
        result["col_type"] = "boolean"
        result["true_pct"] = round(series.sum() / n * 100, 2) if n > 0 else 0.0

    else:
        result["col_type"] = "numeric"
        described = series.describe()
        result["mean"] = round(float(described.get("mean", 0)), 4)
        result["std"] = round(float(described.get("std", 0)), 4)
        result["min"] = round(float(described.get("min", 0)), 4)
        result["p25"] = round(float(described.get("25%", 0)), 4)
        result["median"] = round(float(described.get("50%", 0)), 4)
        result["p75"] = round(float(described.get("75%", 0)), 4)
        result["max"] = round(float(described.get("max", 0)), 4)
        result["skewness"] = round(float(series.skew()), 4) if n > 2 else 0.0

        # Outlier detection via IQR
        q1 = described.get("25%", 0)
        q3 = described.get("75%", 0)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        n_outliers = int(((series < lower) | (series > upper)).sum())
        result["n_outliers"] = n_outliers
        result["outlier_pct"] = round(n_outliers / n * 100, 2) if n > 0 else 0.0

    return result


def compute_correlations(df, target_col: str) -> dict:
    """Compute numeric correlations with target column."""
    import numpy as np
    numeric_df = df.select_dtypes(include="number")
    if target_col not in numeric_df.columns or len(numeric_df.columns) < 2:
        return {}
    corr = numeric_df.corr()[target_col].drop(target_col, errors="ignore")
    return {col: round(float(val), 4) for col, val in corr.items() if abs(val) > 0.05}


def main():
    parser = argparse.ArgumentParser(description="DataForge dataset profiler")
    parser.add_argument("--data", required=True, help="Path to dataset file")
    parser.add_argument("--output", required=True, help="Output profile JSON path")
    parser.add_argument("--target", default=None, help="Target column name")
    args = parser.parse_args()

    try:
        df = load_df(args.data)
    except Exception as e:
        print(f"ERROR: Cannot load dataset: {e}", file=sys.stderr)
        sys.exit(2)

    target_col = args.target

    # Per-column profiles
    column_profiles = {}
    for col in df.columns:
        try:
            column_profiles[col] = profile_column(df[col])
        except Exception as e:
            column_profiles[col] = {"error": str(e)}

    # Target correlations
    correlations = {}
    if target_col and target_col in df.columns:
        try:
            correlations = compute_correlations(df, target_col)
        except Exception:
            pass

    # Class balance (for classification)
    class_balance = {}
    if target_col and target_col in df.columns:
        vc = df[target_col].value_counts(normalize=True).round(4)
        class_balance = {str(k): float(v) for k, v in vc.items()}

    problem_type = detect_problem_type(df, target_col)

    # Detect duplicate rows
    n_duplicates = int(df.duplicated().sum())

    profile = {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "target_column": target_col,
        "problem_type": problem_type,
        "n_duplicates": n_duplicates,
        "duplicate_pct": round(n_duplicates / len(df) * 100, 2) if len(df) > 0 else 0.0,
        "column_profiles": column_profiles,
        "target_correlations": correlations,
        "class_balance": class_balance,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Profile saved to: {args.output}")
    print(json.dumps({
        "status": "success",
        "n_rows": profile["n_rows"],
        "n_cols": profile["n_cols"],
        "problem_type": problem_type,
        "columns": profile["columns"],
        "profile_path": args.output,
    }))


if __name__ == "__main__":
    main()
