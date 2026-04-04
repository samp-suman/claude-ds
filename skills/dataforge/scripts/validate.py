#!/usr/bin/env python3
"""
DataForge — Data Validation & Quality Gate

Runs all validation checks against the dataset. Uses exit codes to signal
severity to the orchestrator.

Usage:
    python validate.py --data <path> --target <col> --output-dir <project_dir>

Exit codes:
    0  All checks pass
    1  Warnings only — safe to continue with notice to user
    2  HARD STOP — pipeline must halt, user must fix issue first

Output:
    Writes {output_dir}/data/interim/validation_report.json
    Also writes {output_dir}/data/interim/.validation_passed (empty sentinel file on exit 0/1)
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
    return pd.read_csv(path)


# ── Individual Checks ─────────────────────────────────────────────────────────

def check_min_samples(df, min_rows: int = 50) -> dict:
    n = len(df)
    if n < min_rows:
        return {
            "name": "min_samples",
            "status": "HARD_STOP",
            "message": f"Only {n} rows found. Minimum required is {min_rows}. "
                       "DataForge cannot build reliable models on this dataset.",
        }
    return {"name": "min_samples", "status": "PASS", "message": f"{n:,} rows — sufficient."}


def check_target_exists(df, target_col: str) -> dict:
    if not target_col:
        return {"name": "target_exists", "status": "PASS", "message": "No target column (clustering mode)."}
    if target_col not in df.columns:
        return {
            "name": "target_exists",
            "status": "HARD_STOP",
            "message": f"Target column '{target_col}' not found. "
                       f"Available columns: {list(df.columns)[:10]}",
        }
    return {"name": "target_exists", "status": "PASS", "message": f"Target column '{target_col}' found."}


def check_target_leakage(df, target_col: str, threshold: float = 0.99) -> dict:
    """Detect features that are nearly perfectly correlated with the target (data leakage)."""
    if not target_col or target_col not in df.columns:
        return {"name": "target_leakage", "status": "PASS", "message": "Skipped (no target)."}

    import numpy as np
    numeric_df = df.select_dtypes(include="number")
    if target_col not in numeric_df.columns:
        return {"name": "target_leakage", "status": "PASS", "message": "Skipped (non-numeric target)."}

    leaky = []
    target_vals = numeric_df[target_col].dropna()
    for col in numeric_df.columns:
        if col == target_col:
            continue
        col_vals = numeric_df[col].dropna()
        common_idx = target_vals.index.intersection(col_vals.index)
        if len(common_idx) < 10:
            continue
        try:
            corr = abs(float(np.corrcoef(target_vals[common_idx], col_vals[common_idx])[0, 1]))
            if corr >= threshold:
                leaky.append({"column": col, "correlation": round(corr, 4)})
        except Exception:
            continue

    if leaky:
        return {
            "name": "target_leakage",
            "status": "HARD_STOP",
            "message": f"Target leakage detected! The following features have correlation "
                       f">= {threshold} with the target (likely leak future information): {leaky}. "
                       "Remove these columns before proceeding.",
            "leaky_columns": leaky,
        }
    return {"name": "target_leakage", "status": "PASS", "message": "No target leakage detected."}


def check_class_imbalance(df, target_col: str, max_ratio: float = 10.0) -> dict:
    if not target_col or target_col not in df.columns:
        return {"name": "class_imbalance", "status": "PASS", "message": "Skipped."}
    col = df[target_col]
    if col.nunique() > 20:
        return {"name": "class_imbalance", "status": "PASS", "message": "Skipped (regression)."}
    vc = col.value_counts()
    if len(vc) < 2:
        return {"name": "class_imbalance", "status": "PASS", "message": "Only one class — check target column."}
    ratio = vc.iloc[0] / vc.iloc[-1]
    if ratio > max_ratio:
        return {
            "name": "class_imbalance",
            "status": "WARNING",
            "message": f"Class imbalance ratio {ratio:.1f}:1. "
                       "Consider using class_weight='balanced' or SMOTE oversampling.",
            "imbalance_ratio": round(ratio, 2),
            "class_counts": vc.to_dict(),
        }
    return {
        "name": "class_imbalance",
        "status": "PASS",
        "message": f"Class balance acceptable (ratio {ratio:.1f}:1).",
    }


def check_high_missing(df, threshold: float = 50.0) -> dict:
    null_pct = (df.isnull().sum() / len(df) * 100)
    high_missing = null_pct[null_pct > threshold].round(1).to_dict()
    if high_missing:
        return {
            "name": "high_missing",
            "status": "WARNING",
            "message": f"{len(high_missing)} column(s) have > {threshold}% missing values: {high_missing}. "
                       "DataForge will impute with median/mode unless you drop them first.",
            "high_missing_columns": high_missing,
        }
    return {"name": "high_missing", "status": "PASS", "message": "All columns within missing value threshold."}


def check_duplicate_rows(df, threshold: float = 5.0) -> dict:
    n_dup = int(df.duplicated().sum())
    dup_pct = round(n_dup / len(df) * 100, 2) if len(df) > 0 else 0.0
    if dup_pct > threshold:
        return {
            "name": "duplicate_rows",
            "status": "WARNING",
            "message": f"{n_dup:,} duplicate rows ({dup_pct}%). DataForge will deduplicate automatically.",
            "n_duplicates": n_dup,
            "duplicate_pct": dup_pct,
        }
    return {"name": "duplicate_rows", "status": "PASS", "message": f"{n_dup} duplicate rows ({dup_pct}%)."}


def check_constant_columns(df) -> dict:
    constant = [col for col in df.columns if df[col].nunique() <= 1]
    if constant:
        return {
            "name": "constant_columns",
            "status": "WARNING",
            "message": f"Constant columns detected (will be dropped): {constant}",
            "constant_columns": constant,
        }
    return {"name": "constant_columns", "status": "PASS", "message": "No constant columns."}


def check_id_like_columns(df) -> dict:
    import numpy as np
    id_like = []
    for col in df.columns:
        uniq_ratio = df[col].nunique() / len(df)
        if uniq_ratio > 0.95 and len(df) > 100:
            id_like.append(col)
    if id_like:
        return {
            "name": "id_like_columns",
            "status": "WARNING",
            "message": f"High-cardinality ID-like columns detected (will be dropped unless they are the target): {id_like}",
            "id_like_columns": id_like,
        }
    return {"name": "id_like_columns", "status": "PASS", "message": "No suspicious ID-like columns."}


def check_target_variance(df, target_col: str) -> dict:
    if not target_col or target_col not in df.columns:
        return {"name": "target_variance", "status": "PASS", "message": "Skipped."}
    col = df[target_col]
    if col.nunique() <= 1:
        return {
            "name": "target_variance",
            "status": "HARD_STOP",
            "message": f"Target column '{target_col}' has zero variance (only one unique value). "
                       "Cannot train a model with a constant target.",
        }
    return {"name": "target_variance", "status": "PASS", "message": "Target column has sufficient variance."}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DataForge data validation")
    parser.add_argument("--data", required=True, help="Path to raw dataset file")
    parser.add_argument("--target", default=None, help="Target column name")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    interim_dir = output_dir / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_df(args.data)
    except Exception as e:
        report = {
            "status": "HARD_STOP",
            "exit_code": 2,
            "checks": [{"name": "load", "status": "HARD_STOP", "message": f"Cannot load dataset: {e}"}],
        }
        with open(interim_dir / "validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report))
        sys.exit(2)

    target_col = args.target

    checks = [
        check_min_samples(df),
        check_target_exists(df, target_col),
        check_target_variance(df, target_col),
        check_target_leakage(df, target_col),
        check_class_imbalance(df, target_col),
        check_high_missing(df),
        check_duplicate_rows(df),
        check_constant_columns(df),
        check_id_like_columns(df),
    ]

    hard_stops = [c for c in checks if c["status"] == "HARD_STOP"]
    warnings = [c for c in checks if c["status"] == "WARNING"]

    if hard_stops:
        exit_code = 2
        overall_status = "HARD_STOP"
    elif warnings:
        exit_code = 1
        overall_status = "WARNING"
    else:
        exit_code = 0
        overall_status = "PASS"

    report = {
        "status": overall_status,
        "exit_code": exit_code,
        "n_checks": len(checks),
        "n_hard_stops": len(hard_stops),
        "n_warnings": len(warnings),
        "checks": checks,
    }

    report_path = interim_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Write sentinel file so pre-train hook knows validation was done
    if exit_code <= 1:
        (interim_dir / ".validation_passed").touch()

    # Human-readable summary
    print(f"\n{'='*50}")
    print(f"DataForge Validation Report")
    print(f"{'='*50}")
    for check in checks:
        icon = "✓" if check["status"] == "PASS" else ("⚠" if check["status"] == "WARNING" else "✗")
        print(f"  {icon} {check['name']}: {check['message']}")
    print(f"{'='*50}")
    print(f"Result: {overall_status} (exit code: {exit_code})")
    if hard_stops:
        print("\nHARD STOP — Pipeline cannot continue. Please fix the issues above.")
    elif warnings:
        print("\nWarnings detected — Pipeline will continue with automatic mitigations.")
    else:
        print("\nAll checks passed — Pipeline may proceed.")

    print(json.dumps(report))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
