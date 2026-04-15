---
name: dataforge-learn
description: >
  DataForge knowledge-base refresh skill. Spawns researcher agents in parallel
  waves to fetch updated information from whitelisted sources (library
  changelogs, domain techniques, role thought-leaders), then merges their
  outputs into the live KB at ~/.claude/dataforge/knowledge/. Triggers on:
  "refresh knowledge", "/dataforge-learn", "update KB", "learn libraries".
user-invokable: true
argument-hint: "[all|library|domain|role] [--area <name>] [--source <url>] [--web-search] [--force]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
---

# DataForge - Learn Skill

> Refresh the live knowledge base by spawning researcher agents against the
> whitelisted sources in `~/.claude/dataforge/knowledge/sources.json`.

## Commands

| Command | What it does |
|---------|-------------|
| `/dataforge-learn all` | Refresh every stale area (libraries, domains, roles) |
| `/dataforge-learn library [--area sklearn]` | Refresh one library (or all libraries if no --area) |
| `/dataforge-learn domain [--area finance]` | Refresh one domain (or all domains) |
| `/dataforge-learn role [--area mlops]` | Refresh one role (or all roles) |

Flags:
- `--force` - ignore TTL and refresh even if fresh
- `--web-search` - allow opt-in WebSearch fallback when whitelisted sources yield <3 entries
- `--source <url>` - one-off: inject a user-provided URL for this run only

## Shared Constants

```
SCRIPTS_DIR = ~/.claude/scripts
KB_ROOT     = ~/.claude/dataforge/knowledge
CONFIG      = ~/.claude/dataforge/config.json
```

---

## Step 1 - Parse arguments

Extract:
- `SCOPE` = first positional arg (`all` | `library` | `domain` | `role`); default `all`
- `AREA` = value of `--area` if present, else empty
- `FORCE` = `--force` flag
- `WEB_SEARCH` = `--web-search` flag OR `config.web_search_fallback=true`
- `ONE_OFF_SOURCE` = value of `--source` if present

## Step 2 - Compute the spawn plan

```bash
python3 ~/.claude/scripts/learn_orchestrator.py plan \
  --scope {SCOPE} \
  {--area "{AREA}" if AREA} \
  {--force if FORCE} \
  {--web-search if WEB_SEARCH} \
  --output "{KB_ROOT}/.learn_plan.json"
```

Read the resulting JSON. Report to the user:
- Total spawns
- Total waves
- Any areas skipped (reason: fresh, no_sources, etc.)

If `total_spawns == 0`, print "Nothing to refresh" and stop.

## Step 3 - Execute waves

For each wave in `waves`, spawn all agents in the wave IN PARALLEL in a SINGLE
message. Do NOT spawn one at a time.

For each spawn entry, build the task:

```
Task: Refresh {category} "{area}"
agent_type: {agent_type}
area: {area}
track: {track}
sources: {sources JSON inline}
kb_root: {kb_root}
force: {force}
web_search: {web_search}
```

Use `Agent` with:
- `subagent_type` = `general-purpose` (researcher agents are `.md` agents under `agents/`)
- `description` = `"Refresh {area}"`
- The researcher agents are declared in `agents/df-researcher-{library,domain,role}.md`

After each wave finishes, collect the JSON results from every sub-agent. Keep
a running list `all_results: list[dict]`.

**One-off source handling**: if `ONE_OFF_SOURCE` was provided AND the scope is
a single area, append a synthetic source `{"id": "user-oneoff", "url": ONE_OFF_SOURCE, "tier": "user", "category": SCOPE, "area": AREA}` to that spawn's `sources` before spawning. It is not written to `sources.json`.

## Step 4 - Merge results

Write `all_results` as a JSON array to `{KB_ROOT}/.learn_results.json`, then:

```bash
python3 ~/.claude/scripts/merge_knowledge.py \
  --kb-root "{KB_ROOT}" \
  --results-file "{KB_ROOT}/.learn_results.json"
```

Read the merge summary and report:
- Total entries after merge
- Cross-cutting entries extracted
- Areas updated
- Any unparseable files (warnings)

## Step 5 - Final summary

Print a short summary:

```
DataForge KB refresh complete
- Scope: {SCOPE}
- Waves: {n_waves}
- Researchers spawned: {n_spawns}
- New entries: {sum(r.entries_new)}
- Updated entries: {sum(r.entries_updated)}
- Failed sources: {count}
- Merge: {merge.total_entries} total, {merge.cross_cutting} cross-cutting
```

## Error handling

| Scenario | Action |
|----------|--------|
| KB root missing | Run `python3 ~/.claude/scripts/seed_kb.py` first, then retry |
| No sources.json or empty | Print "no sources configured, run /dataforge-setup" and stop |
| Researcher returns status=failure | Record in summary, continue with others (never abort the wave) |
| Merge returns exit_code=1 (unparseable) | Report warnings, do not fail the overall run |
| All researchers fail | Return non-zero, print "refresh failed - check sources.json URLs" |

## Rules

- Each wave is <= 10 agents in parallel (orchestrator already batches).
- Waves are sequential; agents within a wave are parallel.
- Never spawn researchers directly from here - always read the plan from the orchestrator.
- Do not touch sources.json or meta.json from this skill - merge_knowledge.py owns those writes.
