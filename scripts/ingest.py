#!/usr/bin/env python3
"""
DataForge — Data Ingestion Script

Loads data from any supported source into the project's data/raw/ directory.
Outputs a raw profile JSON with shape, dtypes, and null statistics.

Usage:
    python ingest.py --source <path_or_uri> --output-dir <project_dir>

Exit codes:
    0  Success
    1  Warning (partial load, some issues)
    2  Fatal error (cannot proceed)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse


def detect_format(source: str) -> str:
    """Detect data source format from path/URI."""
    s = source.lower()
    if s.startswith("sqlite:///") or s.startswith("postgresql://") or s.startswith("mysql://"):
        return "database"
    if s.startswith("http://") or s.startswith("https://"):
        return "url"
    if s.startswith("kaggle:"):
        return "kaggle"
    ext = Path(source).suffix.lower()
    fmt_map = {
        ".csv": "csv", ".tsv": "tsv",
        ".json": "json", ".jsonl": "jsonl",
        ".parquet": "parquet", ".pq": "parquet",
        ".xlsx": "excel", ".xls": "excel",
        ".db": "sqlite", ".sqlite": "sqlite", ".sqlite3": "sqlite",
        ".pkl": "pickle", ".pickle": "pickle",
    }
    if ext in fmt_map:
        return fmt_map[ext]
    return "unknown"


def load_data(source: str, fmt: str):
    """Load data from source into a pandas DataFrame."""
    import pandas as pd

    if fmt == "csv":
        return pd.read_csv(source)
    if fmt == "tsv":
        return pd.read_csv(source, sep="\t")
    if fmt == "json":
        return pd.read_json(source)
    if fmt == "jsonl":
        return pd.read_json(source, lines=True)
    if fmt == "parquet":
        return pd.read_parquet(source)
    if fmt == "excel":
        return pd.read_excel(source)
    if fmt == "sqlite":
        import sqlite3
        conn = sqlite3.connect(source)
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        if tables.empty:
            raise ValueError("No tables found in SQLite database.")
        table_name = tables.iloc[0]["name"]
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        return df
    if fmt == "database":
        from sqlalchemy import create_engine, text, inspect
        # Extract table name from URI query param if present
        # e.g., sqlite:///db.sqlite?table=users
        table_match = re.search(r"\?table=([^&]+)", source)
        clean_uri = re.sub(r"\?.*$", "", source)
        engine = create_engine(clean_uri)
        inspector = inspect(engine)
        if table_match:
            table_name = table_match.group(1)
        else:
            tables = inspector.get_table_names()
            if not tables:
                raise ValueError("No tables found in database.")
            table_name = tables[0]
        import pandas as pd
        with engine.connect() as conn:
            return pd.read_sql(text(f"SELECT * FROM {table_name}"), conn)
    if fmt == "url":
        import pandas as pd
        url_lower = source.lower()
        if ".csv" in url_lower:
            return pd.read_csv(source)
        if ".parquet" in url_lower:
            return pd.read_parquet(source)
        if ".json" in url_lower:
            return pd.read_json(source)
        # Default: try CSV
        return pd.read_csv(source)
    if fmt == "pickle":
        import pandas as pd
        return pd.read_pickle(source)
    raise ValueError(
        f"Unsupported format '{fmt}'. Supported: CSV, TSV, JSON, JSONL, Parquet, "
        "Excel (.xlsx/.xls), SQLite (.db/.sqlite), SQLAlchemy URI, HTTP URL, Pickle."
    )


def compute_hash(path: str) -> str:
    """Compute SHA-256 of a file for change detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()[:16]}"


def build_raw_profile(df, source_path: str) -> dict:
    """Build a lightweight profile of the raw dataframe."""
    import numpy as np

    null_pct = (df.isnull().sum() / len(df) * 100).round(2).to_dict()
    unique_counts = df.nunique().to_dict()
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Detect datetime columns
    datetime_cols = []
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            datetime_cols.append(col)
        elif str(df[col].dtype) == "object":
            sample = df[col].dropna().head(10).astype(str)
            date_pattern = re.compile(
                r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}"
            )
            if sample.apply(lambda x: bool(date_pattern.search(x))).mean() > 0.7:
                datetime_cols.append(col)

    # Detect potential ID columns (high cardinality integer/object)
    id_like_cols = []
    for col in df.columns:
        uniq_ratio = df[col].nunique() / len(df)
        if uniq_ratio > 0.95 and len(df) > 100:
            id_like_cols.append(col)

    return {
        "source": source_path,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "dtypes": dtypes,
        "null_pct": null_pct,
        "unique_counts": unique_counts,
        "datetime_cols": datetime_cols,
        "id_like_cols": id_like_cols,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="DataForge data ingestion")
    parser.add_argument("--source", required=True, help="Data source path or URI")
    parser.add_argument("--output-dir", required=True, help="Project root directory")
    parser.add_argument("--table", default=None, help="Table name (for DB sources)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    raw_dir = output_dir / "data" / "raw"
    interim_dir = output_dir / "data" / "interim"
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    source = args.source
    fmt = detect_format(source)

    if fmt == "unknown":
        print(
            f"ERROR: Cannot detect format for '{source}'.\n"
            "Supported: .csv, .tsv, .json, .jsonl, .parquet, .xlsx, .xls, "
            ".db, .sqlite, sqlite:/// URI, http(s):// URL, .pkl",
            file=sys.stderr,
        )
        sys.exit(2)

    if fmt == "kaggle":
        print(
            "ERROR: Kaggle sources require the kaggle extension.\n"
            "Run: python ~/.claude/skills/dataforge/extensions/kaggle/scripts/kaggle_fetch.py "
            f"--dataset '{source[7:]}' --output-dir '{output_dir}'",
            file=sys.stderr,
        )
        sys.exit(2)

    print(f"Loading data from: {source} (format: {fmt})")

    try:
        df = load_data(source, fmt)
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Loaded: {len(df):,} rows × {len(df.columns)} columns")

    # Copy / save raw file
    if fmt in ("csv", "tsv", "json", "jsonl", "parquet", "excel", "sqlite", "pickle"):
        raw_filename = Path(source).name
        raw_dest = raw_dir / raw_filename
        if Path(source).exists():
            shutil.copy2(source, raw_dest)
        else:
            # URL or computed — save as parquet
            raw_filename = Path(source.split("/")[-1].split("?")[0]).stem + ".parquet"
            raw_dest = raw_dir / raw_filename
            df.to_parquet(raw_dest, index=False)
    else:
        # Database / URL — save as parquet
        stem = re.sub(r"[^\w]", "_", source)[:40]
        raw_filename = f"{stem}.parquet"
        raw_dest = raw_dir / raw_filename
        df.to_parquet(raw_dest, index=False)

    file_hash = compute_hash(str(raw_dest)) if raw_dest.exists() else "n/a"

    # Build and save raw profile
    profile = build_raw_profile(df, str(raw_dest))
    profile["file_hash"] = file_hash
    profile["raw_filename"] = raw_filename

    profile_path = interim_dir / "profile_raw.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Raw data saved to: {raw_dest}")
    print(f"Profile saved to:  {profile_path}")
    print(json.dumps({"status": "success", "raw_path": str(raw_dest), "profile_path": str(profile_path), **profile}))


if __name__ == "__main__":
    main()
