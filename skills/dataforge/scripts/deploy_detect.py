#!/usr/bin/env python3
"""
DataForge — Deployment Target Detection

Heuristically selects the best deployment target based on problem type,
dataset size, and user flags.

Usage:
    python deploy_detect.py \
        --problem-type <problem_type> \
        [--production] \
        [--model-size-mb <size>] \
        --output <deploy_config.json>

Output: JSON deploy config written to --output path
"""
import argparse
import json
import sys
from pathlib import Path


def detect_target(problem_type: str, production: bool, model_size_mb: float) -> dict:
    """Determine deployment target and configuration."""

    if production:
        target = "fastapi"
        reason = "Production flag set — using FastAPI for REST API deployment"
        port = 8000
        endpoint = "/predict"
    elif problem_type == "time_series":
        target = "streamlit"
        reason = "Time series — using Streamlit for interactive chart exploration"
        port = 8501
        endpoint = None
    elif problem_type == "clustering":
        target = "streamlit"
        reason = "Clustering — Streamlit for cluster visualization dashboard"
        port = 8501
        endpoint = None
    elif model_size_mb > 500:
        target = "fastapi"
        reason = f"Large model ({model_size_mb:.0f}MB) — FastAPI for efficient serving"
        port = 8000
        endpoint = "/predict"
    else:
        target = "streamlit"
        reason = "Default: Streamlit for interactive exploration and demo"
        port = 8501
        endpoint = None

    return {
        "target": target,
        "reason": reason,
        "port": port,
        "endpoint": endpoint,
        "production": production,
        "problem_type": problem_type,
    }


def main():
    parser = argparse.ArgumentParser(description="DataForge deployment target detection")
    parser.add_argument("--problem-type", required=True)
    parser.add_argument("--production", action="store_true", default=False)
    parser.add_argument("--model-size-mb", type=float, default=0.0)
    parser.add_argument("--output", required=True, help="Output deploy_config.json path")
    args = parser.parse_args()

    config = detect_target(args.problem_type, args.production, args.model_size_mb)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Deployment target: {config['target']} (port {config['port']})")
    print(f"Reason: {config['reason']}")
    print(json.dumps(config))


if __name__ == "__main__":
    main()
