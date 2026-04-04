#!/usr/bin/env python3
"""
DataForge Kaggle Extension — Dataset Fetcher

Downloads a Kaggle dataset and places it in the project's data/raw/ directory.

Usage:
    python kaggle_fetch.py --dataset owner/dataset-name --output-dir <project_dir>

Requires:
    pip install kaggle
    ~/.kaggle/kaggle.json with API credentials
"""
import argparse
import json
import os
import sys
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="DataForge Kaggle dataset fetcher")
    parser.add_argument("--dataset", required=True, help="Kaggle dataset slug: owner/dataset-name")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    args = parser.parse_args()

    try:
        import kaggle
    except ImportError:
        print("ERROR: kaggle package not installed. Run: pip install kaggle", file=sys.stderr)
        sys.exit(2)

    raw_dir = Path(args.output_dir) / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Kaggle dataset: {args.dataset}")
    try:
        kaggle.api.dataset_download_files(
            args.dataset,
            path=str(raw_dir),
            unzip=True,
        )
    except Exception as e:
        print(f"ERROR: Kaggle download failed: {e}", file=sys.stderr)
        print("Check that ~/.kaggle/kaggle.json exists and has valid credentials.", file=sys.stderr)
        sys.exit(2)

    # Find downloaded files
    files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.parquet"))
    if not files:
        print(f"ERROR: No CSV/Parquet files found after download in {raw_dir}", file=sys.stderr)
        sys.exit(2)

    primary_file = files[0]
    print(f"Downloaded: {primary_file}")
    print(json.dumps({
        "status": "success",
        "raw_path": str(primary_file),
        "all_files": [str(f) for f in files],
    }))


if __name__ == "__main__":
    main()
