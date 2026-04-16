#!/usr/bin/env python3
"""
DataForge — EDA Script

Performs Exploratory Data Analysis on a single column or the full dataset.

Usage:
    # Per-column mode (called by df-eda-column agent):
    python eda.py --data <path> --column <col_name> --output <output_dir>

    # Global mode (called separately for heatmap + target distribution):
    python eda.py --data <path> --mode global --target <col> --output <output_dir>

Output:
    Per column:  {output_dir}/reports/eda/{column}_stats.json
                 {output_dir}/reports/eda/{column}_plot.png
    Global:      {output_dir}/reports/eda/correlation_heatmap.png
                 {output_dir}/reports/eda/target_distribution.png
                 {output_dir}/reports/eda/missing_matrix.png
                 {output_dir}/reports/eda/global_stats.json
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
    if p.endswith(".json"):
        return pd.read_json(path)
    if p.endswith(".xlsx") or p.endswith(".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def analyze_numeric_column(series, col_name: str, output_dir: Path) -> dict:
    """Full numeric column analysis: stats + distribution plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    clean = series.dropna()
    n = len(series)
    n_valid = len(clean)

    # Stats
    q1, q3 = float(clean.quantile(0.25)), float(clean.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    n_outliers = int(((clean < lower_bound) | (clean > upper_bound)).sum())

    stats = {
        "col_type": "numeric",
        "n": n,
        "n_valid": n_valid,
        "null_pct": round((n - n_valid) / n * 100, 2) if n > 0 else 0.0,
        "mean": round(float(clean.mean()), 4),
        "std": round(float(clean.std()), 4),
        "min": round(float(clean.min()), 4),
        "p5": round(float(clean.quantile(0.05)), 4),
        "p25": round(float(q1), 4),
        "median": round(float(clean.median()), 4),
        "p75": round(float(q3), 4),
        "p95": round(float(clean.quantile(0.95)), 4),
        "max": round(float(clean.max()), 4),
        "skewness": round(float(clean.skew()), 4),
        "kurtosis": round(float(clean.kurtosis()), 4),
        "n_outliers": n_outliers,
        "outlier_pct": round(n_outliers / n_valid * 100, 2) if n_valid > 0 else 0.0,
        "iqr_lower": round(lower_bound, 4),
        "iqr_upper": round(upper_bound, 4),
    }

    # Recommended handling
    recs = []
    engineering_suggestions = []

    if stats["null_pct"] > 0:
        if stats["null_pct"] < 30:
            recs.append("median_imputation")
        else:
            # Instead of "consider_dropping", suggest advanced imputation or engineering
            recs.append("advanced_imputation_needed")
            engineering_suggestions.append("indicator_feature")  # Add binary flag for missingness
            engineering_suggestions.append("knn_imputation")  # Or KNN imputation

    if abs(stats["skewness"]) > 1:
        recs.append("log_transform" if stats["min"] > 0 else "yeo_johnson_transform")

    if n_outliers > 0:
        recs.append("clip_outliers")

    recs.append("standard_scaling")
    stats["recommended_transforms"] = recs
    stats["engineering_suggestions"] = engineering_suggestions

    # Plot: histogram + KDE + boxplot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(f"Column: {col_name}", fontsize=13, fontweight="bold")

    # Histogram + KDE
    axes[0].hist(clean, bins=min(50, max(10, n_valid // 20)), color="#4C72B0", alpha=0.7, edgecolor="white")
    axes[0].set_title("Distribution")
    axes[0].set_xlabel(col_name)
    axes[0].set_ylabel("Count")
    ax2 = axes[0].twinx()
    try:
        clean.plot.kde(ax=ax2, color="red", linewidth=1.5)
        ax2.set_ylabel("Density", color="red")
    except Exception:
        pass

    # Boxplot
    axes[1].boxplot(clean, vert=True, patch_artist=True,
                    boxprops=dict(facecolor="#4C72B0", alpha=0.7))
    axes[1].set_title("Box Plot")
    axes[1].set_ylabel(col_name)

    plt.tight_layout()
    plot_path = output_dir / f"{col_name}_plot.png"
    plt.savefig(plot_path, dpi=100, bbox_inches="tight")
    plt.close()

    stats["plot_path"] = str(plot_path)
    return stats


def analyze_categorical_column(series, col_name: str, output_dir: Path) -> dict:
    """Categorical column analysis: value counts + bar chart."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(series)
    n_valid = int(series.notna().sum())
    vc = series.value_counts()
    n_unique = int(series.nunique())

    stats = {
        "col_type": "categorical",
        "n": n,
        "n_valid": n_valid,
        "null_pct": round((n - n_valid) / n * 100, 2) if n > 0 else 0.0,
        "n_unique": n_unique,
        "cardinality": round(n_unique / n, 4) if n > 0 else 0.0,
        "mode": str(vc.index[0]) if len(vc) > 0 else None,
        "mode_freq_pct": round(float(vc.iloc[0]) / n_valid * 100, 2) if n_valid > 0 else 0.0,
        "top_values": {str(k): int(v) for k, v in vc.head(10).items()},
    }

    recs = []
    engineering_suggestions = []

    if stats["null_pct"] > 0:
        recs.append("mode_imputation")

    if n_unique <= 10:
        recs.append("one_hot_encoding")
    elif n_unique <= 50:
        recs.append("label_encoding")
        # For moderate cardinality, suggest ordinal grouping if values are naturally ordered
        engineering_suggestions.append("ordinal_groups")
    else:
        # High cardinality: suggest multiple engineering options
        recs.append("target_encoding")
        engineering_suggestions.append("frequency_encoding")
        engineering_suggestions.append("count_list_items")  # If values contain lists

    stats["recommended_transforms"] = recs
    stats["engineering_suggestions"] = engineering_suggestions

    # Bar chart of top 20 values
    top_n = vc.head(20)
    fig, ax = plt.subplots(figsize=(10, 5))
    top_n.plot(kind="bar", ax=ax, color="#55A868", alpha=0.8, edgecolor="white")
    ax.set_title(f"Column: {col_name} (top {len(top_n)} values)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    plot_path = output_dir / f"{col_name}_plot.png"
    plt.savefig(plot_path, dpi=100, bbox_inches="tight")
    plt.close()

    stats["plot_path"] = str(plot_path)
    return stats


def analyze_datetime_column(series, col_name: str, output_dir: Path) -> dict:
    """Datetime column analysis: temporal range + time series plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    try:
        series = pd.to_datetime(series)
    except Exception:
        return {"col_type": "datetime_parse_error", "error": "Could not parse as datetime"}

    n = len(series)
    n_valid = int(series.notna().sum())

    stats = {
        "col_type": "datetime",
        "n": n,
        "n_valid": n_valid,
        "null_pct": round((n - n_valid) / n * 100, 2) if n > 0 else 0.0,
        "min": str(series.min()),
        "max": str(series.max()),
        "date_range_days": (series.max() - series.min()).days if n_valid > 1 else 0,
        "recommended_transforms": ["extract_year", "extract_month", "extract_dayofweek"],
    }

    # Time series plot
    fig, ax = plt.subplots(figsize=(12, 4))
    counts_by_period = series.dt.to_period("M").value_counts().sort_index()
    counts_by_period.plot(kind="bar", ax=ax, color="#C44E52", alpha=0.8)
    ax.set_title(f"Column: {col_name} — Records per Month", fontsize=13, fontweight="bold")
    ax.set_xlabel("Period")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    plot_path = output_dir / f"{col_name}_plot.png"
    plt.savefig(plot_path, dpi=100, bbox_inches="tight")
    plt.close()

    stats["plot_path"] = str(plot_path)
    return stats


def run_global_eda(df, target_col: str, output_dir: Path) -> dict:
    """Generate global EDA artifacts: correlation heatmap, target distribution, missing matrix."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    eda_dir = output_dir / "reports" / "eda"
    eda_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {}

    # 1. Correlation heatmap (numeric columns only)
    numeric_df = df.select_dtypes(include="number")
    if len(numeric_df.columns) >= 2:
        corr = numeric_df.corr()
        n_cols = len(corr.columns)
        fig_size = max(8, min(20, n_cols))
        fig, ax = plt.subplots(figsize=(fig_size, fig_size - 1))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=(n_cols <= 15), fmt=".2f",
                    cmap="RdBu_r", center=0, ax=ax, square=True,
                    linewidths=0.5, cbar_kws={"shrink": 0.8})
        ax.set_title("Correlation Heatmap (Numeric Features)", fontsize=14, fontweight="bold")
        plt.tight_layout()
        heatmap_path = eda_dir / "correlation_heatmap.png"
        plt.savefig(heatmap_path, dpi=100, bbox_inches="tight")
        plt.close()
        artifacts["correlation_heatmap"] = str(heatmap_path)

    # 2. Target distribution
    if target_col and target_col in df.columns:
        fig, ax = plt.subplots(figsize=(8, 5))
        target = df[target_col]
        if target.nunique() <= 20:
            vc = target.value_counts()
            vc.plot(kind="bar", ax=ax, color="#4C72B0", alpha=0.8, edgecolor="white")
            ax.set_title(f"Target Distribution: {target_col}", fontsize=13, fontweight="bold")
            ax.set_xlabel("Class")
            ax.set_ylabel("Count")
            ax.tick_params(axis="x", rotation=45)
        else:
            ax.hist(target.dropna(), bins=50, color="#4C72B0", alpha=0.7, edgecolor="white")
            ax.set_title(f"Target Distribution: {target_col}", fontsize=13, fontweight="bold")
            ax.set_xlabel(target_col)
            ax.set_ylabel("Count")
        plt.tight_layout()
        target_plot_path = eda_dir / "target_distribution.png"
        plt.savefig(target_plot_path, dpi=100, bbox_inches="tight")
        plt.close()
        artifacts["target_distribution"] = str(target_plot_path)

    # 3. Missing value matrix
    null_pcts = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    if null_pcts.max() > 0:
        show_cols = null_pcts[null_pcts > 0].head(30)
        fig, ax = plt.subplots(figsize=(10, max(4, len(show_cols) * 0.4)))
        show_cols.plot(kind="barh", ax=ax, color="#DD8452", alpha=0.8)
        ax.set_title("Missing Value Percentages", fontsize=13, fontweight="bold")
        ax.set_xlabel("Missing %")
        ax.axvline(x=50, color="red", linestyle="--", alpha=0.7, label="50% threshold")
        ax.legend()
        plt.tight_layout()
        missing_path = eda_dir / "missing_matrix.png"
        plt.savefig(missing_path, dpi=100, bbox_inches="tight")
        plt.close()
        artifacts["missing_matrix"] = str(missing_path)

    # 4. Global stats JSON
    global_stats = {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "total_missing_cells": int(df.isnull().sum().sum()),
        "total_missing_pct": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
        "artifacts": artifacts,
    }
    stats_path = eda_dir / "global_stats.json"
    with open(stats_path, "w") as f:
        json.dump(global_stats, f, indent=2)
    artifacts["global_stats"] = str(stats_path)

    return global_stats


def main():
    parser = argparse.ArgumentParser(description="DataForge EDA script")
    parser.add_argument("--data", required=True, help="Path to dataset file")
    parser.add_argument("--column", default=None, help="Column name (per-column mode)")
    parser.add_argument("--output", required=True, help="Output directory for EDA results")
    parser.add_argument("--mode", default="column", choices=["column", "global"],
                        help="'column' for per-column EDA, 'global' for heatmap + overview")
    parser.add_argument("--target", default=None, help="Target column (used in global mode)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    eda_dir = output_dir / "reports" / "eda"
    eda_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_df(args.data)
    except Exception as e:
        print(f"ERROR: Cannot load dataset: {e}", file=sys.stderr)
        sys.exit(2)

    if args.mode == "global":
        result = run_global_eda(df, args.target, output_dir)
        result["mode"] = "global"
        result["status"] = "success"
        print(json.dumps(result))
        return

    col_name = args.column
    if col_name not in df.columns:
        print(f"ERROR: Column '{col_name}' not found. Available: {list(df.columns)}", file=sys.stderr)
        sys.exit(2)

    series = df[col_name]
    dtype_str = str(series.dtype)

    try:
        if "datetime" in dtype_str:
            stats = analyze_datetime_column(series, col_name, eda_dir)
        elif dtype_str in ("object", "category", "string", "bool", "boolean"):
            stats = analyze_categorical_column(series, col_name, eda_dir)
        else:
            stats = analyze_numeric_column(series, col_name, eda_dir)
    except Exception as e:
        print(f"ERROR: EDA failed for column '{col_name}': {e}", file=sys.stderr)
        sys.exit(1)

    # Save stats JSON
    stats_path = eda_dir / f"{col_name}_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    result = {
        "agent": "df-eda-column",
        "status": "success",
        "column": col_name,
        "dtype": dtype_str,
        "col_type": stats.get("col_type"),
        "null_pct": stats.get("null_pct", 0),
        "recommended_transforms": stats.get("recommended_transforms", []),
        "stats_path": str(stats_path),
        "plot_path": stats.get("plot_path"),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
