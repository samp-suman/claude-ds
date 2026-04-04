#!/usr/bin/env python3
"""
DataForge — Model Interpretability Script

Generates SHAP explanations and feature importance plots for the best model.

Usage:
    python interpret.py \
        --model-path <pkl_path> \
        --data <processed_csv_path> \
        --target <target_column> \
        --problem <problem_type> \
        --output-dir <project_dir>

Output:
    {output_dir}/reports/shap_summary.png       — SHAP summary plot (beeswarm)
    {output_dir}/reports/shap_bar.png           — SHAP mean absolute bar chart
    {output_dir}/reports/feature_importance.png — Model feature importance (if available)
    {output_dir}/reports/shap_values.json       — SHAP values for top 20 features
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def main():
    parser = argparse.ArgumentParser(description="DataForge model interpretability")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--target", default=None)
    parser.add_argument("--problem", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import joblib

    output_dir = Path(args.output_dir)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load model and data
    try:
        model = joblib.load(args.model_path)
    except Exception as e:
        print(f"ERROR: Cannot load model: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_csv(args.data)
    except Exception as e:
        print(f"ERROR: Cannot load data: {e}", file=sys.stderr)
        sys.exit(1)

    if args.target and args.target in df.columns:
        X = df.drop(columns=[args.target]).select_dtypes(include="number").fillna(0)
        y = df[args.target]
    else:
        X = df.select_dtypes(include="number").fillna(0)
        y = None

    # Sample for SHAP if large dataset (SHAP is slow on large datasets)
    n_sample = min(500, len(X))
    X_sample = X.sample(n=n_sample, random_state=42) if len(X) > n_sample else X

    artifacts = {}

    # ── SHAP Analysis ──────────────────────────────────────────────────────────
    try:
        import shap

        # Choose explainer based on model type
        model_type = type(model).__name__.lower()
        if any(t in model_type for t in ["xgb", "lgbm", "lgb", "randomforest", "gradientboosting", "catboost"]):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)
        else:
            explainer = shap.LinearExplainer(model, X_sample) if hasattr(model, "coef_") else \
                        shap.KernelExplainer(model.predict_proba if hasattr(model, "predict_proba") else model.predict,
                                             shap.sample(X_sample, 50))
            shap_values = explainer.shap_values(X_sample)

        # For binary classification, use positive class SHAP values
        if isinstance(shap_values, list) and len(shap_values) == 2:
            shap_vals = shap_values[1]
        elif isinstance(shap_values, list):
            shap_vals = shap_values[0]
        else:
            shap_vals = shap_values

        # SHAP summary beeswarm plot
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_vals, X_sample, show=False, max_display=20)
        plt.title("SHAP Feature Impact (Beeswarm)", fontsize=13, fontweight="bold", pad=10)
        plt.tight_layout()
        shap_summary_path = reports_dir / "shap_summary.png"
        plt.savefig(shap_summary_path, dpi=100, bbox_inches="tight")
        plt.close()
        artifacts["shap_summary"] = str(shap_summary_path)

        # SHAP bar chart (mean absolute SHAP values)
        mean_shap = np.abs(shap_vals).mean(axis=0)
        feature_shap = pd.Series(mean_shap, index=X_sample.columns).sort_values(ascending=False).head(20)

        fig, ax = plt.subplots(figsize=(10, 6))
        feature_shap.sort_values().plot(kind="barh", ax=ax, color="#4C72B0", alpha=0.8)
        ax.set_title("Mean Absolute SHAP Values (Feature Importance)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Mean |SHAP value|")
        plt.tight_layout()
        shap_bar_path = reports_dir / "shap_bar.png"
        plt.savefig(shap_bar_path, dpi=100, bbox_inches="tight")
        plt.close()
        artifacts["shap_bar"] = str(shap_bar_path)

        # Save top SHAP values as JSON
        top_features = feature_shap.head(20)
        shap_json = {
            "top_features": {feat: round(float(val), 6) for feat, val in top_features.items()},
            "n_samples_explained": n_sample,
        }
        shap_json_path = reports_dir / "shap_values.json"
        with open(shap_json_path, "w") as f:
            json.dump(shap_json, f, indent=2)
        artifacts["shap_values_json"] = str(shap_json_path)

        print(f"SHAP analysis complete. Top feature: {top_features.index[0]} (SHAP={top_features.iloc[0]:.4f})")

    except ImportError:
        print("Warning: SHAP not installed. Falling back to feature importance.", file=sys.stderr)
    except Exception as e:
        print(f"Warning: SHAP failed: {e}. Falling back to feature importance.", file=sys.stderr)

    # ── Native Feature Importance (fallback / supplementary) ─────────────────
    try:
        if hasattr(model, "feature_importances_"):
            importance = pd.Series(model.feature_importances_, index=X.columns)
            importance = importance.sort_values(ascending=False).head(20)

            fig, ax = plt.subplots(figsize=(10, 6))
            importance.sort_values().plot(kind="barh", ax=ax, color="#55A868", alpha=0.8)
            ax.set_title("Feature Importance (Model Native)", fontsize=13, fontweight="bold")
            ax.set_xlabel("Importance Score")
            plt.tight_layout()
            fi_path = reports_dir / "feature_importance.png"
            plt.savefig(fi_path, dpi=100, bbox_inches="tight")
            plt.close()
            artifacts["feature_importance"] = str(fi_path)

        elif hasattr(model, "coef_"):
            # Linear model coefficients
            coef = model.coef_.flatten() if model.coef_.ndim > 1 else model.coef_
            if len(coef) == len(X.columns):
                coef_series = pd.Series(np.abs(coef), index=X.columns).sort_values(ascending=False).head(20)
                fig, ax = plt.subplots(figsize=(10, 6))
                coef_series.sort_values().plot(kind="barh", ax=ax, color="#C44E52", alpha=0.8)
                ax.set_title("Feature Coefficients (Absolute Value)", fontsize=13, fontweight="bold")
                ax.set_xlabel("|Coefficient|")
                plt.tight_layout()
                fi_path = reports_dir / "feature_importance.png"
                plt.savefig(fi_path, dpi=100, bbox_inches="tight")
                plt.close()
                artifacts["feature_importance"] = str(fi_path)

    except Exception as e:
        print(f"Warning: Feature importance plot failed: {e}", file=sys.stderr)

    result = {
        "agent": "df-interpret",
        "status": "success",
        "artifacts": artifacts,
        "n_samples_explained": n_sample,
        "error": None,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
