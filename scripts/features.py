#!/usr/bin/env python3
"""
DataForge — Feature Engineering Script

Applies transforms to a single column based on EDA recommendations.
Called per-column by df-feature-column agent.

Usage:
    python features.py \
        --data <path_to_processed_csv> \
        --column <col_name> \
        --transforms <json_list_of_transforms> \
        --output-dir <project_dir> \
        --target <target_col>

Transforms (pass as JSON array string):
    ["median_imputation", "log_transform", "standard_scaling",
     "one_hot_encoding", "label_encoding", "target_encoding",
     "yeo_johnson_transform", "clip_outliers", "mode_imputation",
     "extract_year", "extract_month", "extract_dayofweek",
     "consider_dropping", "drop"]

Output:
    Writes transform log entry to {output_dir}/data/interim/feature_transforms.json
    Returns JSON result with transformed column info.
    The full processed dataset is assembled by the orchestrator after all column agents complete.
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def load_df(path: str):
    import pandas as pd
    p = path.lower()
    if p.endswith(".parquet") or p.endswith(".pq"):
        return pd.read_parquet(path)
    if p.endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_csv(path)


def apply_transforms(series, transforms: list, target_series=None, col_name: str = "") -> tuple:
    """Apply a list of transforms to a Series. Returns (transformed_series, transform_log)."""
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import LabelEncoder, StandardScaler, PowerTransformer

    log = []
    result = series.copy()
    dropped = False
    new_cols = {}  # For one-hot encoding which creates multiple columns

    for transform in transforms:
        try:
            if transform in ("consider_dropping", "drop"):
                dropped = True
                log.append({"transform": transform, "status": "applied", "note": "Column flagged for dropping"})
                break

            elif transform == "median_imputation":
                if result.dtype in (float, "float32", "float64") or pd.api.types.is_numeric_dtype(result):
                    median_val = result.median()
                    n_filled = result.isna().sum()
                    result = result.fillna(median_val)
                    log.append({"transform": transform, "status": "applied",
                                "median": round(float(median_val), 4), "n_filled": int(n_filled)})

            elif transform == "mode_imputation":
                mode_val = result.mode()
                if len(mode_val) > 0:
                    n_filled = int(result.isna().sum())
                    result = result.fillna(mode_val.iloc[0])
                    log.append({"transform": transform, "status": "applied",
                                "mode": str(mode_val.iloc[0]), "n_filled": n_filled})

            elif transform == "log_transform":
                if pd.api.types.is_numeric_dtype(result) and result.min() > 0:
                    result = np.log1p(result)
                    log.append({"transform": transform, "status": "applied"})
                else:
                    log.append({"transform": transform, "status": "skipped",
                                "reason": "Non-positive values — use yeo_johnson instead"})

            elif transform == "yeo_johnson_transform":
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna()
                    pt = PowerTransformer(method="yeo-johnson")
                    transformed = pt.fit_transform(result[valid_idx].values.reshape(-1, 1)).flatten()
                    result.loc[valid_idx] = transformed
                    log.append({"transform": transform, "status": "applied",
                                "lambda": round(float(pt.lambdas_[0]), 4)})

            elif transform == "standard_scaling":
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna()
                    mean_val = float(result[valid_idx].mean())
                    std_val = float(result[valid_idx].std())
                    if std_val > 0:
                        result = (result - mean_val) / std_val
                        log.append({"transform": transform, "status": "applied",
                                    "mean": round(mean_val, 4), "std": round(std_val, 4)})

            elif transform == "clip_outliers":
                if pd.api.types.is_numeric_dtype(result):
                    q1, q3 = float(result.quantile(0.25)), float(result.quantile(0.75))
                    iqr = q3 - q1
                    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    n_clipped = int(((result < lower) | (result > upper)).sum())
                    result = result.clip(lower=lower, upper=upper)
                    log.append({"transform": transform, "status": "applied",
                                "lower": round(lower, 4), "upper": round(upper, 4),
                                "n_clipped": n_clipped})

            elif transform == "one_hot_encoding":
                n_unique = result.nunique()
                dummies = pd.get_dummies(result, prefix=col_name, drop_first=True)
                new_cols.update({col: dummies[col] for col in dummies.columns})
                log.append({"transform": transform, "status": "applied",
                            "n_new_columns": len(dummies.columns),
                            "new_columns": list(dummies.columns)})

            elif transform == "label_encoding":
                le = LabelEncoder()
                valid_idx = result.notna()
                result_encoded = result.copy().astype(str)
                result_encoded[valid_idx] = le.fit_transform(result[valid_idx].astype(str))
                result = pd.to_numeric(result_encoded, errors="coerce")
                log.append({"transform": transform, "status": "applied",
                            "classes": list(le.classes_)[:20]})

            elif transform == "target_encoding":
                if target_series is not None and len(target_series) == len(result):
                    target_num = pd.to_numeric(target_series, errors="coerce")
                    if target_num.notna().sum() > 0:
                        mapping = result.astype(str).map(
                            target_num.groupby(result.astype(str)).mean()
                        )
                        result = mapping.fillna(target_num.mean())
                        log.append({"transform": transform, "status": "applied"})
                    else:
                        log.append({"transform": transform, "status": "skipped",
                                    "reason": "Non-numeric target"})
                else:
                    log.append({"transform": transform, "status": "skipped",
                                "reason": "No target series available"})

            elif transform == "extract_year":
                result = pd.to_datetime(result, errors="coerce").dt.year
                log.append({"transform": transform, "status": "applied"})

            elif transform == "extract_month":
                result = pd.to_datetime(result, errors="coerce").dt.month
                log.append({"transform": transform, "status": "applied"})

            elif transform == "extract_dayofweek":
                result = pd.to_datetime(result, errors="coerce").dt.dayofweek
                log.append({"transform": transform, "status": "applied"})

            elif transform == "indicator_feature":
                # Add binary flag for missingness
                n_missing = result.isna().sum()
                if n_missing > 0:
                    new_cols[f"{col_name}_is_missing"] = result.isna().astype(int)
                    log.append({"transform": transform, "status": "applied",
                                "n_missing": int(n_missing),
                                "new_column": f"{col_name}_is_missing"})

            elif transform == "knn_imputation":
                if pd.api.types.is_numeric_dtype(result):
                    from sklearn.impute import KNNImputer
                    imputer = KNNImputer(n_neighbors=5)
                    valid_idx = result.notna()
                    n_filled = int(result.isna().sum())
                    if n_filled > 0:
                        result = pd.Series(
                            imputer.fit_transform(result.values.reshape(-1, 1)).flatten(),
                            index=result.index
                        )
                        log.append({"transform": transform, "status": "applied",
                                    "n_filled": n_filled, "n_neighbors": 5})

            elif transform == "iterative_imputation":
                if pd.api.types.is_numeric_dtype(result):
                    from sklearn.experimental import enable_iterative_imputer
                    from sklearn.impute import IterativeImputer
                    imputer = IterativeImputer(max_iter=10, random_state=42)
                    n_filled = int(result.isna().sum())
                    if n_filled > 0:
                        result = pd.Series(
                            imputer.fit_transform(result.values.reshape(-1, 1)).flatten(),
                            index=result.index
                        )
                        log.append({"transform": transform, "status": "applied",
                                    "n_filled": n_filled})

            elif transform == "frequency_encoding":
                # Encode by frequency of occurrence
                freq_map = result.value_counts(normalize=True).to_dict()
                result = result.map(freq_map)
                log.append({"transform": transform, "status": "applied",
                            "n_categories": len(freq_map)})

            elif transform == "binary_encoding":
                # Binary encoding: convert integer labels to binary representation
                if result.dtype in ('object', 'category'):
                    le = LabelEncoder()
                    valid_idx = result.notna()
                    result_encoded = le.fit_transform(result[valid_idx].astype(str))
                    result = result.copy().astype(str)
                    result[valid_idx] = result_encoded
                    result = pd.to_numeric(result, errors="coerce")
                    log.append({"transform": transform, "status": "applied",
                                "n_categories": len(le.classes_)})

            elif transform == "robust_scaling":
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna()
                    from sklearn.preprocessing import RobustScaler
                    scaler = RobustScaler()
                    result.loc[valid_idx] = scaler.fit_transform(result[valid_idx].values.reshape(-1, 1)).flatten()
                    log.append({"transform": transform, "status": "applied"})

            elif transform == "maxabs_scaling":
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna()
                    max_abs = result[valid_idx].abs().max()
                    if max_abs > 0:
                        result = result / max_abs
                    log.append({"transform": transform, "status": "applied",
                                "max_abs": round(float(max_abs), 4)})

            elif transform == "polynomial_features":
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna()
                    result_sq = (result ** 2)
                    new_cols[f"{col_name}_squared"] = result_sq
                    log.append({"transform": transform, "status": "applied",
                                "new_column": f"{col_name}_squared"})

            elif transform == "ratio_feature":
                # Ratio feature: only meaningful if we have a denominator (pass via context)
                # For now, create reciprocal to avoid division by zero issues
                if pd.api.types.is_numeric_dtype(result):
                    valid_idx = result.notna() & (result != 0)
                    ratio = 1.0 / (result.abs() + 1.0)  # +1 to avoid division by zero
                    new_cols[f"{col_name}_reciprocal"] = ratio
                    log.append({"transform": transform, "status": "applied",
                                "new_column": f"{col_name}_reciprocal"})

            elif transform == "extract_numeric":
                # Extract numeric values from string
                if result.dtype == 'object':
                    import re
                    numeric_vals = result.str.extract(r'([\d.]+)', expand=False)
                    result = pd.to_numeric(numeric_vals, errors="coerce")
                    log.append({"transform": transform, "status": "applied",
                                "n_extracted": int(result.notna().sum())})

            elif transform == "ordinal_groups":
                # Group high-cardinality ordinal values (e.g., floor numbers → ground/low/mid/high)
                if pd.api.types.is_numeric_dtype(result) or result.dtype == 'object':
                    try:
                        numeric_result = pd.to_numeric(result, errors="coerce")
                        if numeric_result.notna().sum() > 0:
                            result_grouped = pd.cut(numeric_result, bins=4, labels=['group1', 'group2', 'group3', 'group4'])
                            le = LabelEncoder()
                            result = le.fit_transform(result_grouped.astype(str))
                            log.append({"transform": transform, "status": "applied",
                                        "n_groups": 4})
                    except Exception:
                        log.append({"transform": transform, "status": "skipped",
                                    "reason": "Could not create ordinal groups"})

            elif transform == "count_list_items":
                # Count items in list-like strings
                if result.dtype == 'object':
                    list_count = result.str.split(',').str.len()
                    new_cols[f"{col_name}_list_count"] = list_count
                    log.append({"transform": transform, "status": "applied",
                                "new_column": f"{col_name}_list_count"})

        except Exception as e:
            log.append({"transform": transform, "status": "error", "error": str(e)})

    return result, new_cols, dropped, log


def main():
    parser = argparse.ArgumentParser(description="DataForge feature engineering")
    parser.add_argument("--data", required=True, help="Path to current dataset file")
    parser.add_argument("--column", required=True, help="Column name to transform")
    parser.add_argument("--transforms", required=True,
                        help="JSON array of transform names")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    parser.add_argument("--target", default=None, help="Target column name")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    interim_dir = output_dir / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    try:
        transforms = json.loads(args.transforms)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid transforms JSON: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        df = load_df(args.data)
    except Exception as e:
        print(f"ERROR: Cannot load dataset: {e}", file=sys.stderr)
        sys.exit(2)

    col_name = args.column
    if col_name not in df.columns:
        print(f"ERROR: Column '{col_name}' not found.", file=sys.stderr)
        sys.exit(2)

    target_series = df[args.target] if args.target and args.target in df.columns else None

    _, new_cols, dropped, log = apply_transforms(
        df[col_name], transforms, target_series, col_name
    )

    # Append transform log to feature_transforms.json
    transforms_log_path = interim_dir / "feature_transforms.json"
    existing = []
    if transforms_log_path.exists():
        try:
            with open(transforms_log_path) as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append({
        "column": col_name,
        "transforms_applied": log,
        "dropped": dropped,
        "new_columns": list(new_cols.keys()),
    })

    with open(transforms_log_path, "w") as f:
        json.dump(existing, f, indent=2)

    result = {
        "agent": "df-feature-column",
        "status": "success",
        "column": col_name,
        "dropped": dropped,
        "transforms_applied": [t["transform"] for t in log if t.get("status") == "applied"],
        "transforms_skipped": [t["transform"] for t in log if t.get("status") == "skipped"],
        "transforms_errored": [t["transform"] for t in log if t.get("status") == "error"],
        "new_columns": list(new_cols.keys()),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
