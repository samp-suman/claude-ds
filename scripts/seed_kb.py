#!/usr/bin/env python3
"""
DataForge - Knowledge Base Seeder

Modular loader that copies seed knowledge from the repo's
references/seed-knowledge/ tree into the user's live KB at
~/.claude/dataforge/knowledge/, naming the destinations as *.live.md.

This is the bootstrap step that gives every fresh install some baseline
domain/role/library knowledge BEFORE researcher agents have run.

The same script is also used to RE-seed (`--force`) when the seed files
are updated by a DataForge upgrade. Researcher refresh always wins over
seeds in the loader precedence (project snapshot > live KB > seed fallback).

Usage:
    python seed_kb.py                  # copy missing files only
    python seed_kb.py --force          # overwrite existing live files
    python seed_kb.py --dry-run        # report what would change
    python seed_kb.py --target <dir>   # custom KB root (default ~/.claude/dataforge/knowledge)
    python seed_kb.py --source <dir>   # custom seed root (default repo references/seed-knowledge)

Exit codes: 0 = success, 1 = warnings, 2 = source not found.
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def _default_source() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "seed-knowledge"


def _default_target() -> Path:
    return Path.home() / ".claude" / "dataforge" / "knowledge"


def _seed_dest_name(seed_path: Path, source_root: Path) -> Path:
    """Map references/seed-knowledge/<area>/<file>.md to <area>/<stem>.live.md."""
    rel = seed_path.relative_to(source_root)
    parts = list(rel.parts)
    fname = parts[-1]
    if fname.endswith(".md") and not fname.endswith(".live.md"):
        parts[-1] = fname[:-3] + ".live.md"
    return Path(*parts)


def _walk_seeds(source_root: Path):
    for p in source_root.rglob("*.md"):
        if p.is_file():
            yield p


def _update_meta(target_root: Path, copied: list) -> None:
    meta_path = target_root / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    else:
        meta = {}

    meta.setdefault("schema_version", "1.0")
    meta.setdefault("areas", {"libraries": {}, "track": {}, "domain": {}, "role": {}})
    now = datetime.now(timezone.utc).isoformat()
    meta["last_seed_at"] = now
    meta["seed_file_count"] = len(copied)

    # Walk copied paths and record per-area seed timestamps so freshness checks
    # know "this came from a seed, not a researcher".
    for rel in copied:
        parts = rel.parts
        if len(parts) < 2:
            continue
        category = parts[0]  # libraries|track|domain|role|shared
        if category not in meta["areas"]:
            meta["areas"][category] = {}
        # Area key is the file stem (e.g. `sklearn` for libraries/tabular/sklearn.live.md)
        # for libraries, and the parent directory (e.g. `finance` for
        # domain/finance/techniques.live.md) for domain/role where files share a name.
        stem = parts[-1].replace(".live.md", "")
        if category == "libraries":
            area_key = stem
        elif category in ("domain", "role") and len(parts) >= 3:
            area_key = parts[1]
        else:
            area_key = "/".join(parts[1:-1]) or stem
        meta["areas"][category][area_key] = {
            "seeded_at": now,
            "last_refreshed_at": None,
            "source": "seed",
        }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def seed(source_root: Path, target_root: Path, force: bool, dry_run: bool) -> dict:
    if not source_root.exists():
        return {"error": f"Source not found: {source_root}", "copied": [], "skipped": []}

    target_root.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []
    for seed_file in _walk_seeds(source_root):
        rel_dest = _seed_dest_name(seed_file, source_root)
        dest = target_root / rel_dest

        if dest.exists() and not force:
            skipped.append(str(rel_dest))
            continue

        if dry_run:
            copied.append(rel_dest)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed_file, dest)
        copied.append(rel_dest)

    if not dry_run and copied:
        _update_meta(target_root, copied)

    return {
        "source_root": str(source_root),
        "target_root": str(target_root),
        "copied": [str(p) for p in copied],
        "skipped": skipped,
        "force": force,
        "dry_run": dry_run,
    }


def main():
    ap = argparse.ArgumentParser(description="Seed DataForge knowledge base from repo references")
    ap.add_argument("--source", help="Override source dir (default: repo references/seed-knowledge)")
    ap.add_argument("--target", help="Override target dir (default: ~/.claude/dataforge/knowledge)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing *.live.md files")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be copied without writing")
    ap.add_argument("--quiet", action="store_true", help="Print summary only")
    args = ap.parse_args()

    source_root = Path(args.source).expanduser() if args.source else _default_source()
    target_root = Path(args.target).expanduser() if args.target else _default_target()

    result = seed(source_root, target_root, args.force, args.dry_run)

    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(2)

    if args.quiet:
        print(f"copied={len(result['copied'])} skipped={len(result['skipped'])} target={target_root}")
    else:
        print(json.dumps(result, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
