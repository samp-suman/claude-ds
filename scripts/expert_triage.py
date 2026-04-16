#!/usr/bin/env python3
"""
DataForge — Expert Triage

Computes a complexity score for the current pipeline stage and decides
whether expert review is needed, and at what depth.

Usage:
    python expert_triage.py --stage <preprocessing|eda|modeling> \
        --profile <profile.json> --output <triage.json> \
        [--validation <validation_report.json>] \
        [--eda-summary <eda_summary.json>] \
        [--leaderboard <leaderboard.json>] \
        [--feature-report <feature_report.json>] \
        [--cache-dir <path>] \
        [--production] [--first-run] [--domain-flag]

Output:
    {
        "trigger_experts": true/false,
        "complexity_level": "skip" | "light" | "full",
        "score": 0.0-1.0,
        "reasons": ["reason1", "reason2"],
        "stage": "preprocessing"
    }

Thresholds:
    skip  : score < 0.2  (no experts)
    light : score 0.2-0.5 (lead expert only)
    full  : score > 0.5  (all relevant experts + lead)

Always "full" if: --production, --first-run, or --domain-flag is set.

Exit codes: 0 = success, 1 = error
"""
import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Per-stage signal functions
# ---------------------------------------------------------------------------

def _preprocessing_signals(profile, validation, feature_report):
    """Compute complexity signals after preprocessing stage."""
    signals = []
    scores = []

    if not profile:
        return 0.0, ["no profile available"]

    col_profiles = profile.get("column_profiles", {})
    n_cols = len(col_profiles)

    # --- High imputation: >2 columns with >30% missing ---
    high_missing = 0
    for col, info in col_profiles.items():
        missing_pct = info.get("missing_pct", 0)
        if missing_pct > 30:
            high_missing += 1
    if high_missing > 2:
        signals.append(f"{high_missing} columns with >30% missing values")
        scores.append(0.3)
    elif high_missing > 0:
        scores.append(0.1)

    # --- Many features (>50) ---
    if n_cols > 50:
        signals.append(f"{n_cols} features (high dimensionality)")
        scores.append(0.2)

    # --- Class imbalance (>5:1) ---
    if validation:
        for check in validation.get("checks", []):
            if check.get("check") == "class_imbalance":
                ratio = check.get("details", {}).get("ratio", 1)
                if ratio and ratio > 5:
                    signals.append(f"class imbalance ratio {ratio:.1f}:1")
                    scores.append(0.3)

    # --- High-cardinality categoricals (>3 columns with >50 unique) ---
    high_card = 0
    for col, info in col_profiles.items():
        if info.get("dtype") == "object" and info.get("n_unique", 0) > 50:
            high_card += 1
    if high_card > 3:
        signals.append(f"{high_card} high-cardinality categorical columns")
        scores.append(0.2)

    # --- Rows dropped (>20%) from validation ---
    if validation:
        for check in validation.get("checks", []):
            if check.get("check") == "duplicates":
                dup_pct = check.get("details", {}).get("pct", 0)
                if dup_pct and dup_pct > 20:
                    signals.append(f"{dup_pct:.0f}% duplicate rows")
                    scores.append(0.2)

    # --- Feature report: columns dropped ---
    if feature_report:
        dropped = feature_report.get("columns_dropped", [])
        if len(dropped) > 3:
            signals.append(f"{len(dropped)} columns dropped during feature engineering")
            scores.append(0.2)

    # --- Mixed dtypes ---
    dtypes = set(info.get("dtype", "") for info in col_profiles.values())
    if len(dtypes) > 4:
        signals.append(f"{len(dtypes)} distinct dtypes (complex schema)")
        scores.append(0.1)

    composite = min(sum(scores), 1.0) if scores else 0.0
    return composite, signals


def _eda_signals(profile, eda_summary):
    """Compute complexity signals after EDA stage."""
    signals = []
    scores = []

    col_profiles = profile.get("column_profiles", {}) if profile else {}

    # --- Skewed features (>30% with abs(skew) > 2) ---
    if col_profiles:
        n_numeric = 0
        n_skewed = 0
        for col, info in col_profiles.items():
            if info.get("dtype", "").startswith(("float", "int")):
                n_numeric += 1
                skew = info.get("skewness", 0)
                if skew is not None and abs(skew) > 2:
                    n_skewed += 1
        if n_numeric > 0 and n_skewed / max(n_numeric, 1) > 0.3:
            signals.append(f"{n_skewed}/{n_numeric} numeric features highly skewed")
            scores.append(0.25)

    # --- Multicollinear pairs (>2 with corr > 0.85) ---
    if eda_summary:
        corr_pairs = eda_summary.get("high_correlation_pairs", [])
        n_high_corr = sum(1 for p in corr_pairs
                          if abs(p.get("correlation", 0)) > 0.85)
        if n_high_corr > 2:
            signals.append(f"{n_high_corr} feature pairs with correlation >0.85")
            scores.append(0.3)

    # --- Outlier-heavy (>3 columns with >10% outliers) ---
    if eda_summary:
        outlier_cols = eda_summary.get("outlier_columns", [])
        heavy = [c for c in outlier_cols if c.get("outlier_pct", 0) > 10]
        if len(heavy) > 3:
            signals.append(f"{len(heavy)} columns with >10% outliers")
            scores.append(0.2)

    # --- High-cardinality categoricals ---
    high_card = sum(1 for info in col_profiles.values()
                    if info.get("dtype") == "object" and info.get("n_unique", 0) > 50)
    if high_card > 3:
        signals.append(f"{high_card} high-cardinality categorical columns")
        scores.append(0.15)

    # --- Systematic missing (pattern across rows) ---
    if eda_summary and eda_summary.get("systematic_missing", False):
        signals.append("systematic missing pattern detected")
        scores.append(0.2)

    # --- Target imbalance (<10% minority class) ---
    if eda_summary:
        minority_pct = eda_summary.get("target_minority_pct")
        if minority_pct is not None and minority_pct < 10:
            signals.append(f"target minority class at {minority_pct:.1f}%")
            scores.append(0.3)

    composite = min(sum(scores), 1.0) if scores else 0.0
    return composite, signals


def _modeling_signals(leaderboard):
    """Compute complexity signals after modeling stage."""
    signals = []
    scores = []

    if not leaderboard:
        return 0.0, ["no leaderboard available"]

    models = leaderboard.get("models", [])
    if not models:
        return 0.0, ["no models in leaderboard"]

    # --- All models poor performance ---
    primary_metric = leaderboard.get("primary_metric", "")
    best_score = models[0].get("score", 0) if models else 0

    is_classification = primary_metric in (
        "roc_auc", "f1", "accuracy", "precision", "recall"
    )
    if is_classification and best_score < 0.6:
        signals.append(f"best model {primary_metric}={best_score:.3f} (below 0.6)")
        scores.append(0.4)
    elif not is_classification and best_score < 0.3:
        signals.append(f"best model {primary_metric}={best_score:.3f} (below 0.3)")
        scores.append(0.4)

    # --- Train-test gap (>0.05) ---
    for m in models:
        train_score = m.get("train_score", 0)
        test_score = m.get("score", 0)
        gap = abs(train_score - test_score)
        if gap > 0.05:
            signals.append(
                f"{m.get('model', '?')}: train-test gap {gap:.3f} (possible overfit)"
            )
            scores.append(0.3)
            break  # one example is enough

    # --- High CV variance (>0.05) ---
    for m in models:
        cv_std = m.get("cv_std", 0)
        if cv_std and cv_std > 0.05:
            signals.append(f"{m.get('model', '?')}: CV std={cv_std:.3f} (unstable)")
            scores.append(0.2)
            break

    # --- Model failures (>50%) ---
    n_failed = sum(1 for m in models if m.get("status") == "failed")
    if len(models) > 0 and n_failed / len(models) > 0.5:
        signals.append(f"{n_failed}/{len(models)} models failed")
        scores.append(0.3)

    # --- Score clustering (<0.01 spread) ---
    if len(models) >= 3:
        top_scores = [m.get("score", 0) for m in models[:3]]
        spread = max(top_scores) - min(top_scores)
        if spread < 0.01:
            signals.append(
                f"top 3 models within {spread:.4f} — may need tuning"
            )
            scores.append(0.15)

    # --- Unexpected ranking ---
    if leaderboard.get("unexpected_ranking"):
        signals.append("unexpected model ranking detected")
        scores.append(0.2)

    composite = min(sum(scores), 1.0) if scores else 0.0
    return composite, signals


# ---------------------------------------------------------------------------
# Main triage logic
# ---------------------------------------------------------------------------

STAGE_FUNCTIONS = {
    "preprocessing": lambda args: _preprocessing_signals(
        args["profile"], args["validation"], args["feature_report"]
    ),
    "eda": lambda args: _eda_signals(args["profile"], args["eda_summary"]),
    "modeling": lambda args: _modeling_signals(args["leaderboard"]),
}


def load_json(path):
    """Safely load a JSON file, return None if missing or invalid."""
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def run_triage(stage, inputs, force_full=False):
    """Run triage for the given stage. Returns result dict."""
    if stage not in STAGE_FUNCTIONS:
        return {
            "trigger_experts": False,
            "complexity_level": "skip",
            "score": 0.0,
            "reasons": [f"unknown stage: {stage}"],
            "stage": stage,
        }

    score, reasons = STAGE_FUNCTIONS[stage](inputs)

    # Force full if flags set
    if force_full:
        complexity_level = "full"
        trigger = True
        if not reasons:
            reasons = ["forced full review (production/first-run/domain flag)"]
    elif score < 0.05:
        # Very low complexity: skip expert review
        complexity_level = "skip"
        trigger = False
    elif score <= 0.4:
        # Moderate complexity: light review (lead expert only)
        complexity_level = "light"
        trigger = True
    else:
        # High complexity: full review (all domain + methodology experts)
        complexity_level = "full"
        trigger = True

    return {
        "trigger_experts": trigger,
        "complexity_level": complexity_level,
        "score": round(score, 3),
        "reasons": reasons,
        "stage": stage,
    }


def main():
    parser = argparse.ArgumentParser(description="DataForge expert triage")
    parser.add_argument("--stage", required=True,
                        choices=["preprocessing", "eda", "modeling", "feature_engineering"],
                        help="Pipeline stage to evaluate")
    parser.add_argument("--new-dataset", action="store_true",
                        help="Force light expert review (new dataset with no prior history)")
    parser.add_argument("--profile", default=None, help="Path to profile.json")
    parser.add_argument("--validation", default=None,
                        help="Path to validation_report.json")
    parser.add_argument("--eda-summary", default=None,
                        help="Path to eda_summary.json")
    parser.add_argument("--leaderboard", default=None,
                        help="Path to leaderboard.json")
    parser.add_argument("--feature-report", default=None,
                        help="Path to feature_report.json")
    parser.add_argument("--cache-dir", default=None,
                        help="Path to expert cache directory")
    parser.add_argument("--output", required=True,
                        help="Output path for triage.json")
    parser.add_argument("--production", action="store_true",
                        help="Force full expert review")
    parser.add_argument("--first-run", action="store_true",
                        help="Force full expert review")
    parser.add_argument("--domain-flag", action="store_true",
                        help="Force full expert review (domain explicitly set)")
    args = parser.parse_args()

    try:
        # Load inputs
        inputs = {
            "profile": load_json(args.profile),
            "validation": load_json(args.validation),
            "eda_summary": load_json(args.eda_summary),
            "leaderboard": load_json(args.leaderboard),
            "feature_report": load_json(args.feature_report),
        }

        force_full = args.production or args.first_run or args.domain_flag
        force_light_min = args.new_dataset  # Minimum light review for new datasets

        result = run_triage(args.stage, inputs, force_full=force_full)

        # If new_dataset flag set and would skip, upgrade to light
        if force_light_min and result["complexity_level"] == "skip":
            result["complexity_level"] = "light"
            result["trigger_experts"] = True
            result["reasons"].append("new dataset detected - minimum light expert review")

        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # Append to triage history cache if cache dir specified
        if args.cache_dir:
            cache_dir = Path(args.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            history_path = cache_dir / "triage_history.json"
            history = []
            if history_path.exists():
                try:
                    with open(history_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except (json.JSONDecodeError, OSError):
                    history = []
            history.append(result)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

        # Print JSON result as last line
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error_result = {
            "trigger_experts": False,
            "complexity_level": "skip",
            "score": 0.0,
            "reasons": [f"triage error: {str(e)}"],
            "stage": args.stage,
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
