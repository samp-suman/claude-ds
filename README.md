# DataForge

> **Autonomous Data Science plugin for Claude Code.**
> Drop in a dataset, walk away with a production-grade DS project — EDA, fitted
> sklearn pipelines, parallel model training, SHAP interpretation, a Streamlit /
> FastAPI app, and a polished HTML report. A continuously-learning knowledge base
> keeps the generated code current with library APIs and SOTA techniques.

**Repo:** `claude-ds`  ·  **Plugin:** `DataForge`  ·  **Command:** `/dataforge`  ·  **Current:** v0.4.0-alpha (in progress)

---

## What's new in v0.4.0 (in progress)

DataForge is being upgraded from a single-track tabular pipeline into a **continuously-learning, multi-track DS platform**:

- **Knowledge Base** — a refreshable `~/.claude/dataforge/knowledge/` store with libraries, domains, and role-expert knowledge. Researcher agents fetch, parse, and merge updates. Code is generated from current APIs, not training-cutoff guesses.
- **Architect phase** — before any code is written, expert agents read the KB, debate the approach in parallel, and consolidate an `architecture_plan.json`. User-selectable mode: `ask` / `semi` / `auto`.
- **Pipeline-based discipline** — preprocessing is a fitted `sklearn.Pipeline`, not imperative CSV mutation. Holdout test set is created **before** any `.fit()` call. Deploy app and training share one transform path. No more train/serve skew.
- **Three-track architecture** — tabular (this release), deep learning (v0.5.0), RAG (v0.6.0). Track detection, KB skeletons, and architect contracts all ship in v0.4.0 so future tracks are additions, not rewrites.
- **LEARNINGS.md fixes** — post-FE leakage gate, model-specific preprocessing, text-EDA for messy scraped data, multi-file ingest, Windows Unicode safety.

The `v0.3.0` expert-review and pipeline plumbing still works — v0.4.0 layers on top of it.

---

## Execution Flow

```mermaid
flowchart TD
    User([User]) -->|"/dataforge run data target"| Router[skills/dataforge<br/>Router]
    Router --> TypeDetect{project_type_detect.py<br/>tabular &middot; dl &middot; rag}

    TypeDetect -->|dl v0.5| DLStub[/dataforge-dl<br/>STUB/]
    TypeDetect -->|rag v0.6| RAGStub[/dataforge-rag<br/>STUB/]
    TypeDetect -->|tabular| RefreshHook[hook: pre-pipeline-refresh<br/>checks KB freshness]

    RefreshHook -->|stale| Learn[/dataforge-learn]
    RefreshHook -->|fresh| Architect

    Learn -.->|N parallel| ResL[df-researcher-library<br/>per library]
    Learn -.->|N parallel| ResD[df-researcher-domain<br/>per domain]
    Learn -.->|N parallel| ResR[df-researcher-role<br/>per role]
    ResL --> Merge[merge_knowledge.py]
    ResD --> Merge
    ResR --> Merge
    Merge --> KB[(Knowledge Base<br/>~/.claude/dataforge/<br/>knowledge/)]

    Architect[/dataforge-architect/]
    Architect -.reads.-> KB
    Architect --> Experts[df-expert-* in parallel<br/>DS &middot; Stats &middot; MLE &middot; DataEng &middot; MLOps<br/>+ domain experts &middot; AI researcher]
    Experts -->|ExpertRecommendation| Lead[df-expert-lead<br/>consolidates]
    Lead --> Plan[(architecture_plan.json)]
    Plan --> ModeGate{architect_mode}
    ModeGate -->|ask| Ask[AskUserQuestion]
    ModeGate -->|semi conf>=0.8| Pipeline
    ModeGate -->|auto| Pipeline
    Ask -->|approve| Pipeline

    Pipeline[dataforge-pipeline] --> Ingest[df-ingest]
    Ingest --> RawValidate[df-validate<br/>raw quality gate]
    RawValidate --> Holdout["build_pipeline.py<br/>STRATIFIED TEST HOLDOUT<br/>sentinel: .test_split_saved"]

    Holdout --> EDA[dataforge-eda<br/>spawns df-eda-column<br/>N parallel batch&le;10]
    EDA --> PhaseB["dataforge-preprocess Phase B<br/>df-feature-column N parallel<br/>returns transformer specs"]
    PhaseB --> PhaseC[Phase C<br/>cross-column features]
    PhaseC --> Fit["build_pipeline.py<br/>fit pipeline_tree.pkl<br/>fit pipeline_linear.pkl<br/>sentinel: .pipeline_fitted"]
    Fit --> LeakGate{df-validate-features<br/>post-FE leakage gate}
    LeakGate -->|corr&gt;0.95| Stop([HARD STOP])
    LeakGate -->|pass| Train["dataforge-modeling<br/>df-train-model N parallel<br/>each loads its family pipeline"]
    Train --> Eval[df-evaluate<br/>leaderboard.json]
    Eval --> Interp[df-interpret + df-visualize<br/>parallel SHAP + plots]
    Interp --> Deploy["dataforge-deploy<br/>app: joblib.load + pipeline.transform<br/>NO reimplementation"]
    Deploy --> Report[dataforge-report]

    Pipeline -.read/write.-> Memory[(memory/<br/>experiments<br/>decisions<br/>best_pipelines)]
    Pipeline -.snapshot.-> ProjKB[(project knowledge/<br/>per-run KB slice)]
    KB -.copy on start.-> ProjKB

    classDef new fill:#e1f5ff,stroke:#0288d1,color:#000
    classDef stub fill:#f5f5f5,stroke:#999,stroke-dasharray:5 5,color:#666
    classDef gate fill:#fff3e0,stroke:#e65100,color:#000
    classDef store fill:#f3e5f5,stroke:#6a1b9a,color:#000
    classDef stop fill:#ffebee,stroke:#c62828,color:#000

    class TypeDetect,RefreshHook,Learn,ResL,ResD,ResR,Merge,Architect,Experts,Lead,Plan,ModeGate,Ask,Holdout,Fit,LeakGate new
    class DLStub,RAGStub stub
    class RawValidate,LeakGate,ModeGate,Holdout gate
    class KB,Memory,ProjKB store
    class Stop stop
```

> **How to read it.** Blue = new in v0.4.0. Orange = quality gate or decision point. Purple = persistent store. Dashed grey = v0.5/v0.6 stub. Solid arrow = control flow; dashed arrow = read or write to a store.

---

## Decision points and communication

| Where | Who decides | What's communicated | Mechanism |
|-------|------------|---------------------|-----------|
| Track selection | `project_type_detect.py` (auto) or `--type` flag | `tabular` / `dl` / `rag` + subtype + confidence | JSON file in project |
| KB refresh | `pre-pipeline-refresh` hook reads `meta.json` TTLs | Which areas are stale | Hook prepends `/dataforge-learn` instruction |
| Architect plan | Each expert returns an `ExpertRecommendation`; `df-expert-lead` consolidates | Chosen approach + alternatives + confidence | `architecture_plan.json` (filesystem bus) |
| Plan acceptance | User (`ask`), confidence threshold (`semi`), or always (`auto`) | approve / edit / redirect | `AskUserQuestion` or auto-proceed |
| Test holdout | `build_pipeline.py` runs unconditionally before any fit | Sentinel `.test_split_saved` | Hook `pre-fit-guard.py` blocks fits without it |
| Pipeline fit | `build_pipeline.py` produces `pipeline_tree.pkl` + `pipeline_linear.pkl` | Sentinel `.pipeline_fitted` | Hook `pre-train-pipeline-gate.sh` blocks training without it |
| Post-FE leakage | `df-validate-features` runs on `pipeline.transform(X_train)` | corr>0.95 columns | Exit code 2 = HARD STOP |
| Per-stage review | Existing v0.3.0 expert layer (lead + methodology + domain) | findings, advisories, blocks | `lead_verdict` JSON in `expert_cache/` |
| Drift in production | `df-monitor` | drift score per feature + concept drift | Triggers retrain recommendation |

**No agent-to-agent IPC.** Researchers, experts, and execution agents all communicate via the filesystem (KB files, sentinels, `expert_cache/`, `memory/`). Parallel invocations of the same agent type write to disjoint paths so no locks are needed.

---

## Quick Start

```bash
# 1. Install
git clone https://github.com/samp-suman/claude-ds.git
cd claude-ds
pip install -r requirements.txt
bash install.sh              # copies skills/agents/scripts to ~/.claude/
                             # also seeds the KB at ~/.claude/dataforge/knowledge/

# 2. Run
cd ~/my-projects
claude
> /dataforge run data/churn.csv Churn          # full pipeline
> /dataforge analyze data/churn.csv            # analysis without modeling
> /dataforge eda data/churn.csv                # EDA only
> /dataforge train data/processed/train.csv y  # train + evaluate
> /dataforge deploy churn/                     # generate Streamlit/FastAPI app
> /dataforge report churn/                     # regenerate HTML/PDF report
```

### Knowledge base management (v0.4.0)

```bash
> /dataforge-setup                             # one-time wizard: refresh policy, TTLs, domains, roles
> /dataforge-learn all                         # refresh entire KB
> /dataforge-learn library --area sklearn      # refresh one area
> /dataforge-knowledge status                  # per-area last_refreshed timestamps
> /dataforge-knowledge search "target encoding"
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/dataforge run <data> <target>` | Full pipeline (tabular) — ingest through report |
| `/dataforge analyze <data>` | EDA + report, no modeling |
| `/dataforge eda <data>` | EDA only — parallel per-column |
| `/dataforge preprocess <data> <target>` | Phases A-D: cleanup, per-column transforms, cross-column, pipeline assembly |
| `/dataforge train <data> <target>` | Train all model families in parallel |
| `/dataforge validate <data>` | Raw quality + leakage checks |
| `/dataforge architect <data> <target>` | Run architect phase only — produces `architecture_plan.json` |
| `/dataforge deploy <project>` | Generate Streamlit / FastAPI app |
| `/dataforge report <project>` | Generate HTML / PDF report |
| `/dataforge status <project>` | Show experiment history |
| `/dataforge resume <project>` | Resume an interrupted pipeline |
| `/dataforge monitor <project> --new-data <path>` | Drift detection vs training distribution |
| `/dataforge-setup` | KB setup wizard (policy, TTLs, sources) |
| `/dataforge-learn [all\|library\|domain\|role]` | Refresh knowledge base |
| `/dataforge-knowledge [show\|search\|status\|diff]` | Inspect KB |

### Flags

| Flag | Effect |
|------|--------|
| `--type tabular\|dl\|rag` | Override automatic track detection |
| `--architect-mode ask\|semi\|auto` | Override default architect mode |
| `--production` | FastAPI app, force full expert review |
| `--web-search` | Allow researcher agents to use WebSearch fallback (opt-in) |
| `--force` | Re-run even if outputs exist |

See `docs/COMMANDS.md` for the full command reference.

---

## Subsystems at a glance

### Knowledge Base

```
~/.claude/dataforge/knowledge/
├── meta.json              # version, TTLs, last_refresh per area
├── sources.json           # whitelist + fetch state
├── libraries/
│   ├── tabular/           # sklearn, xgboost, lightgbm, catboost,
│   │                      # polars, pandas, optuna, shap
│   ├── dl/                # v0.5 — empty skeleton
│   ├── rag/               # v0.6 — empty skeleton
│   └── common/            # mlflow, wandb, dvc, hydra, bentoml, onnx
├── track/
│   ├── tabular/           # techniques, pitfalls
│   ├── dl/                # v0.5 — cv/nlp/timeseries/audio/multimodal
│   └── rag/               # v0.6 — text/multimodal/doc-kb/agentic
├── domain/                # real-estate finance healthcare retail
│                          # marketing manufacturing social
├── role/                  # data-scientist ml-engineer data-engineer
│                          # mlops statistician ai-researcher
│                          # (+ dl/rag roles reserved for v0.5/v0.6)
├── shared/cross-cutting.md
└── index.md
```

**Loader precedence:** project snapshot > live KB > `references/seed-knowledge/` fallback.
Live entries **extend** seeds — if the KB is empty, DataForge still works.

### The four agent families

| Family | Count | Pattern | Examples |
|--------|------|---------|----------|
| **Execution** | 12 | One agent type, N parallel invocations | `df-eda-column`, `df-feature-column`, `df-train-model`, `df-evaluate`, `df-interpret`, `df-deploy`, `df-report`, `df-monitor` |
| **Expert (v0.3.0)** | 9 | Lead + methodology + domain | `df-expert-lead`, `df-expert-datascientist`, `df-expert-statistician`, 6 domain experts |
| **Expert (v0.4.0 new)** | 4 | Cross-track role experts | `df-expert-mle`, `df-expert-dataeng`, `df-expert-mlops`, `df-expert-airesearcher` |
| **Researcher (v0.4.0 new)** | 3 | Parameterized — one type, N invocations per (library / domain / role) | `df-researcher-library`, `df-researcher-domain`, `df-researcher-role` |

Total target for v0.4.0: **28 agent files** (12 execution + 13 expert + 3 researcher).

### Pipeline discipline (v0.4.0)

The biggest correctness change: preprocessing becomes a fitted `sklearn.Pipeline` instead of imperative CSV mutation.

```
ingest -> raw validate -> STRATIFIED TEST HOLDOUT      [hook blocks any fit before this]
       -> Phase A row cleanup
       -> Phase B df-feature-column emits transformer specs (parallel)
       -> Phase C cross-column transformer specs
       -> build_pipeline.py:
            pipeline_tree    = Pipeline([...for trees...]).fit(X_train)
            pipeline_linear  = Pipeline([...for linear...]).fit(X_train)
       -> validate_features.py on pipeline.transform(X_train)  [HARD STOP if leak]
       -> df-train-model loads its family's pipeline pickle, transforms internally
       -> deploy app: joblib.load + pipeline.transform — NO reimplementation
```

Why: kills training-time leakage AND deploy-time train/serve skew with one structural change.

---

## Generated project layout

```
<project>/
├── CLAUDE.md                       # auto-loads context next session
├── dataforge.config.json           # project_type, architect_mode, test_split, ...
├── architecture_plan.json          # what the experts decided
├── knowledge/                      # per-project KB snapshot (reproducibility)
├── data/{raw,interim,processed}/
├── artifacts/
│   ├── pipeline_tree.pkl           # fitted preprocessor for tree models
│   └── pipeline_linear.pkl         # fitted preprocessor for linear models
├── src/{models,inference.py,...}
├── reports/{eda,shap,confusion,roc,final_report.html}
├── app/{app.py,Dockerfile,requirements.txt}
└── memory/{experiments.json,decisions.md,best_pipelines.json,...}
```

---

## Repository layout

```
claude-ds/
├── skills/                  # 9 skill/workflow dirs (v0.3) + 6 new in v0.4
│   ├── dataforge/           # router (parses + dispatches by track)
│   ├── dataforge-{preprocess,eda,modeling,experiment,deploy,report}/
│   ├── dataforge-{analysis,pipeline}/
│   ├── dataforge-architect/         # NEW v0.4 — runs architect phase
│   ├── dataforge-{learn,knowledge,setup}/   # NEW v0.4 — KB management
│   └── dataforge-{tabular,dl,rag}/  # NEW v0.4 — track entries (dl/rag are stubs)
├── agents/                  # 21 v0.3 + 7 new in v0.4 (3 researchers + 4 role experts)
├── scripts/                 # 16 v0.3 + 9 new in v0.4
├── references/
│   ├── *.md                 # seed reference docs
│   └── seed-knowledge/      # NEW v0.4 — baseline KB (21 files)
│       ├── domain/{7 domains}/techniques.md
│       ├── role/{6 roles}/techniques.md
│       └── libraries/tabular/{8 libs}.md
├── schema/                  # 3 v0.3 + 3 new in v0.4
├── hooks/                   # 2 v0.3 + 5 new in v0.4
├── docs/{ARCHITECTURE,COMMANDS}.md
├── extensions/              # kaggle, mlflow
├── install.sh               # syncs to ~/.claude/, runs setup wizard, seeds KB
├── CLAUDE.md
├── CHANGELOG.md
└── README.md
```

---

## Installation

### Prerequisites

- Claude Code CLI
- Python 3.9+
- (optional) Kaggle CLI for dataset auto-download

### Steps

```bash
git clone https://github.com/samp-suman/claude-ds.git
cd claude-ds
pip install -r requirements.txt
bash install.sh
```

`install.sh` does three things:
1. Copies skills, agents, scripts, references, schemas, hooks to `~/.claude/`.
2. Creates `~/.claude/dataforge/{knowledge,config.json}` if missing.
3. Runs `scripts/seed_kb.py` to populate the KB with baseline knowledge from `references/seed-knowledge/`. Existing live entries are preserved.

Then restart Claude Code. The `/dataforge` command and all sub-skills become available.

### Verify

```bash
ls ~/.claude/skills/ | grep dataforge
ls ~/.claude/agents/ | grep '^df-'
ls ~/.claude/dataforge/knowledge/
python ~/.claude/scripts/project_type_detect.py --input data/titanic.csv
```

### Uninstall

```bash
bash install.sh --uninstall
```

The KB at `~/.claude/dataforge/knowledge/` is preserved across uninstall/reinstall — your learned knowledge is never deleted.

---

## Supported inputs

| Track | Inputs | Status |
|-------|--------|--------|
| **Tabular** | CSV, TSV, JSON, JSONL, Parquet, Excel, SQLite, SQLAlchemy URI, HTTP(S) URL, Pickle, Kaggle slug | implemented |
| **Deep Learning** | image folders, audio folders, NLP text + labels, time series, multimodal | v0.5.0 (skeleton in v0.4) |
| **RAG** | PDF / DOCX / HTML / Markdown folders, multimodal docs, agentic | v0.6.0 (skeleton in v0.4) |

| Tabular problem | Detection | Default models |
|-----------------|-----------|----------------|
| Binary classification | target ≤ 2 unique | LightGBM, XGBoost, RF, Logistic, CatBoost |
| Multiclass | 3-20 unique | same; reports f1_weighted |
| Regression | float/int >20 unique | LightGBM, XGBoost, RF, Ridge, Lasso |
| Clustering | no target | KMeans, DBSCAN, Hierarchical |
| Time series | datetime index | LightGBM with lag features |

---

## Quality gates

| Stage | Check | Threshold | Action |
|-------|-------|-----------|--------|
| Raw validate | min rows | < 50 | HARD STOP |
| Raw validate | target missing | not found | HARD STOP |
| Raw validate | target leakage | corr ≥ 0.99 | HARD STOP |
| Pre-fit guard | test holdout missing | sentinel absent | HARD STOP |
| Post-FE leakage | feature ↔ target correlation | > 0.95 on `pipeline.transform(X_train)` | HARD STOP |
| Pre-train gate | pipeline fit missing | sentinel absent | HARD STOP |
| Pre-deploy lint | app re-implements transformer | regex match | HARD STOP |
| Class imbalance | majority/minority | > 10:1 | warn + auto class_weight |
| High missing | per column | > 50% | warn |
| Duplicates | row level | > 5% | warn |

Sentinels live as zero-byte files in the project (`.test_split_saved`, `.pipeline_fitted`) and are checked by hooks before the next stage runs.

---

## Memory

Each generated project keeps its own persistent memory in `memory/`:

| File | Purpose |
|------|---------|
| `experiments.json` | Run history (configs, metrics, artifact paths) |
| `decisions.md` | Why each choice was made (human-readable) |
| `failed_transforms.json` | What didn't work — skipped on resume |
| `best_pipelines.json` | Winning configs — seeds future runs |
| `architecture_plan.json` | What the architect phase decided |

---

## Extending DataForge

| To add a... | Edit | Then |
|-------------|------|------|
| Model | `references/model-catalog.md` + `scripts/train.py` `get_model()` | `bash install.sh` |
| Data source | `scripts/ingest.py` `load_data()` + `detect_format()` | `bash install.sh` |
| Skill | `skills/dataforge-{name}/SKILL.md` + router entry | `bash install.sh` |
| Domain expert | `agents/df-expert-{domain}.md` + seed knowledge in `references/seed-knowledge/domain/{domain}/` | `bash install.sh` |
| KB source | `references/seed-knowledge/` or runtime via `/dataforge-learn --source <url>` | refresh KB |
| Hook | `hooks/{name}.py` + register in `~/.claude/settings.json` | `bash install.sh` |

---

## Development workflow

```bash
# 1. Edit source
# 2. Sync to ~/.claude/
bash install.sh

# 3. Test
/dataforge validate data/titanic.csv
/dataforge run data/titanic.csv Survived

# 4. Update CHANGELOG.md
# 5. Commit + push
git add -A && git commit -m "feat: ..." && git push
```

See `CLAUDE.md` for the project constitution and conventions.

---

## Roadmap

| Version | Theme | Status |
|---------|-------|--------|
| v0.1.0 | Initial release | shipped |
| v0.2.0 | Modular skill + workflow architecture | shipped |
| v0.3.0 | Expert agent layer | shipped |
| **v0.4.0** | **Continuous learning + foundational fixes + multi-track foundation** | **in progress** |
| v0.5.0 | Deep Learning track (CV / NLP / time-series / audio / multimodal) | planned |
| v0.6.0 | RAG track (text / multimodal / doc-KB / agentic) | planned |
| v0.7.0+ | Cron-based KB refresh, cross-project insight sharing | future |

See [CHANGELOG.md](CHANGELOG.md) for full version history.
