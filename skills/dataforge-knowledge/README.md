# dataforge-knowledge

Read-only inspection of the DataForge knowledge base. Search, browse, and check freshness of the live KB without modifying it.

## Usage

```
/dataforge-knowledge show <area>                    # Print full content for one area (e.g. sklearn, finance)
/dataforge-knowledge search <query>                 # Search entries across all live files
/dataforge-knowledge status                         # Per-area freshness report (last refreshed, stale?)
/dataforge-knowledge diff                           # Show seed-sourced vs researcher-sourced files
```

## What it does

- **show** — Displays the full live markdown for a specific area (library, domain, or role)
- **search** — Full-text search across all knowledge entries by title, summary, or body
- **status** — Reports freshness per area: source type, seeded date, last refresh date, whether it's stale
- **diff** — Compares seed baseline vs live researcher-updated files, with entry counts

## Knowledge base location

```
~/.claude/dataforge/knowledge/
```

To update the knowledge base, use [`/dataforge-learn`](../dataforge-learn/).
