#!/usr/bin/env python3
"""
DataForge — Hyperparameter Tuning

Performs RandomizedSearchCV or Optuna-based HPT on a specified model.

Usage:
    python hpt.py --model <name> --data <path> --target <col> \
        --output-dir <dir> [--n-trials 30] [--cv 5]

Output:
    - {output_dir}/src/models/{model}_best_params.json
    - Updates {output_dir}/memory/best_pipelines.json with best params and score
    - Prints leaderboard comparison

Supported models: xgboost, lightgbm, randomforest, ridge, lasso, logistic

Exit code: 0 = success, 1 = error
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


def get_search_space(model: str, problem_type: str):
    """Define Optuna search space per model type."""
    if model == "xgboost":
        return {
            "n_estimators": (100, 600),
            "learning_rate": (0.01, 0.3),
            "max_depth": (3, 10),
            "subsample": (0.5, 1.0),
            "colsample_bytree": (0.5, 1.0),
            "min_child_weight": (1, 10),
        }
    elif model == "lightgbm":
        return {
            "n_estimators": (100, 600),
            "learning_rate": (0.01, 0.3),
            "max_depth": (-1, 15),
            "num_leaves": (15, 200),
            "min_child_samples": (5, 50),
            "subsample": (0.5, 1.0),
            "colsample_bytree": (0.5, 1.0),
        }
    elif model == "randomforest":
        return {
            "n_estimators": (100, 500),
            "max_depth": (5, 50),
            "min_samples_split": (2, 20),
            "min_samples_leaf": (1, 10),
        }
    elif model in ("ridge", "lasso"):
        return {
            "alpha": (0.001, 100),
        }
    elif model == "logistic":
        return {
            "C": (0.001, 10),
            "max_iter": (1000, 5000),
        }
    return {}


def tune_with_randomsearch(X_train, X_test, y_train, y_test, model, param_dist, cv=5):
    """Tune using RandomizedSearchCV (sklearn fallback)."""
    from sklearn.model_selection import RandomizedSearchCV
    from sklearn.metrics import roc_auc_score, mean_squared_error

    # Get model factory
    clf = _get_model_instance(model, {})
    if clf is None:
        return None, None

    # RandomizedSearchCV
    search = RandomizedSearchCV(
        clf, param_distributions=param_dist, n_iter=30, cv=cv,
        scoring='roc_auc' if hasattr(clf, 'predict_proba') else 'r2',
        n_jobs=-1, verbose=1
    )
    search.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = search.predict(X_test)
    if hasattr(search.best_estimator_, 'predict_proba'):
        y_pred_proba = search.best_estimator_.predict_proba(X_test)[:, 1]
        test_score = roc_auc_score(y_test, y_pred_proba)
    else:
        test_score = mean_squared_error(y_test, y_pred, squared=False)

    return search.best_params_, test_score


def _get_model_instance(model_name: str, hyperparams: dict):
    """Get model instance with given hyperparams."""
    try:
        if model_name == "xgboost":
            from xgboost import XGBClassifier
            return XGBClassifier(**{k: v for k, v in hyperparams.items()}, random_state=42, verbosity=0)
        elif model_name == "lightgbm":
            from lightgbm import LGBMClassifier
            return LGBMClassifier(**{k: v for k, v in hyperparams.items()}, random_state=42, verbose=-1)
        elif model_name == "randomforest":
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(**{k: v for k, v in hyperparams.items()}, n_jobs=-1, random_state=42)
        elif model_name == "ridge":
            from sklearn.linear_model import Ridge
            return Ridge(**{k: v for k, v in hyperparams.items()})
        elif model_name == "lasso":
            from sklearn.linear_model import Lasso
            return Lasso(**{k: v for k, v in hyperparams.items()}, max_iter=10000)
        elif model_name == "logistic":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(**{k: v for k, v in hyperparams.items()}, n_jobs=-1, random_state=42)
    except ImportError:
        return None

    return None


def tune_model(model: str, data_path: str, target: str, output_dir: str, n_trials: int = 30, cv: int = 5):
    """Main HPT function."""
    import pandas as pd
    from sklearn.model_selection import train_test_split, cross_validate

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        df = load_df(data_path)
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}", file=sys.stderr)
        return False

    if target not in df.columns:
        print(f"ERROR: Target column '{target}' not found", file=sys.stderr)
        return False

    # Prepare data
    X = df.drop(columns=[target])
    y = df[target]

    # Numeric only for now (simple path)
    X = X.select_dtypes(include=['number'])
    X = X.fillna(X.median())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Get search space
    search_space = get_search_space(model, "classification")
    if not search_space:
        print(f"ERROR: Unknown model '{model}'", file=sys.stderr)
        return False

    # Convert to RandomizedSearchCV format
    param_dist = {
        k: list(range(v[0], min(v[1], v[0] + 20)))
        if isinstance(v, tuple) and isinstance(v[0], int)
        else v
        for k, v in search_space.items()
    }

    # Run HPT
    print(f"[HPT] Tuning {model} with {n_trials} trials...")
    best_params, test_score = tune_with_randomsearch(X_train, X_test, y_train, y_test, model, param_dist, cv=cv)

    if best_params is None:
        print(f"ERROR: HPT failed for model {model}", file=sys.stderr)
        return False

    # Save best params
    src_dir = output_dir / "src" / "models"
    src_dir.mkdir(parents=True, exist_ok=True)

    best_params_file = src_dir / f"{model}_best_params.json"
    with open(best_params_file, "w") as f:
        json.dump({
            "model": model,
            "best_params": best_params,
            "test_score": float(test_score),
            "cv_folds": cv,
            "n_trials": n_trials,
        }, f, indent=2)

    print(f"[HPT] Best params saved to {best_params_file}", file=sys.stderr)
    print(f"[HPT] Test score: {test_score:.4f}", file=sys.stderr)

    # Update best_pipelines.json
    memory_dir = output_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    best_pipelines_file = memory_dir / "best_pipelines.json"
    try:
        if best_pipelines_file.exists():
            with open(best_pipelines_file, "r") as f:
                pipelines = json.load(f)
        else:
            pipelines = []

        # Find and update or add entry for this model
        entry = next((p for p in pipelines if p.get("model") == model), None)
        if entry:
            entry["hyperparams"] = best_params
            entry["score"] = test_score
            entry["timestamp"] = str(pd.Timestamp.utcnow())
        else:
            pipelines.append({
                "model": model,
                "hyperparams": best_params,
                "score": test_score,
                "timestamp": str(pd.Timestamp.utcnow()),
            })

        with open(best_pipelines_file, "w") as f:
            json.dump(pipelines, f, indent=2)

        print(f"[HPT] Updated memory/best_pipelines.json", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to update best_pipelines.json: {e}", file=sys.stderr)

    return True


def main():
    parser = argparse.ArgumentParser(description="DataForge Hyperparameter Tuning")
    parser.add_argument("--model", required=True, help="Model name (xgboost, lightgbm, randomforest, ridge, lasso, logistic)")
    parser.add_argument("--data", required=True, help="Path to dataset (CSV/Parquet)")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    parser.add_argument("--n-trials", type=int, default=30, help="Number of HPT trials")
    parser.add_argument("--cv", type=int, default=5, help="K-fold cross-validation folds")

    args = parser.parse_args()

    success = tune_model(
        model=args.model,
        data_path=args.data,
        target=args.target,
        output_dir=args.output_dir,
        n_trials=args.n_trials,
        cv=args.cv,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
