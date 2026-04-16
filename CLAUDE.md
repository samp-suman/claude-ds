# DataForge — Autonomous Data Science Pipeline

> Claude Code plugin that transforms raw datasets into complete, production-grade
> Data Science projects with parallel model training, SHAP interpretation, and
> deployment app generation.

## Architecture

DataForge follows a modular **skill + workflow** architecture:

### Skills (atomic, independently invocable)

| Skill | Command | Purpose |
|-------|---------|---------|
| `dataforge-preprocess` | `/dataforge-preprocess [ingest\|validate\|profile\|features]` | Data ingestion, validation, profiling, feature engineering |
| `dataforge-eda` | `/dataforge-eda [column\|global\|summary]` | Exploratory data analysis (parallel per-column + global) |
| `dataforge-modeling` | `/dataforge-modeling [train\|evaluate\|interpret\|visualize]` | Model training, evaluation, SHAP interpretation |
| `dataforge-experiment` | `/dataforge-experiment [status\|compare\|monitor\|history]` | Experiment tracking, comparison, drift monitoring |
| `dataforge-deploy` | `/dataforge-deploy [--production]` | Streamlit/FastAPI/Flask app generation |
| `dataforge-report` | `/dataforge-report [eda]` | HTML/PDF report generation |

### Workflows (composite, orchestrate multiple skills)

| Workflow | Command | Steps |
|----------|---------|-------|
| `dataforge-analysis` | `/dataforge analyze <dataset>` | preprocess -> EDA -> report |
| `dataforge-pipeline` | `/dataforge run <dataset> <target>` | preprocess -> EDA -> modeling -> deploy -> report |

### Router

`dataforge` parses `/dataforge <command>` and delegates to the appropriate skill/workflow.

## Quick Commands

| Command | What it does |
|---------|-------------|
| `/dataforge run <dataset> <target>` | Full end-to-end pipeline |
| `/dataforge analyze <dataset>` | Data analysis without modeling |
| `/dataforge eda <dataset>` | EDA only |
| `/dataforge preprocess <dataset> <target>` | Preprocessing only |
| `/dataforge train <dataset> <target>` | Train + evaluate models |
| `/dataforge deploy <project-dir>` | Generate deployment app |
| `/dataforge report <project-dir>` | Generate HTML/PDF report |
| `/dataforge validate <dataset>` | Data quality checks only |
| `/dataforge status <project-dir>` | View experiment history |
| `/dataforge resume <project-dir>` | Resume interrupted pipeline |
| `/dataforge monitor <dir> --new-data <path>` | Drift detection |

## Directory Layout

```
claude-ds/
├── skills/                   # SKILL.md files (each skill is a subdirectory)
│   ├── dataforge/            # Router (parses commands, delegates)
│   ├── dataforge-preprocess/ # Atomic: ingestion, validation, features
│   ├── dataforge-eda/        # Atomic: EDA analysis + plots
│   ├── dataforge-modeling/   # Atomic: training, evaluation, SHAP
│   ├── dataforge-experiment/ # Atomic: tracking, comparison, monitoring
│   ├── dataforge-deploy/     # Atomic: Streamlit/FastAPI app generation
│   ├── dataforge-report/     # Atomic: HTML/PDF report generation
│   ├── dataforge-analysis/   # Workflow: preprocess + EDA + report
│   └── dataforge-pipeline/   # Workflow: full end-to-end pipeline
├── agents/                   # 21 agents: 12 execution + 9 expert (df-*.md)
├── scripts/                  # 16 Python CLI scripts (all computation)
├── references/               # 12 reference docs (6 general + 6 domain)
├── schema/                   # 3 JSON schemas (config, memory, expert-output)
├── hooks/                    # Pre/Post tool use hooks
├── extensions/               # Optional: Kaggle, MLflow
├── docs/                     # ARCHITECTURE.md, COMMANDS.md
├── requirements.txt          # Python dependencies
├── install.sh                # Install to ~/.claude/
├── CHANGELOG.md              # Version history
└── README.md                 # Installation + usage guide
```

## Conventions

- Scripts are standalone CLI tools; invoke with `~/.claude/dataforge/dfpython ~/.claude/scripts/<name>.py`
- Agents communicate via JSON-in, JSON-out contract
- Parallel execution: column agents batch <= 10; model training is one batch
- Memory persists in generated project folder (`memory/` directory)
- Quality gates: exit code 2 = HARD STOP, exit code 1 = warnings, exit code 0 = pass
- Reference files are loaded on-demand, never all at startup
- Each SKILL.md must stay under 500 lines
- Expert agents trigger adaptively via `expert_triage.py` (skip/light/full)
- Domain auto-detected via `domain_detect.py`; domain experts only spawn when confidence >= 0.5

## Installation

```bash
bash install.sh              # Install to ~/.claude/
bash install.sh --uninstall  # Remove
pip install -r requirements.txt
```

## Working on This Repo

- Read `docs/ARCHITECTURE.md` for system design
- Read `docs/COMMANDS.md` for all commands reference
- Read `CHANGELOG.md` before making changes
- Always update CHANGELOG.md after changes
- Test changes with: `/dataforge run titanic.csv Survived`
- Scripts must not import from each other (standalone CLI tools)
- Run `bash install.sh` after any changes to sync to `~/.claude/`
