#!/usr/bin/env python3
"""
DataForge - Merge Knowledge

Runs after a batch of researcher agents has finished. Walks every
*.live.md file under ~/.claude/dataforge/knowledge/, parses embedded
`json knowledge-entry` fenced blocks, dedupes by id, extracts cross-cutting
insights into shared/cross-cutting.md, rebuilds index.md, and updates
meta.json per-area with last_refreshed_at + source="researcher".

Researcher agents return `source_updates` in their result JSON; this script
ALSO consumes a list of result JSONs (via --results-file) so it can patch
sources.json atomically.

Usage:
    python merge_knowledge.py \
        [--kb-root ~/.claude/dataforge/knowledge] \
        [--results-file <path-to-list-of-researcher-results.json>] \
        [--dry-run]

Exit codes: 0 = success, 1 = partial (some files unparseable), 2 = kb root missing
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


FENCE_RE = re.compile(r"```json knowledge-entry\s*\n(.*?)\n```", re.DOTALL)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    raw = m.group(1)
    out = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _parse_entries(text: str) -> list:
    entries = []
    for m in FENCE_RE.finditer(text):
        try:
            obj = json.loads(m.group(1))
            entries.append(obj)
        except Exception:
            pass
    return entries


def _walk_live_files(kb_root: Path):
    for p in kb_root.rglob("*.live.md"):
        if p.is_file():
            yield p


def _category_area_from_path(p: Path, kb_root: Path):
    rel = p.relative_to(kb_root)
    parts = list(rel.parts)
    if not parts:
        return (None, None)
    cat = parts[0]
    if cat == "libraries":
        if len(parts) >= 3:
            area = parts[-1].replace(".live.md", "")
            return ("library", area)
        return ("library", parts[-1].replace(".live.md", ""))
    if cat in ("domain", "role"):
        if len(parts) >= 3:
            return (cat, parts[1])
        return (cat, parts[-1].replace(".live.md", ""))
    if cat == "shared":
        return ("shared", parts[-1].replace(".live.md", ""))
    return (cat, parts[-1].replace(".live.md", ""))


def dedupe_entries(entries: list) -> list:
    seen = {}
    for e in entries:
        eid = e.get("id")
        if not eid:
            eid = hashlib.sha1(
                (e.get("area", "") + "|" + e.get("title", "")).encode("utf-8")
            ).hexdigest()[:12]
            e["id"] = eid
        prev = seen.get(eid)
        if prev is None:
            seen[eid] = e
            continue
        # Keep the one with the later added_date
        prev_dt = prev.get("added_date", "")
        new_dt = e.get("added_date", "")
        if new_dt > prev_dt:
            seen[eid] = e
    return list(seen.values())


def extract_cross_cutting(entries: list) -> list:
    """Pick entries tagged with kind in {deprecation, pitfall} or
    applies_to='all' so they can live in shared/cross-cutting.md."""
    out = []
    for e in entries:
        kind = e.get("kind")
        if kind in ("deprecation", "pitfall"):
            out.append(e)
        elif "cross-cutting" in (e.get("tags") or []):
            out.append(e)
    return out


def rebuild_index(kb_root: Path, per_area: dict) -> None:
    lines = ["# DataForge Knowledge Base - Index",
             "",
             f"_Generated at {_iso_now()}_",
             "",
             "One-line summary per area. See individual `*.live.md` files for full entries.",
             ""]
    for category in sorted(per_area.keys()):
        lines.append(f"## {category}")
        lines.append("")
        for area in sorted(per_area[category].keys()):
            info = per_area[category][area]
            cnt = info["entry_count"]
            src = info["source"]
            refreshed = info.get("last_refreshed_at") or info.get("seeded_at") or "-"
            lines.append(f"- **{area}** - {cnt} entries (source={src}, refreshed={refreshed})")
        lines.append("")
    (kb_root / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_cross_cutting(kb_root: Path, cross: list) -> None:
    shared_dir = kb_root / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    out_path = shared_dir / "cross-cutting.md"

    lines = ["---",
             "area: cross-cutting",
             "category: shared",
             f"last_refreshed_at: \"{_iso_now()}\"",
             "status: generated",
             f"entry_count: {len(cross)}",
             "---",
             "",
             "# Cross-Cutting Knowledge",
             "",
             "Deprecations and pitfalls that apply across areas. Regenerated from live entries on every merge.",
             ""]
    for e in cross:
        lines.append(f"## [{e.get('id','-')}] {e.get('title','-')}")
        lines.append(f"**Area:** {e.get('area','-')} | **Kind:** {e.get('kind','-')} | **Tier:** {e.get('tier','-')}")
        lines.append("")
        lines.append(e.get("summary", ""))
        if e.get("deprecation_replaces"):
            lines.append(f"**Replaces:** `{e['deprecation_replaces']}`")
        if e.get("source_url"):
            lines.append(f"_Source:_ {e['source_url']}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def update_meta(kb_root: Path, per_area: dict) -> None:
    meta_path = kb_root / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    meta.setdefault("schema_version", "1.0")
    meta.setdefault("areas", {"libraries": {}, "track": {}, "domain": {}, "role": {}})
    now = _iso_now()
    meta["last_global_refresh"] = now

    for category, areas in per_area.items():
        plural = "libraries" if category == "library" else category
        if plural not in meta["areas"]:
            meta["areas"][plural] = {}
        for area, info in areas.items():
            rec = meta["areas"][plural].get(area, {})
            rec["source"] = info["source"]
            rec["last_refreshed_at"] = now if info["source"] == "researcher" else rec.get("last_refreshed_at")
            rec.setdefault("seeded_at", info.get("seeded_at"))
            rec["entry_count"] = info["entry_count"]
            meta["areas"][plural][area] = rec

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def patch_sources(kb_root: Path, source_updates: list) -> None:
    if not source_updates:
        return
    sources_path = kb_root / "sources.json"
    if not sources_path.exists():
        return
    try:
        data = json.loads(sources_path.read_text(encoding="utf-8"))
    except Exception:
        return
    by_id = {u.get("id"): u for u in source_updates if u.get("id")}
    for s in data.get("sources", []):
        sid = s.get("id")
        if sid in by_id:
            u = by_id[sid]
            s["last_fetched"] = u.get("last_fetched", s.get("last_fetched"))
            s["last_hash"] = u.get("last_hash", s.get("last_hash"))
            s["last_status"] = u.get("last_status", s.get("last_status", "ok"))
    data["last_global_refresh"] = _iso_now()
    sources_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run(kb_root: Path, results_file: Path, dry_run: bool) -> dict:
    if not kb_root.exists():
        return {"error": f"KB root not found: {kb_root}", "exit_code": 2}

    per_area = {}
    all_entries = []
    unparseable = []

    for live in _walk_live_files(kb_root):
        try:
            text = live.read_text(encoding="utf-8")
        except Exception as e:
            unparseable.append({"file": str(live), "error": str(e)})
            continue
        fm = _parse_frontmatter(text)
        entries = _parse_entries(text)
        entries = dedupe_entries(entries)
        category, area = _category_area_from_path(live, kb_root)
        if not category or not area:
            continue
        per_area.setdefault(category, {})
        per_area[category][area] = {
            "entry_count": len(entries),
            "source": fm.get("status") or "seed",
            "seeded_at": fm.get("seeded_at"),
            "last_refreshed_at": fm.get("last_refreshed_at"),
            "file": str(live.relative_to(kb_root)),
        }
        all_entries.extend(entries)

    all_entries = dedupe_entries(all_entries)
    cross = extract_cross_cutting(all_entries)

    if dry_run:
        return {
            "dry_run": True,
            "per_area_count": {c: len(a) for c, a in per_area.items()},
            "total_entries": len(all_entries),
            "cross_cutting": len(cross),
            "unparseable": unparseable,
        }

    write_cross_cutting(kb_root, cross)
    rebuild_index(kb_root, per_area)
    update_meta(kb_root, per_area)

    # Consume researcher result file (list of result objects)
    if results_file and results_file.exists():
        try:
            results = json.loads(results_file.read_text(encoding="utf-8"))
            all_updates = []
            for r in results if isinstance(results, list) else [results]:
                for u in r.get("source_updates", []) or []:
                    all_updates.append(u)
            patch_sources(kb_root, all_updates)
        except Exception as e:
            unparseable.append({"file": str(results_file), "error": str(e)})

    return {
        "kb_root": str(kb_root),
        "total_entries": len(all_entries),
        "cross_cutting": len(cross),
        "areas_updated": sum(len(a) for a in per_area.values()),
        "unparseable": unparseable,
        "exit_code": 0 if not unparseable else 1,
    }


def main():
    ap = argparse.ArgumentParser(description="Merge researcher outputs into the live KB")
    ap.add_argument("--kb-root", default=str(Path.home() / ".claude" / "dataforge" / "knowledge"))
    ap.add_argument("--results-file", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    kb_root = Path(args.kb_root).expanduser()
    results_file = Path(args.results_file).expanduser() if args.results_file else None

    result = run(kb_root, results_file, args.dry_run)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(result.get("exit_code", 0) if isinstance(result, dict) else 0)


if __name__ == "__main__":
    main()
