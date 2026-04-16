#!/usr/bin/env python3
"""
DataForge — Model Training Script

Trains a single ML model with cross-validation. Saves model artifact (.pkl)
and metrics JSON. Designed to be called in parallel by multiple df-train-model
agents simultaneously.

Usage:
    python train.py \
        --model <model_name> \
        --data <processed_csv_path> \
        --target <target_column> \
        --problem <problem_type> \
        --output-dir <project_dir> \
        [--hyperparams '{"n_estimators": 300}'] \
        [--test-size 0.2]

Supported models:
    Classification: xgboost, lightgbm, randomforest, logistic, catboost, svm_rbf
    Regression:     xgboost, lightgbm, randomforest, linear, ridge, lasso, catboost
    Clustering:     kmeans, dbscan, hierarchical

Exit codes:
    0  Success
    1  Training failed (log to failed_transforms)
    2  Fatal setup error (missing data, bad args)
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


# ── Model Registry ────────────────────────────────────────────────────────────

def get_model(model_name: str, problem_type: str, hyperparams: dict):
    """Return an untrained model instance from the registry."""
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import (
        LogisticRegression, LinearRegression, Ridge, Lasso
    )
    from sklearn.svm import SVC

    hp = hyperparams or {}

    if problem_type in ("binary_classification", "multiclass_classification"):
        registry = {
            "xgboost": lambda: __import__("xgboost").XGBClassifier(
                n_estimators=hp.get("n_estimators", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                max_depth=hp.get("max_depth", 6),
                subsample=hp.get("subsample", 0.8),
                colsample_bytree=hp.get("colsample_bytree", 0.8),
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42,
                n_jobs=-1,
            ),
            "lightgbm": lambda: __import__("lightgbm").LGBMClassifier(
                n_estimators=hp.get("n_estimators", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                max_depth=hp.get("max_depth", -1),
                num_leaves=hp.get("num_leaves", 31),
                min_child_samples=hp.get("min_child_samples", 20),
                subsample=hp.get("subsample", 0.8),
                colsample_bytree=hp.get("colsample_bytree", 0.8),
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            ),
            "randomforest": lambda: RandomForestClassifier(
                n_estimators=hp.get("n_estimators", 200),
                max_depth=hp.get("max_depth", None),
                min_samples_split=hp.get("min_samples_split", 2),
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
            "logistic": lambda: LogisticRegression(
                C=hp.get("C", 1.0),
                max_iter=hp.get("max_iter", 1000),
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
            "catboost": lambda: __import__("catboost").CatBoostClassifier(
                iterations=hp.get("iterations", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                depth=hp.get("depth", 6),
                random_state=42,
                verbose=0,
            ),
            "svm_rbf": lambda: SVC(
                C=hp.get("C", 1.0),
                kernel="rbf",
                probability=True,
                class_weight="balanced",
                random_state=42,
            ),
            "balanced_bagging": lambda: __import__("imblearn.ensemble", fromlist=["BalancedBaggingClassifier"]).BalancedBaggingClassifier(
                n_estimators=hp.get("n_estimators", 100),
                random_state=42,
                n_jobs=-1,
            ),
        }
    elif problem_type == "regression":
        registry = {
            "xgboost": lambda: __import__("xgboost").XGBRegressor(
                n_estimators=hp.get("n_estimators", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                max_depth=hp.get("max_depth", 6),
                subsample=hp.get("subsample", 0.8),
                colsample_bytree=hp.get("colsample_bytree", 0.8),
                random_state=42,
                n_jobs=-1,
            ),
            "lightgbm": lambda: __import__("lightgbm").LGBMRegressor(
                n_estimators=hp.get("n_estimators", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                num_leaves=hp.get("num_leaves", 31),
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            ),
            "randomforest": lambda: RandomForestRegressor(
                n_estimators=hp.get("n_estimators", 200),
                max_depth=hp.get("max_depth", None),
                random_state=42,
                n_jobs=-1,
            ),
            "linear": lambda: LinearRegression(n_jobs=-1),
            "ridge": lambda: Ridge(alpha=hp.get("alpha", 1.0), random_state=42),
            "lasso": lambda: Lasso(alpha=hp.get("alpha", 0.01), max_iter=2000, random_state=42),
            "catboost": lambda: __import__("catboost").CatBoostRegressor(
                iterations=hp.get("iterations", 300),
                learning_rate=hp.get("learning_rate", 0.05),
                depth=hp.get("depth", 6),
                random_state=42,
                verbose=0,
            ),
        }
    else:
        registry = {}  # Clustering handled separately

    if model_name not in registry:
        raise ValueError(
            f"Unknown model '{model_name}' for problem type '{problem_type}'. "
            f"Available: {list(registry.keys())}"
        )
    return registry[model_name]()


def compute_metrics(y_true, y_pred, y_prob, problem_type: str) -> dict:
    """Compute appropriate metrics for the problem type."""
    import numpy as np
    from sklearn.metrics import (
        accuracy_score, f1_score, roc_auc_score, precision_score, recall_score,
        mean_squared_error, mean_absolute_error, r2_score
    )

    metrics = {}

    if problem_type in ("binary_classification", "multiclass_classification"):
        avg = "binary" if problem_type == "binary_classification" else "weighted"
        metrics["accuracy"] = round(float(accuracy_score(y_true, y_pred)), 4)
        metrics["f1"] = round(float(f1_score(y_true, y_pred, average=avg, zero_division=0)), 4)
        metrics["precision"] = round(float(precision_score(y_true, y_pred, average=avg, zero_division=0)), 4)
        metrics["recall"] = round(float(recall_score(y_true, y_pred, average=avg, zero_division=0)), 4)
        if y_prob is not None:
            try:
                if problem_type == "binary_classification":
                    metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob[:, 1])), 4)
                else:
                    metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob, multi_class="ovr")), 4)
            except Exception:
                pass
        metrics["primary_metric"] = "roc_auc" if "roc_auc" in metrics else "f1"

    elif problem_type == "regression":
        mse = float(mean_squared_error(y_true, y_pred))
        metrics["rmse"] = round(float(np.sqrt(mse)), 4)
        metrics["mae"] = round(float(mean_absolute_error(y_true, y_pred)), 4)
        metrics["r2"] = round(float(r2_score(y_true, y_pred)), 4)
        metrics["mse"] = round(mse, 4)
        metrics["primary_metric"] = "r2"

    return metrics


def train_clustering(df, model_name: str, hyperparams: dict, output_dir: Path) -> dict:
    """Train a clustering model (no target column)."""
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    X = df.select_dtypes(include="number").fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    hp = hyperparams or {}

    if model_name == "kmeans":
        # Elbow method: try k = 2..8
        inertias = []
        k_range = range(2, min(9, len(X) // 10 + 2))
        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(X_scaled)
            inertias.append(km.inertia_)
        best_k = hp.get("n_clusters", int(k_range[max(range(len(inertias)), key=lambda i: (
            (inertias[0] - inertias[i]) / (i + 1)
        ))]))
        model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
        metrics = {"n_clusters": best_k, "inertia": round(float(model.inertia_), 4)}

    elif model_name == "dbscan":
        eps = hp.get("eps", 0.5)
        min_samples = hp.get("min_samples", 5)
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X_scaled)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        metrics = {"n_clusters": n_clusters, "eps": eps, "min_samples": min_samples,
                   "noise_points": int((labels == -1).sum())}

    elif model_name == "hierarchical":
        n_clusters = hp.get("n_clusters", 3)
        model = AgglomerativeClustering(n_clusters=n_clusters)
        labels = model.fit_predict(X_scaled)
        metrics = {"n_clusters": n_clusters}

    else:
        raise ValueError(f"Unknown clustering model: {model_name}")

    # Silhouette score
    try:
        from sklearn.metrics import silhouette_score
        n_unique = len(set(labels))
        if n_unique > 1:
            sil = float(silhouette_score(X_scaled, labels))
            metrics["silhouette_score"] = round(sil, 4)
    except Exception:
        pass

    metrics["primary_metric"] = "silhouette_score"

    import joblib
    models_dir = output_dir / "src" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = models_dir / f"{model_name}.pkl"
    joblib.dump({"model": model, "scaler": scaler, "labels": labels}, artifact_path)

    with open(models_dir / f"{model_name}_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics, str(artifact_path)


def main():
    parser = argparse.ArgumentParser(description="DataForge model trainer")
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument("--data", required=True, help="Processed training data path")
    parser.add_argument("--target", default=None, help="Target column name")
    parser.add_argument("--problem", required=True,
                        help="Problem type: binary_classification|multiclass_classification|regression|clustering")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    parser.add_argument("--hyperparams", default="{}", help="JSON string of hyperparameter overrides")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split fraction")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    models_dir = output_dir / "src" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    try:
        hyperparams = json.loads(args.hyperparams)
    except json.JSONDecodeError:
        hyperparams = {}

    # Load data
    try:
        import pandas as pd
        df = pd.read_csv(args.data)
    except Exception as e:
        result = {"agent": "df-train-model", "model": args.model, "status": "failure",
                  "error": f"Cannot load data: {e}"}
        print(json.dumps(result))
        sys.exit(1)

    # Clustering: separate path
    if args.problem == "clustering":
        try:
            metrics, artifact_path = train_clustering(df, args.model, hyperparams, output_dir)
            result = {
                "agent": "df-train-model",
                "model": args.model,
                "status": "success",
                "problem_type": args.problem,
                "metrics": metrics,
                "artifact_path": artifact_path,
                "error": None,
            }
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"agent": "df-train-model", "model": args.model,
                              "status": "failure", "error": str(e)}))
            sys.exit(1)
        return

    # Supervised: prepare X, y
    if not args.target or args.target not in df.columns:
        print(json.dumps({"agent": "df-train-model", "model": args.model,
                          "status": "failure", "error": f"Target '{args.target}' not found"}))
        sys.exit(1)

    import numpy as np
    from sklearn.model_selection import StratifiedKFold, KFold, cross_validate
    from sklearn.preprocessing import LabelEncoder

    X = df.drop(columns=[args.target]).select_dtypes(include="number").fillna(0)
    y = df[args.target]

    # Encode target for classification
    le = None
    if args.problem in ("binary_classification", "multiclass_classification"):
        if y.dtype == "object" or str(y.dtype) == "category":
            le = LabelEncoder()
            y = le.fit_transform(y)
        else:
            y = y.values

    # Train/test split
    from sklearn.model_selection import train_test_split
    if args.problem in ("binary_classification", "multiclass_classification"):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, stratify=y, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42
        )

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42) \
        if args.problem in ("binary_classification", "multiclass_classification") \
        else KFold(n_splits=5, shuffle=True, random_state=42)

    scoring_map = {
        "binary_classification": ["roc_auc", "f1", "accuracy"],
        "multiclass_classification": ["f1_weighted", "accuracy"],
        "regression": ["r2", "neg_mean_absolute_error", "neg_root_mean_squared_error"],
    }
    scoring = scoring_map.get(args.problem, ["accuracy"])

    print(f"Training {args.model} on {len(X_train)} samples with 5-fold CV...", flush=True)

    try:
        model = get_model(args.model, args.problem, hyperparams)
        cv_results = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring,
                                    return_train_score=False, n_jobs=-1)
    except Exception as e:
        result = {"agent": "df-train-model", "model": args.model, "status": "failure", "error": str(e)}
        print(json.dumps(result))
        sys.exit(1)

    # CV summary
    cv_metrics = {}
    for metric_key, values in cv_results.items():
        if metric_key.startswith("test_"):
            metric_name = metric_key[5:]
            if metric_name.startswith("neg_"):
                metric_name = metric_name[4:]
                values = -values
            cv_metrics[f"cv_{metric_name}_mean"] = round(float(np.mean(values)), 4)
            cv_metrics[f"cv_{metric_name}_std"] = round(float(np.std(values)), 4)

    # Fit final model on full training set
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = None
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X_test)
        except Exception:
            pass

    test_metrics = compute_metrics(y_test, y_pred, y_prob, args.problem)
    all_metrics = {**cv_metrics, **test_metrics}

    # Save artifact
    import joblib
    artifact_path = models_dir / f"{args.model}.pkl"
    joblib.dump(model, artifact_path)

    # Save metrics JSON
    metrics_data = {
        "model": args.model,
        "problem_type": args.problem,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_features": len(X.columns),
        "feature_names": list(X.columns),
        "metrics": all_metrics,
        "label_classes": list(le.classes_) if le is not None else None,
    }
    with open(models_dir / f"{args.model}_metrics.json", "w") as f:
        json.dump(metrics_data, f, indent=2)

    # Save CV results for leaderboard
    with open(models_dir / f"{args.model}_cv_results.json", "w") as f:
        json.dump({"model": args.model, "cv_scores": cv_metrics}, f, indent=2)

    primary_metric = all_metrics.get("primary_metric", list(all_metrics.keys())[0])
    primary_value = all_metrics.get(primary_metric, 0.0)

    print(f"{args.model}: {primary_metric}={primary_value}", flush=True)

    result = {
        "agent": "df-train-model",
        "model": args.model,
        "status": "success",
        "problem_type": args.problem,
        "metrics": all_metrics,
        "primary_metric": primary_metric,
        "primary_value": primary_value,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_features": len(X.columns),
        "artifact_path": str(artifact_path),
        "error": None,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
