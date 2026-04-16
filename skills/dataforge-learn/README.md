# dataforge-learn

Refreshes the DataForge knowledge base by spawning researcher agents that fetch updated information from whitelisted sources (library changelogs, domain techniques, role thought-leaders).

## Usage

```
/dataforge-learn all                                # Refresh everything that's stale
/dataforge-learn library                            # Refresh all libraries
/dataforge-learn library --area sklearn             # Refresh just sklearn
/dataforge-learn domain --area finance              # Refresh just finance domain
/dataforge-learn role --area data-scientist         # Refresh just one role
/dataforge-learn all --force                        # Force refresh even if not stale
/dataforge-learn library --source <url>             # Add a new source URL
/dataforge-learn all --web-search                   # Allow web search fallback
```

## What it does

1. Reads `meta.json` and `sources.json` to determine which areas are stale (past their TTL)
2. Spawns researcher agents in parallel waves (up to 10 at a time)
3. Each researcher fetches from whitelisted URLs, extracts knowledge entries, and writes `*.live.md` files
4. After all researchers complete, runs a merge step that deduplicates entries, updates the index, and patches metadata

## Knowledge areas

| Area | What's tracked |
|------|---------------|
| **Libraries** | sklearn, xgboost, lightgbm, catboost, polars, pandas, optuna, shap |
| **Domains** | healthcare, finance, marketing, retail, social, manufacturing, real-estate |
| **Roles** | data-scientist, ml-engineer, data-engineer, mlops, statistician, ai-researcher |
