---
name: df-knowledge
description: >
  DataForge read-only knowledge-base query skill. Inspect, search, and diff the
  live knowledge base at ~/.claude/dataforge/knowledge/. Triggers on:
  "show knowledge", "/df-knowledge", "KB status", "what does DataForge
  know about".
user-invokable: true
argument-hint: "[show|search|status|diff] [area|query]"
allowed-tools:
  - Read
  - Bash
---

# DataForge - Knowledge Query Skill

> Read-only inspection of the live knowledge base. Never modifies the KB -
> use `/df-learn` for that.

## Commands

| Command | What it does |
|---------|-------------|
| `/df-knowledge show <area>` | Print the full live markdown for one area (e.g. `sklearn`, `finance`) |
| `/df-knowledge search <query>` | Search entries across every live file by title/summary/body |
| `/df-knowledge status` | Per-area freshness report: source, seeded_at, last_refreshed_at, stale? |
| `/df-knowledge diff` | Show which files are seed-sourced vs researcher-sourced, with entry counts |

---

## Shared Constants

```
SCRIPTS_DIR = ~/.claude/scripts
KB_ROOT     = ~/.claude/dataforge/knowledge
```

## Step 1 - Parse subcommand

Extract the first positional: `show`, `search`, `status`, or `diff`.
- For `show`, second positional = area name
- For `search`, second positional = query string (preserve spaces)

## Step 2 - Delegate to the query backend

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/knowledge_query.py {subcommand} {arg} \
  --kb-root "{KB_ROOT}"
```

## Step 3 - Render the result

- `show`: print each matched file's content as a fenced block
- `search`: render a table `area | id | title | tier | source_url`
- `status`: render a table `category | area | source | last_refreshed | stale`; highlight any `stale=true` rows
- `diff`: render a table `file | status | entry_count | last_refreshed_at`

## Error handling

| Scenario | Action |
|----------|--------|
| KB root missing | Instruct: `bash install.sh` then `~/.claude/dataforge/dfpython ~/.claude/scripts/seed_kb.py` |
| No matches for `show`/`search` | Print "No matches" and exit 1 |
| Malformed JSON in a live file | Report the file path and skip it (merge_knowledge.py handles repair) |

## Rules

- This skill is read-only - never write to the KB.
- If the user asks to refresh, suggest `/df-learn` and stop.
- Never fabricate entries; render exactly what the backend returned.
