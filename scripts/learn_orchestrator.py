#!/usr/bin/env python3
"""
DataForge - Learn Orchestrator

Backend for the `/dataforge-learn` skill. Given the KB meta.json, sources.json,
and user config, decides WHICH researcher agents need to be spawned WITH WHICH
parameters, emits a run-plan JSON the skill consumes to spawn them in parallel
waves (batch <= 10), and writes the run plan to disk so it can be inspected.

This script does NOT spawn agents itself -- that is the skill's job. It only
computes the manifest. Keeping the decision logic in Python (not in a SKILL.md)
makes it testable and keeps SKILL.md short.

Usage:
    python learn_orchestrator.py plan \
        --scope all|library|domain|role \
        [--area <name>] \
        [--force] \
        [--web-search] \
        [--kb-root ~/.claude/dataforge/knowledge] \
        [--config ~/.claude/dataforge/config.json] \
        [--output <plan.json>]

    python learn_orchestrator.py status \
        [--kb-root ~/.claude/dataforge/knowledge]

Exit codes:
    0 - plan written (or nothing to do)
    1 - KB root not found
    2 - invalid scope / arguments
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


TTL_DEFAULTS = {
    "library": 7,
    "domain": 30,
    "role": 30,
    "research": 14,
    "hackathon": 30,
}

AGENT_BY_CATEGORY = {
    "library": "df-researcher-library",
    "domain": "df-researcher-domain",
    "role": "df-researcher-role",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_config(config_path: Path) -> dict:
    cfg = _load_json(config_path, {})
    # Defaults applied in-memory only; not written back.
    cfg.setdefault("refresh_policy", "ttl")
    cfg.setdefault("web_search_fallback", False)
    cfg.setdefault("ttl_days", dict(TTL_DEFAULTS))
    cfg.setdefault("tracked_domains", [])
    cfg.setdefault("tracked_roles", [])
    cfg.setdefault("tracked_libraries", [])
    return cfg


def _is_stale(last_fetched_iso: str, ttl_days: int, now: datetime) -> bool:
    dt = _parse_iso(last_fetched_iso)
    if dt is None:
        return True
    return now - dt >= timedelta(days=ttl_days)


def _meta_area_last_refreshed(meta: dict, category: str, area: str):
    areas = (meta.get("areas") or {}).get(category, {}) or {}
    rec = areas.get(area) or {}
    return rec.get("last_refreshed_at") or rec.get("seeded_at")


def _collect_areas(meta: dict, scope: str, explicit_area: str):
    """Return a flat list of (category, area) pairs we might refresh."""
    out = []
    areas = meta.get("areas") or {}

    if scope == "all":
        for category in ("libraries", "domain", "role"):
            block = areas.get(category, {}) or {}
            for area_key in block.keys():
                cat_singular = "library" if category == "libraries" else category
                out.append((cat_singular, area_key))
        return out

    if scope in ("library", "domain", "role"):
        category_plural = "libraries" if scope == "library" else scope
        block = areas.get(category_plural, {}) or {}
        if explicit_area:
            if explicit_area in block or True:
                out.append((scope, explicit_area))
        else:
            for area_key in block.keys():
                out.append((scope, area_key))
        return out

    return out


def _filter_sources(sources: list, category: str, area: str):
    """Find sources tagged for this (category, area)."""
    matches = []
    for s in sources or []:
        if not s.get("enabled", True):
            continue
        if s.get("category") != category:
            continue
        if s.get("area") != area:
            continue
        matches.append(s)
    return matches


def build_plan(kb_root: Path, config_path: Path, scope: str, explicit_area: str,
               force: bool, web_search: bool) -> dict:
    if not kb_root.exists():
        return {"error": f"KB root not found: {kb_root}"}

    meta = _load_json(kb_root / "meta.json", {})
    sources_file = _load_json(kb_root / "sources.json", {"sources": []})
    sources = sources_file.get("sources", [])
    cfg = _load_config(config_path)

    now = datetime.now(timezone.utc)
    ttl_cfg = cfg.get("ttl_days", TTL_DEFAULTS)

    candidate_areas = _collect_areas(meta, scope, explicit_area)

    spawns = []
    skipped = []

    for category, area in candidate_areas:
        agent_type = AGENT_BY_CATEGORY.get(category)
        if not agent_type:
            continue

        # Staleness: prefer area last_refreshed; fall back to max(source.last_fetched)
        meta_category = "libraries" if category == "library" else category
        last_refreshed = _meta_area_last_refreshed(meta, meta_category, area)
        ttl = int(ttl_cfg.get(category, TTL_DEFAULTS[category]))
        stale = force or _is_stale(last_refreshed, ttl, now)

        area_sources = _filter_sources(sources, category, area)

        if not stale and not force:
            skipped.append({"category": category, "area": area, "reason": "fresh",
                            "last_refreshed_at": last_refreshed, "ttl_days": ttl})
            continue

        if not area_sources and not web_search:
            skipped.append({"category": category, "area": area,
                            "reason": "no_sources_and_no_websearch"})
            continue

        track = "tabular"
        if area_sources:
            track = area_sources[0].get("track", "tabular")

        spawns.append({
            "agent_type": agent_type,
            "category": category,
            "area": area,
            "track": track,
            "sources": area_sources,
            "force": force,
            "web_search": web_search,
            "kb_root": str(kb_root),
            "last_refreshed_at": last_refreshed,
            "ttl_days": ttl,
        })

    # Batch into waves of <= 10 for parallel spawning
    waves = []
    batch_size = 10
    for i in range(0, len(spawns), batch_size):
        waves.append(spawns[i:i + batch_size])

    return {
        "schema_version": "1.0",
        "generated_at": _iso_now(),
        "scope": scope,
        "explicit_area": explicit_area,
        "force": force,
        "web_search": web_search,
        "kb_root": str(kb_root),
        "spawns": spawns,
        "waves": waves,
        "skipped": skipped,
        "summary": {
            "total_candidates": len(candidate_areas),
            "total_spawns": len(spawns),
            "total_waves": len(waves),
            "total_skipped": len(skipped),
        },
    }


def status(kb_root: Path, config_path: Path) -> dict:
    meta = _load_json(kb_root / "meta.json", {})
    cfg = _load_config(config_path)
    ttl_cfg = cfg.get("ttl_days", TTL_DEFAULTS)
    now = datetime.now(timezone.utc)

    report = {"schema_version": "1.0", "checked_at": _iso_now(), "areas": []}
    for category_plural, block in (meta.get("areas") or {}).items():
        category = "library" if category_plural == "libraries" else category_plural
        ttl = int(ttl_cfg.get(category, TTL_DEFAULTS.get(category, 30)))
        for area_key, rec in (block or {}).items():
            last = (rec or {}).get("last_refreshed_at") or (rec or {}).get("seeded_at")
            is_stale = _is_stale(last, ttl, now)
            report["areas"].append({
                "category": category,
                "area": area_key,
                "source": (rec or {}).get("source"),
                "seeded_at": (rec or {}).get("seeded_at"),
                "last_refreshed_at": (rec or {}).get("last_refreshed_at"),
                "ttl_days": ttl,
                "stale": is_stale,
            })
    report["any_stale"] = any(a["stale"] for a in report["areas"])
    return report


def main():
    ap = argparse.ArgumentParser(description="DataForge learn orchestrator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Compute a researcher spawn plan")
    p_plan.add_argument("--scope", default="all", choices=["all", "library", "domain", "role"])
    p_plan.add_argument("--area", default="")
    p_plan.add_argument("--force", action="store_true")
    p_plan.add_argument("--web-search", action="store_true")
    p_plan.add_argument("--kb-root", default=str(Path.home() / ".claude" / "dataforge" / "knowledge"))
    p_plan.add_argument("--config", default=str(Path.home() / ".claude" / "dataforge" / "config.json"))
    p_plan.add_argument("--output", default="")

    p_status = sub.add_parser("status", help="Report KB freshness per area")
    p_status.add_argument("--kb-root", default=str(Path.home() / ".claude" / "dataforge" / "knowledge"))
    p_status.add_argument("--config", default=str(Path.home() / ".claude" / "dataforge" / "config.json"))

    args = ap.parse_args()

    kb_root = Path(args.kb_root).expanduser()
    config_path = Path(args.config).expanduser()

    if args.cmd == "plan":
        plan = build_plan(kb_root, config_path, args.scope, args.area,
                          args.force, args.web_search)
        if "error" in plan:
            print(json.dumps(plan, indent=2))
            sys.exit(1)

        if args.output:
            out = Path(args.output).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        print(json.dumps(plan, indent=2))
        sys.exit(0)

    if args.cmd == "status":
        rep = status(kb_root, config_path)
        print(json.dumps(rep, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
