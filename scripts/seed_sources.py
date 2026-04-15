#!/usr/bin/env python3
"""
DataForge - Seed Sources

Parses references/seed-sources/**/*.md files and populates
~/.claude/dataforge/knowledge/sources.json with the initial whitelist. Each
markdown file groups URLs under `## area: <name> (tier: <tier>)` headers; the
parser walks all files under the seed-sources tree, collects entries, and
writes them as `sources.json` compatible with schema/sources.json.

This is idempotent: reruns preserve existing `last_fetched` / `last_hash` /
`last_status` fields for matching source ids and only adds new entries. Use
`--force` to reset state.

Usage:
    python seed_sources.py
    python seed_sources.py --force
    python seed_sources.py --dry-run
    python seed_sources.py --source <dir>  --target <path to sources.json>

Exit codes: 0 = success, 1 = warnings, 2 = source dir missing
"""
import argparse
import json
import re
import sys
from pathlib import Path


AREA_HEADER_RE = re.compile(
    r"^##\s*area:\s*([a-zA-Z0-9_\-]+)\s*(?:\(tier:\s*([a-zA-Z]+)\))?",
    re.IGNORECASE,
)
URL_LINE_RE = re.compile(r"^\s*[-*]\s*(https?://\S+)")

TTL_BY_TIER = {"official": 7, "research": 14, "blog": 30, "hackathon": 30, "user": 30}


def _default_source() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "seed-sources"


def _default_target() -> Path:
    return Path.home() / ".claude" / "dataforge" / "knowledge" / "sources.json"


def _category_from_path(p: Path, root: Path) -> str:
    rel = p.relative_to(root)
    first = rel.parts[0] if rel.parts else ""
    if first == "libraries":
        return "library"
    if first == "domain":
        return "domain"
    if first == "role":
        return "role"
    return "user"


def _track_from_path(p: Path, root: Path) -> str:
    rel = p.relative_to(root)
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "libraries":
        stem = parts[1].replace(".md", "")
        if stem in ("tabular", "dl", "rag", "common"):
            return stem
    return "tabular"


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _parse_file(p: Path, category: str, track: str):
    entries = []
    current_area = None
    current_tier = "blog"
    for raw in p.read_text(encoding="utf-8").splitlines():
        m = AREA_HEADER_RE.match(raw)
        if m:
            current_area = m.group(1).strip()
            current_tier = (m.group(2) or "blog").lower()
            continue
        um = URL_LINE_RE.match(raw)
        if um and current_area:
            url = um.group(1).strip()
            sid = f"{category}-{current_area}-{_slug(url)[:40]}"
            entries.append({
                "id": sid,
                "url": url,
                "category": category,
                "area": current_area,
                "track": track,
                "tier": current_tier,
                "ttl_days": TTL_BY_TIER.get(current_tier, 30),
                "last_fetched": None,
                "last_hash": None,
                "last_status": "never",
                "enabled": True,
            })
    return entries


def seed(source_root: Path, target_path: Path, force: bool, dry_run: bool) -> dict:
    if not source_root.exists():
        return {"error": f"Source not found: {source_root}", "added": [], "kept": []}

    all_entries = []
    for p in source_root.rglob("*.md"):
        if not p.is_file():
            continue
        cat = _category_from_path(p, source_root)
        trk = _track_from_path(p, source_root)
        all_entries.extend(_parse_file(p, cat, trk))

    existing = {"schema_version": "1.0", "last_global_refresh": None, "sources": []}
    if target_path.exists() and not force:
        try:
            existing = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    by_id = {s["id"]: s for s in existing.get("sources", [])}
    added = []
    for e in all_entries:
        if e["id"] not in by_id:
            by_id[e["id"]] = e
            added.append(e["id"])
        else:
            # Preserve runtime state (last_fetched/hash/status) but update
            # url/tier/ttl if the seed file changed them.
            prev = by_id[e["id"]]
            prev.update({
                "url": e["url"],
                "category": e["category"],
                "area": e["area"],
                "track": e["track"],
                "tier": e["tier"],
                "ttl_days": e["ttl_days"],
            })

    out = {
        "schema_version": "1.0",
        "last_global_refresh": existing.get("last_global_refresh"),
        "sources": sorted(by_id.values(), key=lambda s: (s["category"], s["area"], s["id"])),
    }

    if dry_run:
        return {"dry_run": True, "would_write": str(target_path),
                "added": added, "total": len(out["sources"])}

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return {"target": str(target_path), "added": added, "total": len(out["sources"])}


def main():
    ap = argparse.ArgumentParser(description="Seed DataForge KB sources.json from references")
    ap.add_argument("--source", default="")
    ap.add_argument("--target", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    source_root = Path(args.source).expanduser() if args.source else _default_source()
    target_path = Path(args.target).expanduser() if args.target else _default_target()

    result = seed(source_root, target_path, args.force, args.dry_run)
    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(2)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
