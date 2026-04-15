#!/usr/bin/env python3
"""
DataForge - Knowledge Query

Read-only backend for `/dataforge-knowledge`. Answers queries against the live
KB at ~/.claude/dataforge/knowledge/.

Subcommands:
    show <area>      - print the full *.live.md file(s) matching <area>
    search <query>   - grep entries across every live file, return ranked JSON
    status           - per-area freshness (source, seeded_at, last_refreshed_at, stale?)
    diff             - show live-vs-seed diff per area (source + entry count delta)

Usage:
    python knowledge_query.py show sklearn
    python knowledge_query.py search "target encoder"
    python knowledge_query.py status
    python knowledge_query.py diff

Exit codes: 0 = success, 1 = no matches, 2 = kb root missing
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


FENCE_RE = re.compile(r"```json knowledge-entry\s*\n(.*?)\n```", re.DOTALL)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

TTL_DEFAULTS = {"library": 7, "domain": 30, "role": 30}


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _parse_entries(text):
    entries = []
    for m in FENCE_RE.finditer(text):
        try:
            entries.append(json.loads(m.group(1)))
        except Exception:
            pass
    return entries


def _walk_live(kb_root: Path):
    for p in kb_root.rglob("*.live.md"):
        if p.is_file():
            yield p


def _category_from_path(rel: Path):
    parts = rel.parts
    if not parts:
        return None
    if parts[0] == "libraries":
        return "library"
    if parts[0] in ("domain", "role", "track", "shared"):
        return parts[0]
    return parts[0]


def cmd_show(kb_root: Path, area: str) -> dict:
    hits = []
    target = area.lower()
    for p in _walk_live(kb_root):
        rel = p.relative_to(kb_root)
        if target in str(rel).lower():
            hits.append({
                "file": str(rel),
                "content": p.read_text(encoding="utf-8"),
            })
    return {"area_query": area, "matches": hits, "count": len(hits)}


def cmd_search(kb_root: Path, query: str) -> dict:
    q = query.lower()
    results = []
    for p in _walk_live(kb_root):
        text = p.read_text(encoding="utf-8")
        entries = _parse_entries(text)
        for e in entries:
            hay = " ".join([
                str(e.get("title", "")),
                str(e.get("summary", "")),
                str(e.get("body", "")),
                " ".join(e.get("tags") or []),
            ]).lower()
            if q in hay:
                results.append({
                    "file": str(p.relative_to(kb_root)),
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "summary": e.get("summary"),
                    "area": e.get("area"),
                    "tier": e.get("tier"),
                    "kind": e.get("kind"),
                    "source_url": e.get("source_url"),
                })
    return {"query": query, "results": results, "count": len(results)}


def cmd_status(kb_root: Path) -> dict:
    meta_path = kb_root / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    now = datetime.now(timezone.utc)
    rows = []
    for plural, block in (meta.get("areas") or {}).items():
        category = "library" if plural == "libraries" else plural
        ttl = TTL_DEFAULTS.get(category, 30)
        for area, rec in (block or {}).items():
            last = (rec or {}).get("last_refreshed_at") or (rec or {}).get("seeded_at")
            dt = _parse_iso(last)
            stale = True if dt is None else (now - dt) >= timedelta(days=ttl)
            rows.append({
                "category": category,
                "area": area,
                "source": (rec or {}).get("source"),
                "seeded_at": (rec or {}).get("seeded_at"),
                "last_refreshed_at": (rec or {}).get("last_refreshed_at"),
                "entry_count": (rec or {}).get("entry_count"),
                "ttl_days": ttl,
                "stale": stale,
            })
    return {
        "kb_root": str(kb_root),
        "checked_at": _iso_now(),
        "last_global_refresh": meta.get("last_global_refresh"),
        "areas": rows,
        "stale_count": sum(1 for r in rows if r["stale"]),
    }


def cmd_diff(kb_root: Path) -> dict:
    """Compare live KB entries to the seed baseline.
    Uses frontmatter `status` field (seed vs researcher) as the label, plus
    entry counts parsed from the live files."""
    rows = []
    for p in _walk_live(kb_root):
        text = p.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        entries = _parse_entries(text)
        rows.append({
            "file": str(p.relative_to(kb_root)),
            "area": fm.get("area"),
            "status": fm.get("status", "unknown"),
            "seeded_at": fm.get("seeded_at"),
            "last_refreshed_at": fm.get("last_refreshed_at"),
            "entry_count": len(entries),
        })
    return {"kb_root": str(kb_root), "files": rows, "total_files": len(rows)}


def main():
    ap = argparse.ArgumentParser(description="DataForge knowledge query backend")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show")
    p_show.add_argument("area")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")

    sub.add_parser("status")
    sub.add_parser("diff")

    ap.add_argument("--kb-root", default=str(Path.home() / ".claude" / "dataforge" / "knowledge"))
    args = ap.parse_args()

    kb_root = Path(args.kb_root).expanduser()
    if not kb_root.exists():
        print(json.dumps({"error": f"KB root not found: {kb_root}"}, indent=2))
        sys.exit(2)

    if args.cmd == "show":
        out = cmd_show(kb_root, args.area)
        print(json.dumps(out, indent=2))
        sys.exit(0 if out["count"] else 1)

    if args.cmd == "search":
        out = cmd_search(kb_root, args.query)
        print(json.dumps(out, indent=2))
        sys.exit(0 if out["count"] else 1)

    if args.cmd == "status":
        out = cmd_status(kb_root)
        print(json.dumps(out, indent=2))
        sys.exit(0)

    if args.cmd == "diff":
        out = cmd_diff(kb_root)
        print(json.dumps(out, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
