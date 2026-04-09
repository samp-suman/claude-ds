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
├── agents/df-*.md                      # 12 sub-agents
├── scripts/*.py                        # 14 Python scripts
├── references/*.md                     # 6 reference docs
├── schema/*.json                       # 2 JSON schemas
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
EDA (eda.py, parallel) ──► reports/eda/{col}_stats.json + {col}_plot.png
    │                       eda_summary.json + correlation_heatmap.png
    ▼
FEATURES (features.py, parallel) ──► data/processed/train.csv
    │
    ▼
TRAIN (train.py, ALL parallel) ──► src/models/{model}.pkl + {model}_metrics.json
    │
    ▼
EVALUATE (evaluate.py) ──► src/models/leaderboard.json
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

## Roadmap: Expert Agent Layer (v0.3.0+)

The next evolution of DataForge adds an **expert agent layer** -- specialized
agents that act as senior practitioners who review, verify, and guide decisions
made by the execution agents. These experts don't just process data -- they
apply deep domain knowledge and methodological rigor.

### Layer Architecture (Target)

```
┌─────────────────────────────────────────────────────────────┐
│  EXPERT AGENTS (review + verify + guide)                    │
│                                                             │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │  DOMAIN EXPERTS     │  │  METHODOLOGY EXPERTS         │  │
│  │                     │  │                              │  │
│  │  df-expert-health   │  │  df-expert-datascientist     │  │
│  │  df-expert-finance  │  │  df-expert-statistician      │  │
│  │  df-expert-market   │  │  df-expert-mlops             │  │
│  │  df-expert-retail   │  │                              │  │
│  │  df-expert-social   │  │  10+ years experience        │  │
│  │  df-expert-mfg      │  │  Verify techniques, catch    │  │
│  │                     │  │  methodological errors,      │  │
│  │  Know domain KPIs,  │  │  suggest better approaches   │  │
│  │  business logic,    │  │                              │  │
│  │  feature meaning    │  │                              │  │
│  └─────────────────────┘  └──────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  SKILLS + WORKFLOWS (orchestrate)                           │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  EXECUTION AGENTS + SCRIPTS (process)                       │
└─────────────────────────────────────────────────────────────┘
```

### Domain Expert Agents

Domain experts understand the business context of the data. They are spawned
based on auto-detected or user-specified domain. Each expert knows:

| Agent | Domain | Knowledge |
|-------|--------|-----------|
| `df-expert-healthcare` | Healthcare, clinical, pharma | HIPAA awareness, clinical feature interpretation (BMI, vitals, lab ranges), survival analysis, class imbalance in diagnosis, confounding variables |
| `df-expert-finance` | Banking, fintech, insurance | Risk scoring, fraud patterns, regulatory features, time-series financial data, PD/LGD/EAD models, credit scoring |
| `df-expert-marketing` | Marketing, advertising, CRM | Customer lifetime value, churn signals, RFM segmentation, attribution modeling, A/B test analysis, cohort analysis |
| `df-expert-retail` | E-commerce, retail, supply chain | Demand forecasting, price elasticity, basket analysis, inventory signals, seasonality, category management |
| `df-expert-social` | Social media, content, NLP | Engagement metrics, sentiment features, network effects, viral signals, content classification, bot detection |
| `df-expert-manufacturing` | IoT, manufacturing, quality | Sensor data patterns, predictive maintenance, yield optimization, SPC signals, anomaly detection |

**What domain experts do at each stage:**

1. **After EDA** -- Review findings through domain lens:
   - Flag features with domain-specific meaning (e.g., "HbA1c > 6.5 means diabetes")
   - Suggest domain-specific feature engineering (e.g., "create BMI from height/weight")
   - Identify business-relevant outliers vs data errors
   - Recommend domain-appropriate analysis types

2. **After preprocessing** -- Verify transforms make domain sense:
   - Catch harmful transforms (e.g., "don't log-transform age in healthcare")
   - Suggest domain-standard encodings
   - Flag dropped features that have domain importance

3. **After modeling** -- Interpret results through domain lens:
   - Validate that top SHAP features make domain sense
   - Flag surprising features (possible leakage or spurious correlations)
   - Suggest domain-appropriate metrics (e.g., sensitivity over accuracy for diagnosis)
   - Provide business impact interpretation

### Methodology Expert Agents

Methodology experts act as senior data scientists and statisticians who verify
that the right techniques are being used correctly.

| Agent | Role | Expertise |
|-------|------|-----------|
| `df-expert-datascientist` | Senior DS (10+ yr) | End-to-end pipeline review, feature selection strategy, model selection rationale, experiment design, bias detection, overfitting risk |
| `df-expert-statistician` | Senior Statistician (10+ yr) | Distribution assumptions, hypothesis testing validity, correlation vs causation, sample size adequacy, statistical power, confidence intervals |
| `df-expert-mlops` | ML Engineer / MLOps | Model serving readiness, inference latency, model size constraints, A/B testing design, monitoring strategy, retraining triggers |

**What methodology experts do at each stage:**

1. **After preprocessing** -- `df-expert-statistician` reviews:
   - Are imputation methods statistically appropriate?
   - Is scaling applied correctly (fit on train only)?
   - Are encoding choices justified for the model types?
   - Is there data leakage in the preprocessing pipeline?

2. **After EDA** -- `df-expert-datascientist` reviews:
   - Are the right statistical tests being used?
   - Are correlations being interpreted correctly?
   - Is the feature study comprehensive enough?
   - Should additional analysis be done (PCA, clustering, time decomposition)?

3. **After modeling** -- `df-expert-datascientist` reviews:
   - Is the train/test split appropriate (stratified? temporal?)?
   - Is cross-validation setup correct for this problem type?
   - Are the right metrics being used as primary?
   - Is there overfitting (large gap between train and CV scores)?
   - Should hyperparameter tuning be done?
   - Are there better model architectures to try?

4. **After evaluation** -- `df-expert-mlops` reviews:
   - Is the model production-ready? (size, latency, dependencies)
   - Is the monitoring strategy appropriate?
   - Are the right drift metrics being tracked?
   - Is the deployment target appropriate for the use case?

### Expert Integration Pattern

Experts are invoked as **review checkpoints** between pipeline stages. They
receive the outputs of the previous stage and return a structured review:

```json
{
  "agent": "df-expert-healthcare",
  "stage_reviewed": "eda",
  "verdict": "approve|flag|block",
  "findings": [
    {
      "severity": "critical|warning|suggestion",
      "finding": "HbA1c feature dropped as high-cardinality but is the primary diabetes indicator",
      "recommendation": "Keep HbA1c, bin into clinical ranges: normal (<5.7), prediabetes (5.7-6.4), diabetes (>6.5)",
      "domain_rationale": "Standard ADA diagnostic threshold"
    }
  ],
  "approved_decisions": ["age imputation with median", "BMI feature creation"],
  "domain_features_suggested": ["BMI = weight_kg / (height_m ^ 2)", "age_group binning"]
}
```

**Verdict meanings:**
- `approve` -- Expert agrees with all decisions, pipeline continues
- `flag` -- Expert has suggestions but doesn't block; findings logged to `memory/decisions.md`
- `block` -- Expert found a critical issue (e.g., target leakage, harmful transform); pipeline pauses for user review

### Domain Auto-Detection

The pipeline auto-detects domain from:
1. Column names (e.g., `diagnosis`, `icd_code` -> healthcare)
2. Dataset filename (e.g., `patient_records.csv` -> healthcare)
3. Value patterns (e.g., dollar amounts, dates, medical codes)
4. User-specified domain flag: `/dataforge run data.csv target --domain healthcare`

### Implementation Plan

| Phase | Deliverable |
|-------|------------|
| v0.3.0 | `df-expert-datascientist` + `df-expert-statistician` -- methodology review at each stage |
| v0.3.1 | Domain auto-detection logic + `df-expert-healthcare` + `df-expert-finance` |
| v0.3.2 | `df-expert-marketing` + `df-expert-retail` + `df-expert-social` |
| v0.3.3 | `df-expert-mlops` + `df-expert-manufacturing` |
| v0.4.0 | Expert consensus protocol (multiple experts vote, conflicts escalated to user) |
