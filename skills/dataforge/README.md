# DataForge Router Skill

This is the **router skill** -- the main entry point for DataForge. It parses
`/dataforge <command>` and delegates to the appropriate atomic skill or workflow.

## How It Works

The router contains:
- Command table mapping commands to skills/workflows
- Input parsing logic (extract dataset, target, flags)
- Architecture overview for reference

The router **never does computation itself** -- it delegates everything.

## Routing Table

| Command | Delegates to |
|---------|-------------|
| `run` | dataforge-pipeline |
| `analyze` | dataforge-analysis |
| `eda` | dataforge-eda |
| `preprocess` | dataforge-preprocess |
| `train` | dataforge-modeling |
| `deploy` | dataforge-deploy |
| `report` | dataforge-report |
| `validate` | dataforge-preprocess |
| `status` | dataforge-experiment |
| `resume` | dataforge-pipeline |
| `monitor` | dataforge-experiment |
| `compare` | dataforge-experiment |

## Related Skills

All skills live as peer directories under `skills/`:
- `skills/dataforge-preprocess/` -- ingestion, validation, features
- `skills/dataforge-eda/` -- exploratory data analysis
- `skills/dataforge-modeling/` -- training, evaluation, SHAP
- `skills/dataforge-experiment/` -- tracking, comparison
- `skills/dataforge-deploy/` -- deployment apps
- `skills/dataforge-report/` -- report generation
- `skills/dataforge-analysis/` -- analysis workflow
- `skills/dataforge-pipeline/` -- full pipeline workflow
