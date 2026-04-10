# DataForge Architecture

## Overview

DataForge is a Claude Code plugin that transforms raw datasets into complete,
production-grade Data Science projects. It follows a modular **skill + workflow**
architecture inspired by [claude-seo](https://github.com/AgriciDaniel/claude-seo).

## Design Principles

1. **Modular skills**: Each DS step (preprocessing, EDA, modeling, etc.) is an
   independently invocable skill with its own SKILL.md
2. **Composable workflows**: Workflows orchestrate skills in sequence without
   duplicating logic
3. **Parallel execution**: Column-level and model-level operations run in parallel
   via Claude Code's Agent tool
4. **Shared scripts**: All computation lives in standalone Python CLI tools that
   skills and agents invoke
5. **Quality gates**: Validation must pass before training can begin
6. **Memory persistence**: Experiment history persists in the generated project folder

## Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  USER                                               │
│  /dataforge run titanic.csv Survived                │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  ROUTER: skills/dataforge/SKILL.md                  │
│  Parses command, delegates to skill/workflow         │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  WORKFLOWS                                          │
│  dataforge-pipeline  (full end-to-end)              │
│  dataforge-analysis  (EDA without modeling)          │
│  Orchestrate skills in sequence                     │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  EXPERT AGENTS (review + verify + guide) [v0.3.0]   │
│                                                     │
│  Methodology:        Domain (auto-detected):        │
│  df-expert-ds        df-expert-healthcare           │
│  df-expert-stats     df-expert-finance              │
│                      df-expert-marketing            │
│  Lead:               df-expert-retail               │
│  df-expert-lead      df-expert-social               │
│  (collates + acts)   df-expert-manufacturing        │
│                                                     │
│  Triage: expert_triage.py → skip/light/full         │
│  Domain: domain_detect.py → auto-detect domain      │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  SKILLS (atomic, independently invocable)           │
│  dataforge-preprocess  │  dataforge-eda             │
│  dataforge-modeling    │  dataforge-experiment       │
│  dataforge-deploy      │  dataforge-report           │
│  Each skill spawns agents for parallel work         │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  AGENTS (parallel execution units)                  │
│  df-eda-column (N parallel)  │  df-train-model (N)  │
│  df-feature-column (N)       │  df-interpret         │
│  df-validate  │  df-evaluate │  df-visualize         │
│  df-deploy    │  df-report   │  df-monitor           │
│  Each agent calls Python scripts                    │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│  SCRIPTS (Python CLI tools)                         │
│  ingest.py  │  validate.py  │  data_profiler.py     │
│  eda.py     │  features.py  │  train.py             │
│  evaluate.py│  interpret.py │  visualize.py          │
│  deploy_detect.py │  report.py │  memory_*.py        │
│  domain_detect.py │  expert_triage.py               │
│  Standalone, JSON output, exit codes 0/1/2          │
└─────────────────────────────────────────────────────┘
```

## Installation Layout

Development repo (`claude-ds/`) installs to `~/.claude/`:

```
~/.claude/
├── skills/
│   ├── dataforge/SKILL.md              # Router
│   ├── dataforge-preprocess/SKILL.md   # Atomic skill
│   ├── dataforge-eda/SKILL.md          # Atomic skill
│   ├── dataforge-modeling/SKILL.md     # Atomic skill
│   ├── dataforge-experiment/SKILL.md   # Atomic skill
│   ├── dataforge-deploy/SKILL.md       # Atomic skill
│   ├── dataforge-report/SKILL.md       # Atomic skill
│   ├── dataforge-analysis/SKILL.md     # Workflow
│   └── dataforge-pipeline/SKILL.md     # Workflow
├── agents/df-*.md                      # 21 sub-agents (12 execution + 9 expert)
├── scripts/*.py                        # 16 Python scripts
├── references/*.md                     # 12 reference docs (6 general + 6 domain)
├── schema/*.json                       # 3 JSON schemas
└── hooks/*                             # 2 hooks
```

## Data Flow

```
Raw Dataset
    │
    ▼
INGEST (ingest.py) ──► data/raw/{file}
    │
    ▼
VALIDATE (validate.py) ──► validation_report.json + .validation_passed
    │ (GATE: exit_code 2 = STOP)
    ▼
PROFILE (data_profiler.py) ──► profile.json + dataforge.config.json
    │
    ▼
DOMAIN DETECT (domain_detect.py) ──► expert_cache/domain.json
    │
    ▼
EXPERT CHECKPOINT 1 (triage → experts → lead) ──► preprocessing review
    │ (block = pause for user)
    ▼
EDA (eda.py, parallel) ──► reports/eda/{col}_stats.json + {col}_plot.png
    │                       eda_summary.json + correlation_heatmap.png
    ▼
EXPERT CHECKPOINT 2 (triage → experts → lead) ──► EDA review
    │
    ▼
FEATURES (features.py, parallel) ──► data/processed/train.csv
    │
    ▼
TRAIN (train.py, ALL parallel) ──► src/models/{model}.pkl + {model}_metrics.json
    │
    ▼
EVALUATE (evaluate.py) ──► src/models/leaderboard.json
    │
    ▼
EXPERT CHECKPOINT 3 (triage → experts → lead) ──► modeling review
    │
    ├──► INTERPRET (interpret.py) ──► shap_summary.png, shap_bar.png
    │                                  (parallel)
    └──► VISUALIZE (visualize.py) ──► confusion_matrix.png, roc_curve.png
    │
    ▼
DEPLOY (deploy_detect.py + df-deploy) ──► app/app.py + Dockerfile
    │
    ▼
REPORT (report.py) ──► reports/final_report.html
```

## Parallel Execution Strategy

| Stage | Parallelism | Batch Size |
|-------|------------|------------|
| EDA | One agent per column | <= 10 per batch |
| Feature engineering | One agent per column | <= 10 per batch |
| **Model training** | **All models at once** | **Single batch** |
| Interpret + Visualize | Both simultaneously | 2 agents |
| **Expert review (full)** | **Methodology + domain parallel, then lead** | **2-3 experts + lead** |

## Quality Gate System

Validation runs before any modeling. Hard stops (exit code 2) halt the pipeline:

| Check | Threshold | Action |
|-------|-----------|--------|
| Minimum rows | < 50 | HARD STOP |
| Target missing | Not found | HARD STOP |
| Target variance | 1 unique value | HARD STOP |
| Target leakage | Correlation >= 0.99 | HARD STOP |
| Class imbalance | > 10:1 | Warning, set balanced weights |
| High missing | > 50% per column | Warning, impute |
| Duplicates | > 5% | Warning, deduplicate |

## Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `post-generate-lint.py` | After Write/Edit of .py file | pyflakes check on generated code |
| `pre-train-validate.sh` | Before Bash with train.py | Blocks training if validation not passed |

## Memory System

Each generated project persists memory in `memory/`:

| File | Purpose |
|------|---------|
| `experiments.json` | Run history (configs, metrics, artifact paths) |
| `best_pipelines.json` | Winning configurations (seeds future runs) |
| `failed_transforms.json` | Transforms/models that failed (avoid repeating) |
| `decisions.md` | Human-readable log of why choices were made |

## Extension Points

| Extension | Location | Purpose |
|-----------|----------|---------|
| Kaggle | `extensions/kaggle/` | Download datasets via Kaggle API |
| MLflow | `extensions/mlflow/` | Log experiments to MLflow server |

## Key Design Decisions

1. **Flat skill directories** -- Claude Code discovers skills by scanning
   `skills/*/SKILL.md`, so each skill is a peer directory
2. **Scripts are standalone** -- No imports between scripts; each is a CLI tool
   with `--arg` interface and JSON stdout
3. **Agents are shared** -- All agents live in `agents/` and are reused across
   skills (e.g., `df-report` used by both report skill and pipeline workflow)
4. **Workflows don't duplicate** -- Workflows call skills by name, never
   re-implement skill logic
5. **Memory in project** -- No external DB; all state lives in the generated
   project's `memory/` directory

---

## Expert Agent Layer (v0.3.0)

DataForge includes an expert review layer that acts as senior practitioners
reviewing, auto-correcting, and guiding pipeline decisions.

### Expert Types

**Methodology Experts** (verify techniques):

| Agent | Role | Expertise |
|-------|------|-----------|
| `df-expert-datascientist` | Senior DS (10+ yr) | Pipeline review, model selection, overfitting, bias |
| `df-expert-statistician` | Senior Statistician (10+ yr) | Distributions, tests, assumptions, leakage |

**Domain Experts** (understand business context, auto-detected):

| Agent | Domain | Knowledge |
|-------|--------|-----------|
| `df-expert-healthcare` | Healthcare/Clinical | Clinical thresholds, HIPAA, confounders, survival analysis |
| `df-expert-finance` | Banking/Fintech | Risk scoring, fraud, regulatory, temporal leakage, fair lending |
| `df-expert-marketing` | Marketing/CRM | CLV, churn, RFM, attribution, A/B testing, cohort analysis |
| `df-expert-retail` | Retail/E-commerce | Demand forecasting, price elasticity, basket analysis, seasonality |
| `df-expert-social` | Social Media/NLP | Engagement, sentiment, network effects, bot detection |
| `df-expert-manufacturing` | IoT/Manufacturing | Sensor data, predictive maintenance, SPC, yield optimization |

**Lead Expert** (collates findings, makes final call):

| Agent | Role |
|-------|------|
| `df-expert-lead` | Collates all expert findings, applies auto-corrections, returns verdict |

### Adaptive Expert Triage

Experts trigger based on data complexity, not blindly at every stage:

```
Stage completes → expert_triage.py (complexity score)
  ├── score < 0.2:  skip (no experts, 0 token cost)
  ├── score 0.2-0.5: light (lead expert only, ~1 agent call)
  └── score > 0.5:  full (methodology + domain + lead, ~3-4 agent calls)

Always full if: --production, first run, or --domain flag set
```

### Expert Checkpoints

| Checkpoint | After Stage | What's Reviewed |
|-----------|-------------|-----------------|
| 1 | Preprocessing | Imputation, encoding, feature drops, leakage, domain features |
| 2 | EDA | Distributions, correlations, outliers, imbalance, domain patterns |
| 3 | Modeling | Train-test gap, metric selection, SHAP sanity, calibration |

### Lead Verdict

The lead expert returns one of three verdicts:

- **approve** — Continue normally
- **flag** — Continue, advisories logged to `memory/decisions.md`
- **block** — Pause pipeline, present critical issues to user for review

### Token Optimization

1. **Lazy loading**: Domain reference docs loaded only when domain expert triggers
2. **Tiered depth**: Skip/light/full based on complexity score
3. **Agent continuity**: Experts spawned once, continued via SendMessage at later stages
4. **Cross-stage caching**: All findings cached in `expert_cache/` directory
5. **Cache-friendly prompts**: Static persona + dynamic inputs structure for prompt caching

### Domain Auto-Detection

`domain_detect.py` scores each domain using 4 layers:
- Column name keywords (weight 0.4)
- Filename patterns (weight 0.2)
- Value patterns from profile (weight 0.3)
- Feature type distribution (weight 0.1)

Confidence >= 0.5 activates domain expert; otherwise "general" (no domain expert).

---

## Roadmap

| Version | Deliverable |
|---------|------------|
| v0.4.0 | Expert consensus protocol (multiple experts vote, conflicts escalated) |
