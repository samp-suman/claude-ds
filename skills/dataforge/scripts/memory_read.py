#!/usr/bin/env python3
"""
DataForge — Memory Read Script

Reads memory files from a DataForge project directory and prints them
as a consolidated JSON blob for the orchestrator to consume.

Usage:
    python memory_read.py --project-dir <project_dir> [--file <memory_file>]

    --file: experiments | decisions | failed_transforms | best_pipelines | all (default)

Output: JSON printed to stdout
"""
import argparse
import json
import sys
from pathlib import Path


MEMORY_FILES = {
    "experiments": "memory/experiments.json",
    "decisions": "memory/decisions.md",
    "failed_transforms": "memory/failed_transforms.json",
    "best_pipelines": "memory/best_pipelines.json",
}


def read_json_memory(path: Path) -> dict:
    """Read a JSON memory file, return empty structure if missing or corrupt."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def read_md_memory(path: Path) -> str:
    """Read a Markdown memory file, return empty string if missing."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except IOError:
        return ""


def main():
    parser = argparse.ArgumentParser(description="DataForge memory reader")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--file", default="all",
                        help="Memory file to read: experiments|decisions|failed_transforms|best_pipelines|all")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    memory_dir = project_dir / "memory"

    if not memory_dir.exists():
        print(json.dumps({"status": "no_memory", "message": "Memory directory does not exist yet."}))
        return

    result = {"status": "ok", "project_dir": str(project_dir)}

    files_to_read = MEMORY_FILES if args.file == "all" else {
        args.file: MEMORY_FILES.get(args.file, f"memory/{args.file}.json")
    }

    for key, rel_path in files_to_read.items():
        full_path = project_dir / rel_path
        if rel_path.endswith(".json"):
            result[key] = read_json_memory(full_path)
        elif rel_path.endswith(".md"):
            result[key] = read_md_memory(full_path)
        else:
            result[key] = None

    # Extract useful summary for orchestrator
    experiments = result.get("experiments", {})
    best_pipelines = result.get("best_pipelines", {})
    failed_transforms = result.get("failed_transforms", {})

    runs = experiments.get("runs", []) if isinstance(experiments, dict) else []
    pipelines = best_pipelines.get("best_pipelines", []) if isinstance(best_pipelines, dict) else []
    failed_models = failed_transforms.get("failed_models", []) if isinstance(failed_transforms, dict) else []

    result["summary"] = {
        "n_past_runs": len(runs),
        "n_best_pipelines": len(pipelines),
        "n_failed_models": len(failed_models),
        "last_best_model": runs[-1].get("best_model") if runs else None,
        "last_best_metric": runs[-1].get("best_metric") if runs else None,
        "skip_models": [m["model"] for m in failed_models if m.get("skip_in_future")],
        "seed_hyperparams": pipelines[0].get("hyperparams") if pipelines else {},
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
