#!/usr/bin/env python3
"""
DataForge — Visualization Script

Generates the standard visualization suite for a DS project:
- Prediction distribution
- Confusion matrix (classification)
- Residual plot (regression)
- Prediction vs Actual (regression)
- Top-N feature pairplot (if n_features <= 10)

Usage:
    python visualize.py \
        --output-dir <project_dir> \
        --problem <problem_type> \
        [--model-path <pkl_path>] \
        [--data <processed_csv_path>] \
        [--target <target_col>]
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def plot_confusion_matrix(model, X_test, y_test, labels, output_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
    import numpy as np

    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

    fig, ax = plt.subplots(figsize=(max(6, len(labels)), max(5, len(labels) - 1)))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()


def plot_residuals(model, X_test, y_test, output_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    y_pred = model.predict(X_test)
    residuals = y_test - y_pred

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Residual plot
    axes[0].scatter(y_pred, residuals, alpha=0.5, color="#4C72B0", s=20)
    axes[0].axhline(y=0, color="red", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Predicted Values")
    axes[0].set_ylabel("Residuals")
    axes[0].set_title("Residual Plot", fontsize=12, fontweight="bold")

    # Prediction vs Actual
    axes[1].scatter(y_test, y_pred, alpha=0.5, color="#55A868", s=20)
    min_val = min(float(y_test.min()), float(y_pred.min()))
    max_val = max(float(y_test.max()), float(y_pred.max()))
    axes[1].plot([min_val, max_val], [min_val, max_val], "r--", linewidth=1.5, label="Perfect fit")
    axes[1].set_xlabel("Actual Values")
    axes[1].set_ylabel("Predicted Values")
    axes[1].set_title("Prediction vs Actual", fontsize=12, fontweight="bold")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()


def plot_roc_curve(model, X_test, y_test, output_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import RocCurveDisplay

    try:
        fig, ax = plt.subplots(figsize=(7, 6))
        RocCurveDisplay.from_estimator(model, X_test, y_test, ax=ax, color="#4C72B0")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5)
        ax.set_title("ROC Curve", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        plt.close()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="DataForge visualization suite")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--problem", required=True)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--data", default=None)
    parser.add_argument("--target", default=None)
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    import numpy as np

    output_dir = Path(args.output_dir)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {}

    # Load model if path provided
    model = None
    if args.model_path and Path(args.model_path).exists():
        try:
            import joblib
            model = joblib.load(args.model_path)
        except Exception as e:
            print(f"Warning: Cannot load model: {e}", file=sys.stderr)

    # Load data if path provided
    X_test, y_test = None, None
    if args.data and Path(args.data).exists():
        try:
            df = pd.read_csv(args.data)
            if args.target and args.target in df.columns:
                X = df.drop(columns=[args.target]).select_dtypes(include="number").fillna(0)
                y = df[args.target]
                from sklearn.model_selection import train_test_split
                if args.problem in ("binary_classification", "multiclass_classification"):
                    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
                else:
                    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        except Exception as e:
            print(f"Warning: Cannot prepare test data: {e}", file=sys.stderr)

    # ── Generate visualizations by problem type ──────────────────────────────

    if model is not None and X_test is not None and y_test is not None:

        if args.problem in ("binary_classification", "multiclass_classification"):
            # Confusion matrix
            try:
                labels = sorted(y_test.unique())
                cm_path = reports_dir / "confusion_matrix.png"
                plot_confusion_matrix(model, X_test, y_test, labels, cm_path)
                artifacts["confusion_matrix"] = str(cm_path)
            except Exception as e:
                print(f"Warning: Confusion matrix failed: {e}", file=sys.stderr)

            # ROC curve (binary only)
            if args.problem == "binary_classification":
                roc_path = reports_dir / "roc_curve.png"
                if plot_roc_curve(model, X_test, y_test, roc_path):
                    artifacts["roc_curve"] = str(roc_path)

        elif args.problem == "regression":
            # Residual + prediction vs actual
            try:
                residual_path = reports_dir / "residual_plot.png"
                plot_residuals(model, X_test, y_test, residual_path)
                artifacts["residual_plot"] = str(residual_path)
            except Exception as e:
                print(f"Warning: Residual plot failed: {e}", file=sys.stderr)

    # ── Pairplot for small feature sets ───────────────────────────────────────
    if args.data and Path(args.data).exists():
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            df = pd.read_csv(args.data)
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if args.target and args.target in numeric_cols:
                numeric_cols.remove(args.target)
            if 2 <= len(numeric_cols) <= 8:
                cols_to_plot = numeric_cols[:8]
                if args.target and args.target in df.columns:
                    plot_df = df[cols_to_plot + [args.target]].dropna().head(1000)
                    hue = args.target if df[args.target].nunique() <= 10 else None
                else:
                    plot_df = df[cols_to_plot].dropna().head(1000)
                    hue = None
                fig = sns.pairplot(plot_df, hue=hue, plot_kws={"alpha": 0.4, "s": 15},
                                   height=2.0, aspect=1.0)
                plt.suptitle("Feature Pairplot", y=1.02, fontsize=12, fontweight="bold")
                pairplot_path = reports_dir / "pairplot.png"
                plt.savefig(pairplot_path, dpi=80, bbox_inches="tight")
                plt.close()
                artifacts["pairplot"] = str(pairplot_path)
        except Exception as e:
            print(f"Warning: Pairplot failed: {e}", file=sys.stderr)

    result = {
        "agent": "df-visualize",
        "status": "success",
        "artifacts": artifacts,
        "error": None,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
