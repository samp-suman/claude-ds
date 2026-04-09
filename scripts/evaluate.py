#!/usr/bin/env python3
"""
DataForge — Model Evaluation & Ranking Script

Reads all model metrics JSONs from src/models/, ranks them by primary metric,
generates comparison plots, and writes the leaderboard.

Usage:
    python evaluate.py \
        --output-dir <project_dir> \
        --problem <problem_type>

Output:
    {output_dir}/src/models/leaderboard.json
    {output_dir}/reports/model_comparison.png
    {output_dir}/reports/confusion_matrix_{best_model}.png  (classification only)
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def load_all_metrics(models_dir: Path) -> list:
    """Load all *_metrics.json files from the models directory."""
    results = []
    for path in models_dir.glob("*_metrics.json"):
        if "leaderboard" in path.name:
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            data["_metrics_path"] = str(path)
            results.append(data)
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
    return results


def rank_models(results: list, problem_type: str) -> list:
    """Rank models by primary metric (higher is better)."""
    primary_metric_map = {
        "binary_classification": "roc_auc",
        "multiclass_classification": "f1",
        "regression": "r2",
        "clustering": "silhouette_score",
    }
    primary = primary_metric_map.get(problem_type, "accuracy")

    def get_score(r):
        metrics = r.get("metrics", {})
        # Try primary, then cv_primary_mean, then fallback
        score = metrics.get(primary)
        if score is None:
            score = metrics.get(f"cv_{primary}_mean")
        if score is None:
            # Fallback to any numeric metric
            for v in metrics.values():
                if isinstance(v, (int, float)):
                    score = v
                    break
        return score or 0.0

    ranked = sorted(results, key=get_score, reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
        r["primary_metric"] = primary
        r["primary_value"] = round(float(get_score(r)), 4)
    return ranked


def plot_model_comparison(ranked: list, output_dir: Path, problem_type: str):
    """Bar chart comparing all models by primary metric."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if not ranked:
        return

    models = [r["model"] for r in ranked]
    primary_metric = ranked[0].get("primary_metric", "score")
    scores = [r["primary_value"] for r in ranked]

    # Color best model differently
    colors = ["#C44E52" if i == 0 else "#4C72B0" for i in range(len(models))]

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 1.5), 5))
    bars = ax.bar(models, scores, color=colors, alpha=0.85, edgecolor="white")

    # Add value labels
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{score:.3f}", ha="center", va="bottom", fontweight="bold", fontsize=10)

    ax.set_title(f"Model Comparison — {primary_metric.upper()} ({problem_type})",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel(primary_metric)
    ax.set_ylim(0, min(1.05, max(scores) * 1.15))
    ax.tick_params(axis="x", rotation=15)

    # Legend for best model
    import matplotlib.patches as mpatches
    best_patch = mpatches.Patch(color="#C44E52", alpha=0.85, label=f"Best: {models[0]}")
    ax.legend(handles=[best_patch], loc="lower right")

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "model_comparison.png"
    plt.savefig(plot_path, dpi=100, bbox_inches="tight")
    plt.close()
    return str(plot_path)


def main():
    parser = argparse.ArgumentParser(description="DataForge model evaluator")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    parser.add_argument("--problem", required=True, help="Problem type")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    models_dir = output_dir / "src" / "models"
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not models_dir.exists():
        print(f"ERROR: Models directory not found: {models_dir}", file=sys.stderr)
        sys.exit(2)

    results = load_all_metrics(models_dir)
    if not results:
        print("ERROR: No model metrics found. Run training first.", file=sys.stderr)
        sys.exit(2)

    ranked = rank_models(results, args.problem)

    # Plot comparison
    plot_path = plot_model_comparison(ranked, reports_dir, args.problem)

    # Build leaderboard
    leaderboard = {
        "problem_type": args.problem,
        "primary_metric": ranked[0].get("primary_metric"),
        "best_model": ranked[0]["model"],
        "best_score": ranked[0]["primary_value"],
        "models": [
            {
                "rank": r["rank"],
                "model": r["model"],
                "primary_metric": r.get("primary_metric"),
                "primary_value": r["primary_value"],
                "metrics": r.get("metrics", {}),
                "artifact_path": str(models_dir / f"{r['model']}.pkl"),
            }
            for r in ranked
        ],
        "comparison_plot": plot_path,
    }

    leaderboard_path = models_dir / "leaderboard.json"
    with open(leaderboard_path, "w") as f:
        json.dump(leaderboard, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Model Leaderboard ({args.problem})")
    print(f"{'='*50}")
    for r in ranked:
        medal = ["1st", "2nd", "3rd"][r["rank"] - 1] if r["rank"] <= 3 else f"{r['rank']}th"
        print(f"  {medal:4s} {r['model']:<20s} {r.get('primary_metric', 'score')}: {r['primary_value']:.4f}")
    print(f"\nBest model: {leaderboard['best_model']} ({leaderboard['primary_metric']}: {leaderboard['best_score']:.4f})")

    result = {
        "agent": "df-evaluate",
        "status": "success",
        "best_model": leaderboard["best_model"],
        "best_metric": leaderboard["primary_metric"],
        "best_score": leaderboard["best_score"],
        "n_models_evaluated": len(ranked),
        "leaderboard_path": str(leaderboard_path),
        "comparison_plot": plot_path,
        "error": None,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
