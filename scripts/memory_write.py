#!/usr/bin/env python3
"""
DataForge — Memory Write Script (Concurrent-Safe)

Writes to memory files using file locking to prevent corruption when
multiple parallel agents write simultaneously.

Usage:
    python memory_write.py \
        --project-dir <project_dir> \
        --file <memory_file> \
        --mode <append|update|merge|reset> \
        --data '<json_string>'

    --file: experiments | decisions | failed_transforms | best_pipelines
    --mode:
        append  — add new item to the top-level array/list
        update  — merge JSON dict into existing top-level dict
        merge   — deep merge (for nested structures)
        reset   — overwrite file with --data content
        append_md — append text to a Markdown file (for decisions.md)

Examples:
    # Log a completed experiment run
    python memory_write.py --project-dir ./my-project --file experiments \\
        --mode append --data '{"run_id": "run_001", "best_model": "lightgbm"}'

    # Add a decision note
    python memory_write.py --project-dir ./my-project --file decisions \\
        --mode append_md --data "## 2026-04-04 -- Chose LightGBM over XGBoost\\nReason: ..."

    # Update best pipelines
    python memory_write.py --project-dir ./my-project --file best_pipelines \\
        --mode append --data '{"problem_type": "regression", "best_model": "ridge"}'
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Platform-safe file locking
try:
    import fcntl

    def _lock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

except ImportError:
    # Windows: use msvcrt
    try:
        import msvcrt

        def _lock(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)

        def _unlock(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

    except Exception:
        # No locking available — proceed without (best effort)
        def _lock(f):
            pass
        def _unlock(f):
            pass


MEMORY_FILES = {
    "experiments": "memory/experiments.json",
    "decisions": "memory/decisions.md",
    "failed_transforms": "memory/failed_transforms.json",
    "best_pipelines": "memory/best_pipelines.json",
}

DEFAULT_STRUCTURES = {
    "experiments": {"schema_version": "1.0", "runs": []},
    "failed_transforms": {"failed_models": [], "failed_transforms": []},
    "best_pipelines": {"best_pipelines": []},
}


def read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, IOError):
        return {}


def write_json_file(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            result[key] = result[key] + val
        else:
            result[key] = val
    return result


def safe_write(path: Path, mode: str, data):
    """Write to file with locking. Retries up to 5 times on lock conflict."""
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(5):
        try:
            if path.suffix == ".md":
                # Markdown file — open in append or write mode
                open_mode = "a" if mode == "append_md" else "w"
                with open(path, open_mode, encoding="utf-8") as f:
                    _lock(f)
                    try:
                        if isinstance(data, str):
                            f.write("\n" + data + "\n")
                        else:
                            f.write("\n" + str(data) + "\n")
                    finally:
                        _unlock(f)
                return

            # JSON file
            existing = read_json_file(path)

            if mode == "reset":
                new_content = data if isinstance(data, dict) else {"data": data}

            elif mode == "append":
                # Find the first list in the existing structure and append to it
                new_content = existing.copy()
                if not new_content:
                    # Initialize from default structure if available
                    file_key = path.stem
                    new_content = DEFAULT_STRUCTURES.get(file_key, {}).copy()

                # Find the primary list key
                list_key = None
                for k, v in new_content.items():
                    if isinstance(v, list):
                        list_key = k
                        break

                if list_key:
                    new_content[list_key] = new_content[list_key] + [data]
                else:
                    # No list found — create a "records" list
                    new_content.setdefault("records", [])
                    new_content["records"].append(data)

            elif mode == "update":
                if isinstance(data, dict):
                    new_content = {**existing, **data}
                else:
                    new_content = existing

            elif mode == "merge":
                new_content = deep_merge(existing, data) if isinstance(data, dict) else existing

            else:
                new_content = existing

            with open(path, "w") as f:
                _lock(f)
                try:
                    json.dump(new_content, f, indent=2)
                finally:
                    _unlock(f)
            return

        except (IOError, OSError) as e:
            if attempt < 4:
                time.sleep(0.1 * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to write after 5 attempts: {e}") from e


def main():
    parser = argparse.ArgumentParser(description="DataForge memory writer")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--file", required=True,
                        help="Memory file: experiments|decisions|failed_transforms|best_pipelines")
    parser.add_argument("--mode", required=True,
                        help="Write mode: append|update|merge|reset|append_md")
    parser.add_argument("--data", required=True, help="JSON string or text to write")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)

    rel_path = MEMORY_FILES.get(args.file)
    if not rel_path:
        print(f"ERROR: Unknown memory file '{args.file}'. "
              f"Choose from: {list(MEMORY_FILES.keys())}", file=sys.stderr)
        sys.exit(1)

    full_path = project_dir / rel_path

    # Parse data
    if args.mode == "append_md":
        data = args.data
    else:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in --data: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        safe_write(full_path, args.mode, data)
        print(json.dumps({"status": "ok", "file": str(full_path), "mode": args.mode}))
    except Exception as e:
        print(f"ERROR: Write failed: {e}", file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
