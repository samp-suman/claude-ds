#!/usr/bin/env python3
"""
DataForge MLflow Extension — Experiment Logger

Logs a completed training run to MLflow.

Usage:
    python mlflow_log.py \
        --project-name <name> \
        --model <model_name> \
        --metrics-path <metrics.json> \
        --artifact-path <model.pkl> \
        [--tracking-uri http://localhost:5000]
"""
import argparse
import json
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="DataForge MLflow logger")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--metrics-path", required=True)
    parser.add_argument("--artifact-path", default=None)
    parser.add_argument("--tracking-uri", default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    args = parser.parse_args()

    try:
        import mlflow
    except ImportError:
        print("ERROR: mlflow not installed. Run: pip install mlflow", file=sys.stderr)
        sys.exit(1)

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.project_name)

    with open(args.metrics_path) as f:
        metrics_data = json.load(f)

    with mlflow.start_run(run_name=args.model):
        # Log hyperparameters (if any in metrics JSON)
        params = metrics_data.get("hyperparams", {})
        for k, v in params.items():
            mlflow.log_param(k, v)

        mlflow.log_param("model", args.model)
        mlflow.log_param("problem_type", metrics_data.get("problem_type", "unknown"))
        mlflow.log_param("n_train", metrics_data.get("n_train", 0))
        mlflow.log_param("n_features", metrics_data.get("n_features", 0))

        # Log all numeric metrics
        for k, v in metrics_data.get("metrics", {}).items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(k, v)

        # Log model artifact
        if args.artifact_path and Path(args.artifact_path).exists():
            mlflow.log_artifact(args.artifact_path)

    print(f"Logged run for {args.model} to MLflow at {args.tracking_uri}")
    print(json.dumps({"status": "success", "model": args.model, "tracking_uri": args.tracking_uri}))


if __name__ == "__main__":
    main()
