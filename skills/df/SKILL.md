---
name: df
description: >
  DataForge router. Routes commands to 15 specialized skills: core DS pipeline
  (preprocess, EDA, modeling, deploy, experiment, pipeline), domain-specific skills
  (feature-architect, rag-orchestrator, llm-orchestrator), infrastructure skills
  (mlops-pipeline, distributed-training), and utilities (analysis, knowledge, learn,
  report). Autonomous execution of end-to-end data science projects.
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
| `/dataforge run <dataset> <target>` | `df-pipeline` | Full pipeline: ingest -> validate -> EDA -> features -> train -> evaluate -> interpret -> deploy -> report |
| `/dataforge analyze <dataset> [target]` | `df-analysis` | Data analysis: ingest -> validate -> EDA -> report (no modeling) |
| `/dataforge eda <dataset>` | `df-eda` | EDA only: profile + parallel per-column analysis + correlation heatmap |
| `/dataforge preprocess <dataset> <target>` | `df-preprocess` | Preprocessing: ingest + validate + profile + feature engineering |
| `/dataforge train <dataset> <target>` | `df-modeling` | Train all models in parallel, evaluate, rank |
| `/dataforge deploy <project-dir>` | `df-deploy` | Generate Streamlit/FastAPI app for existing project |
| `/dataforge report <project-dir>` | `df-report` | Regenerate HTML/PDF report from existing results |
| `/dataforge validate <dataset>` | `df-preprocess` | Data quality checks + leakage detection only |
| `/dataforge status <project-dir>` | `df-experiment` | Print memory: experiments, decisions, best pipeline |
| `/dataforge resume <project-dir>` | `df-pipeline` | Resume interrupted pipeline from last checkpoint |
| `/dataforge monitor <dir> --new-data <path>` | `df-experiment` | Data/concept drift detection |
| `/dataforge learn [scope] [flags]` | `df-learn` | Refresh the live knowledge base from whitelisted sources |
| `/dataforge knowledge [subcommand]` | `df-knowledge` | Inspect / search / diff the live knowledge base (read-only) |
| `/dataforge compare <project-dir>` | `df-experiment` | Compare experiments across runs |

---

## ROUTING LOGIC

Parse the first argument after `/dataforge` as `COMMAND`.

### `run` -> df-pipeline workflow

Full end-to-end pipeline. Requires `<dataset>` and `<target>`.
Invoke the `df-pipeline` skill with all arguments.

### `analyze` -> df-analysis workflow

Data analysis without modeling. Requires `<dataset>`, optional `[target]`.
Invoke the `df-analysis` skill.

### `eda` -> df-eda skill

EDA only. Requires `<dataset>`.
Invoke the `df-eda` skill.

### `preprocess` -> df-preprocess skill

Preprocessing pipeline. Route to appropriate sub-command:
- `/dataforge preprocess <dataset> <target>` -> `/df-preprocess features <dataset> <target>`
- `/dataforge validate <dataset>` -> `/df-preprocess validate <dataset>`
- `/dataforge ingest <dataset>` -> `/df-preprocess ingest <dataset>`

### `train` -> df-modeling skill

Model training. Requires `<dataset>` and `<target>`.
Invoke `/df-modeling train <dataset> <target>`.

### `deploy` -> df-deploy skill

Deployment. Requires `<project-dir>`.
Invoke the `df-deploy` skill.

### `report` -> df-report skill

Report generation. Requires `<project-dir>`.
Invoke the `df-report` skill.

### `status` / `compare` / `monitor` / `history` -> df-experiment skill

Experiment management. Requires `<project-dir>`.
Invoke the `df-experiment` skill with the appropriate sub-command.

### `resume` -> df-pipeline workflow (resume mode)

Resume interrupted pipeline. Requires `<project-dir>`.
Invoke the `df-pipeline` skill in resume mode.

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
- `df-preprocess` -- data ingestion, validation, profiling, feature engineering
- `df-eda` -- exploratory data analysis (parallel per-column + global)
- `df-modeling` -- model training, evaluation, interpretation, visualization
- `df-experiment` -- experiment tracking, comparison, drift monitoring
- `df-deploy` -- deployment app generation (Streamlit/FastAPI)
- `df-report` -- HTML/PDF report generation

**Workflows** (composite orchestrations):
- `df-analysis` -- preprocess + EDA + report (no modeling)
- `df-pipeline` -- full end-to-end pipeline (all skills)

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
