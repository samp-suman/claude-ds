---
name: dataforge
description: >
  Autonomous Data Science project generator. Routes commands to specialized
  DataForge skills and workflows. Given a dataset and problem statement,
  orchestrates a complete production-grade DS project. Triggers on: "data science",
  "train model", "build pipeline", "analyze dataset", "predict", "classification",
  "regression", "clustering", "EDA", "feature engineering", "dataforge",
  "run pipeline", "ml project", "machine learning project".
user-invokable: true
argument-hint: "<command> [arguments]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Data Science Pipeline Router

> Routes `/dataforge <command>` to the appropriate skill or workflow.

## Commands

| Command | Delegates to | What it does |
|---------|-------------|-------------|
| `/dataforge run <dataset> <target>` | `dataforge-pipeline` | Full pipeline: ingest -> validate -> EDA -> features -> train -> evaluate -> interpret -> deploy -> report |
| `/dataforge analyze <dataset> [target]` | `dataforge-analysis` | Data analysis: ingest -> validate -> EDA -> report (no modeling) |
| `/dataforge eda <dataset>` | `dataforge-eda` | EDA only: profile + parallel per-column analysis + correlation heatmap |
| `/dataforge preprocess <dataset> <target>` | `dataforge-preprocess` | Preprocessing: ingest + validate + profile + feature engineering |
| `/dataforge train <dataset> <target>` | `dataforge-modeling` | Train all models in parallel, evaluate, rank |
| `/dataforge deploy <project-dir>` | `dataforge-deploy` | Generate Streamlit/FastAPI app for existing project |
| `/dataforge report <project-dir>` | `dataforge-report` | Regenerate HTML/PDF report from existing results |
| `/dataforge validate <dataset>` | `dataforge-preprocess` | Data quality checks + leakage detection only |
| `/dataforge status <project-dir>` | `dataforge-experiment` | Print memory: experiments, decisions, best pipeline |
| `/dataforge resume <project-dir>` | `dataforge-pipeline` | Resume interrupted pipeline from last checkpoint |
| `/dataforge monitor <dir> --new-data <path>` | `dataforge-experiment` | Data/concept drift detection |
| `/dataforge learn [scope] [flags]` | `dataforge-learn` | Refresh the live knowledge base from whitelisted sources |
| `/dataforge knowledge [subcommand]` | `dataforge-knowledge` | Inspect / search / diff the live knowledge base (read-only) |
| `/dataforge compare <project-dir>` | `dataforge-experiment` | Compare experiments across runs |

---

## ROUTING LOGIC

Parse the first argument after `/dataforge` as `COMMAND`.

### `run` -> dataforge-pipeline workflow

Full end-to-end pipeline. Requires `<dataset>` and `<target>`.
Invoke the `dataforge-pipeline` skill with all arguments.

### `analyze` -> dataforge-analysis workflow

Data analysis without modeling. Requires `<dataset>`, optional `[target]`.
Invoke the `dataforge-analysis` skill.

### `eda` -> dataforge-eda skill

EDA only. Requires `<dataset>`.
Invoke the `dataforge-eda` skill.

### `preprocess` -> dataforge-preprocess skill

Preprocessing pipeline. Route to appropriate sub-command:
- `/dataforge preprocess <dataset> <target>` -> `/dataforge-preprocess features <dataset> <target>`
- `/dataforge validate <dataset>` -> `/dataforge-preprocess validate <dataset>`
- `/dataforge ingest <dataset>` -> `/dataforge-preprocess ingest <dataset>`

### `train` -> dataforge-modeling skill

Model training. Requires `<dataset>` and `<target>`.
Invoke `/dataforge-modeling train <dataset> <target>`.

### `deploy` -> dataforge-deploy skill

Deployment. Requires `<project-dir>`.
Invoke the `dataforge-deploy` skill.

### `report` -> dataforge-report skill

Report generation. Requires `<project-dir>`.
Invoke the `dataforge-report` skill.

### `status` / `compare` / `monitor` / `history` -> dataforge-experiment skill

Experiment management. Requires `<project-dir>`.
Invoke the `dataforge-experiment` skill with the appropriate sub-command.

### `resume` -> dataforge-pipeline workflow (resume mode)

Resume interrupted pipeline. Requires `<project-dir>`.
Invoke the `dataforge-pipeline` skill in resume mode.

---

## SHARED CONSTANTS

All skills use these paths:

```
SCRIPTS_DIR     = ~/.claude/scripts/
REFERENCES_DIR  = ~/.claude/references/
SCHEMA_DIR      = ~/.claude/schema/
HOOKS_DIR       = ~/.claude/hooks/
```

---

## ARCHITECTURE

DataForge follows a modular skill + workflow architecture:

**Atomic Skills** (independently invocable):
- `dataforge-preprocess` -- data ingestion, validation, profiling, feature engineering
- `dataforge-eda` -- exploratory data analysis (parallel per-column + global)
- `dataforge-modeling` -- model training, evaluation, interpretation, visualization
- `dataforge-experiment` -- experiment tracking, comparison, drift monitoring
- `dataforge-deploy` -- deployment app generation (Streamlit/FastAPI)
- `dataforge-report` -- HTML/PDF report generation

**Workflows** (composite orchestrations):
- `dataforge-analysis` -- preprocess + EDA + report (no modeling)
- `dataforge-pipeline` -- full end-to-end pipeline (all skills)

**Sub-Agents** (spawned by skills for parallel execution):
- `df-ingest`, `df-validate` -- data processing agents
- `df-eda-column`, `df-eda-global` -- per-column and global EDA agents
- `df-feature-column` -- feature engineering agents (parallel)
- `df-train-model` -- model training agents (all models simultaneously)
- `df-evaluate` -- model ranking agent
- `df-interpret`, `df-visualize` -- interpretation agents (parallel pair)
- `df-deploy` -- deployment generation agent
- `df-report` -- report assembly agent
- `df-monitor` -- drift detection agent

**Scripts** (shared Python CLI tools in `~/.claude/scripts/`):
- All computation runs in standalone Python scripts
- Scripts have narrow CLI interfaces and return JSON results
- Exit codes: 0 = success, 1 = warning, 2 = fatal error

---

## ERROR HANDLING

If the command is not recognized:
- Print the command table above
- Suggest the most likely intended command
- List available skills that can be invoked directly
