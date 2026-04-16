# DataForge Architecture

> Updated for **v0.4.0** — multi-track foundation, knowledge base, architect phase,
> and pipeline-based DS-process discipline.

## Overview

DataForge is a Claude Code plugin that turns a dataset into a complete,
production-grade Data Science project. It is organized as a stack of layers:

1. A **router** that picks an execution track from the input.
2. A **knowledge base** that researcher agents keep current.
3. An **architect phase** where role and domain experts decide the approach.
4. A **track-specific pipeline** that executes the plan with parallel agents.
5. **Hooks** that enforce correctness invariants the model can't talk its way out of.
6. **Memory** that persists per-project state for resume and reproducibility.

v0.4.0 is the foundation release: tabular is fully populated; deep-learning and
RAG tracks ship as skeletons so v0.5/v0.6 are additions, not rewrites.

---

## Design principles

1. **Modular skills.** Each DS step lives in its own `skills/<name>/SKILL.md`.
   Skills are independently invocable and stay under 500 lines.
2. **Composable workflows.** Workflows orchestrate skills in sequence; they
   never re-implement skill logic.
3. **Parallel by default.** Per-column work, per-model training, and per-area
   research all run as N invocations of one agent type in a single message.
4. **Filesystem as bus.** Researchers, experts, and execution agents communicate
   via files (KB entries, sentinels, `expert_cache/`, `memory/`). No locks, no IPC.
5. **Standalone scripts.** All real computation lives in `scripts/*.py` CLI tools
   that don't import each other. Skills and agents call them via Bash.
6. **Hooks enforce, not hope.** Test holdout, pipeline fit, leakage gate, and
   deploy-app correctness are all enforced by `PreToolUse` / `UserPromptSubmit`
   hooks — the LLM cannot skip them.
7. **Forward-compatible from day one.** Every v0.4.0 schema and contract is
   designed to cover DL and RAG without rewrites.
8. **Loader precedence.** Project snapshot > live KB > seed fallback. Live KB
   extends seeds, never replaces them, so DataForge works even with an empty KB.

---

## Layered architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER                                                       │
│  /dataforge run titanic.csv Survived                        │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ROUTER (skills/dataforge/SKILL.md)                         │
│  + project_type_detect.py  ->  tabular | dl | rag           │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  TRACK ENTRY                                                │
│  dataforge-tabular  (v0.4 implemented)                      │
│  dataforge-dl       (v0.5 stub)                             │
│  dataforge-rag      (v0.6 stub)                             │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  KNOWLEDGE REFRESH (hook + skill)                           │
│  pre-pipeline-refresh.py checks meta.json TTLs              │
│  /df-learn spawns:                                   │
│    df-researcher-library  x N  (parallel)                   │
│    df-researcher-domain   x N  (parallel)                   │
│    df-researcher-role     x N  (parallel)                   │
│  merge_knowledge.py rebuilds index + cross-cutting insights │
│  Writes to ~/.claude/dataforge/knowledge/                   │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ARCHITECT PHASE (dataforge-architect)                      │
│  Spawns expert agents in parallel:                          │
│    df-expert-datascientist   df-expert-mle                  │
│    df-expert-statistician    df-expert-dataeng              │
│    df-expert-airesearcher    df-expert-mlops                │
│    df-expert-<domain>  (auto-detected)                      │
│  Each reads its KB slice, returns ExpertRecommendation      │
│  df-expert-lead consolidates -> architecture_plan.json      │
│  Mode gate: ask | semi (conf>=0.8) | auto                   │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  TABULAR PIPELINE (df-pipeline)                      │
│                                                             │
│  ingest -> raw validate -> STRATIFIED HOLDOUT (sentinel)    │
│         -> Phase A row cleanup                              │
│         -> Phase B df-feature-column N parallel             │
│              (returns transformer SPECS, not mutated CSVs)  │
│         -> Phase C cross-column transforms                  │
│         -> build_pipeline.py:                               │
│              fit pipeline_tree.pkl                          │
│              fit pipeline_linear.pkl    (sentinel)          │
│         -> validate_features.py on pipeline.transform()     │
│              corr > 0.95 -> HARD STOP                       │
│         -> df-train-model N parallel (each loads its        │
│              family's pipeline pickle, transforms inside)   │
│         -> df-evaluate -> leaderboard.json                  │
│         -> df-interpret + df-visualize (parallel)           │
│         -> df-deploy (joblib.load + .transform)      │
│         -> df-report                                 │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PERSISTENCE                                                │
│  <project>/memory/        experiments, decisions, ...       │
│  <project>/knowledge/     per-project KB snapshot            │
│  <project>/artifacts/     pipeline pickles                  │
│  ~/.claude/dataforge/     global KB + config                │
└─────────────────────────────────────────────────────────────┘
```

---

## Subsystems

### 1. Router and project-type detection

- **`skills/dataforge/SKILL.md`** parses `/dataforge <verb>` and dispatches.
- **`scripts/project_type_detect.py`** sniffs the input path and returns
  `{track, subtype, confidence, ambiguous, counts, reason}`.
  - Single file: extension drives the decision (CSV → tabular, image → dl, PDF → rag, ...).
  - Directory: walks up to 4 levels deep / 2000 files, classifies by file family.
  - Strong single-family signals (≥60% by count) yield high confidence.
  - Mixed contents return `ambiguous=true` with the largest family chosen, so the router can `AskUserQuestion`.
- The track skills (`dataforge-tabular`, `dataforge-dl`, `dataforge-rag`) are the entry points after dispatch. In v0.4.0 only `dataforge-tabular` is implemented; the other two are stubs that print the roadmap.

### 2. Knowledge base

The KB lives at `~/.claude/dataforge/knowledge/` and is structured by namespace.

```
knowledge/
├── meta.json                 # version, TTLs, last_refresh, last_seed_at, areas
├── sources.json              # whitelist + fetch state
├── libraries/{tabular,dl,rag,common}/<lib>.live.md
├── track/{tabular,dl,rag}/{techniques,pitfalls}.live.md
├── domain/<name>/<file>.live.md
├── role/<name>/<file>.live.md
├── shared/cross-cutting.md
└── index.md
```

**Loader precedence** when a skill or agent reads "leakage patterns":

1. `<project>/knowledge/...live.md` (per-run snapshot)
2. `~/.claude/dataforge/knowledge/...live.md` (global live)
3. `references/seed-knowledge/...md` (seed fallback, always present)

Live entries **extend** seeds; the seed fallback guarantees DataForge works even
with an empty KB.

**Schemas (in `schema/`):**

- `sources.json` — whitelist of fetch sources with `id`, `url`, `category`,
  `area`, `track`, `tier`, `ttl_days`, `last_fetched`, `last_hash`, `enabled`.
- `knowledge-entry.json` — a single knowledge unit produced by researchers:
  `id`, `title`, `summary`, `body`, `code_example`, `source_url`, `tier`,
  `category`, `area`, `track`, `kind` (`new_api|deprecation|best_practice|pitfall|technique|benchmark|case_study`),
  `applies_to_versions`, `deprecation_replaces`, `confidence`.

**Refresh flow:**

1. `df-learn` (skill) computes which areas are stale from `meta.json` and `sources.json` TTLs.
2. Spawns N invocations of the relevant researcher agent type in **one message**:
   - `df-researcher-library` (one per stale library)
   - `df-researcher-domain` (one per enabled domain)
   - `df-researcher-role` (one per enabled role)
3. Each invocation writes ONLY to its own namespace (e.g., `libraries/polars.live.md`). Disjoint targets → no locks.
4. After all return, `scripts/merge_knowledge.py` extracts cross-cutting insights, writes `shared/cross-cutting.md`, updates `meta.json`, rebuilds `index.md`.

**Bootstrap:** `scripts/seed_kb.py` copies `references/seed-knowledge/` into
the live KB as `*.live.md` files. Idempotent; `--force` re-seeds. Updates
`meta.json` per area with `seeded_at` and `source: "seed"`.

**Bundled seed knowledge (v0.4.0):**

- 7 domains: real-estate, finance, healthcare, retail, marketing, manufacturing, social
- 6 active roles: data-scientist, ml-engineer, data-engineer, mlops, statistician, ai-researcher
- 8 tabular libraries: sklearn, xgboost, lightgbm, catboost, polars, pandas, optuna, shap

Each seed file has YAML frontmatter (`area`, `category`, `track`, `seeded_at`,
`refresh_command`, `applies_to_versions`) so a researcher can replace it modularly.

### 3. Architect phase

A new phase between project setup and execution. Skill: `dataforge-architect`.

**Flow:**

1. Track + subtype already known from project_type_detect.
2. `pre-pipeline-refresh.py` hook ensures relevant KB areas are fresh.
3. `dataforge-architect` spawns the track's reviewer experts **in parallel in one message**. Each expert reads its KB slice + project context.
4. Each expert returns an `ExpertRecommendation`:
   `{expert, role, proposed_approach, alternatives, rationale, kb_citations, confidence}`
5. `df-expert-lead` consolidates into `architecture_plan.json`:
   `{track, subtype, chosen_approach, alternatives_considered, rationale, expert_recommendations, expert_citations, fallback_plan, confidence_score, complexity_score, kb_freshness}`
6. **Mode gate** decides how the plan reaches execution:
   - `ask` (default) — `AskUserQuestion`, user can approve / edit / redirect.
   - `semi` — auto-proceed when `confidence_score >= 0.8` AND experts agree AND KB is fresh, else fall through to `ask`.
   - `auto` — always auto-proceed; flagged in the report if `confidence_score < 0.5`.

**Schema:** `schema/architecture-plan.json` is **track-agnostic**. `chosen_approach`
is a `oneOf` over `tabular_approach`, `dl_approach`, `rag_approach` definitions.
DL and RAG approach shapes are defined in v0.4.0 (even though execution lands later)
so the schema does not need to change in v0.5/v0.6.

### 4. Tabular pipeline discipline

The structural fix that addresses the LEARNINGS.md leakage and train/serve skew.

**Execution order (enforced by hooks):**

| Step | What happens | Sentinel | Enforcement |
|------|-------------|----------|-------------|
| 1 | ingest | — | — |
| 2 | raw validate | `.validation_passed` | `pre-train-validate.sh` |
| 3 | **stratified test holdout** | `.test_split_saved` | `pre-fit-guard.py` blocks any fit before this |
| 4 | Phase A row cleanup | — | — |
| 5 | Phase B `df-feature-column` parallel — returns transformer SPECS, not mutated CSVs | — | output contract |
| 6 | Phase C cross-column transformer specs | — | — |
| 7 | `build_pipeline.py` fits `pipeline_tree.pkl` and `pipeline_linear.pkl` on **train only** | `.pipeline_fitted` | hook |
| 8 | `validate_features.py` runs on `pipeline.transform(X_train)` | — | exit 2 = HARD STOP if corr > 0.95 |
| 9 | `df-train-model` — N models in parallel, each loads its family's pipeline, `.transform()` internally | — | `pre-train-pipeline-gate.sh` blocks training before sentinels |
| 10 | `df-evaluate`, `df-interpret`, `df-visualize` | — | — |
| 11 | `df-deploy` — generated app must `joblib.load` + `pipeline.transform()` | — | `pre-deploy-lint.py` blocks app code that re-implements transformers |
| 12 | `df-report` | — | — |

**Phase B output contract** changes in v0.4.0: `df-feature-column` returns a
JSON spec describing a sklearn transformer + its column targets, not a mutated
column CSV. The orchestrator collects specs into two `ColumnTransformer`s
(`pipeline_tree`, `pipeline_linear`) and fits each.

**Pipeline split:**

- `pipeline_tree` — for HistGradientBoosting, XGBoost, LightGBM, CatBoost, RF: ordinal/native categorical, no scaling, NaN passthrough.
- `pipeline_linear` — for Ridge, Lasso, Logistic, LinearSVC: median imputation, OneHot, StandardScaler, optional polynomial terms.

**Why this matters:**

- No leakage via imputers / encoders / scalers — all fit on train only.
- No train/serve skew — the deploy app does not own the transforms; it calls `.transform()` on the same fitted pipeline used for evaluation.
- Reproducibility — `pipeline_*.pkl` + `test.csv` row hash in `dataforge.config.json` produces identical numbers forever.

### 5. Expert agents

DataForge has **two expert layers**:

**v0.3.0 review experts** (still active) — review a stage's output and either approve, flag, or block:

| Agent | Role | Trigger |
|-------|------|---------|
| `df-expert-lead` | Lead — collates findings, applies auto-corrections, returns verdict | every checkpoint |
| `df-expert-datascientist` | Senior DS methodology | `expert_triage.py` complexity score |
| `df-expert-statistician` | Senior statistician | complexity score |
| `df-expert-{healthcare,finance,marketing,retail,social,manufacturing}` | 6 domain experts | `domain_detect.py` confidence ≥ 0.5 |

**v0.4.0 architect experts** — make the call BEFORE execution, in the architect phase:

| Agent | Role | Track |
|-------|------|-------|
| `df-expert-mle` | ML Engineer — serving, optimization, inference cost | cross-track |
| `df-expert-dataeng` | Data Engineer — pipelines, schemas, quality | cross-track |
| `df-expert-mlops` | MLOps — monitoring, drift, deployment reliability | cross-track |
| `df-expert-airesearcher` | AI Researcher — SOTA awareness, cross-track inputs | cross-track |

Same agents serve both phases — in the architect phase they propose; at review
checkpoints they critique. The pairing rule: every expert is paired with a
researcher invocation that populates its KB slice before it speaks.

**Expert triage** (`scripts/expert_triage.py`) decides depth at each stage:

```
score < 0.2  -> skip   (no review, 0 token cost)
score 0.2-0.5 -> light  (lead expert only)
score > 0.5  -> full   (methodology + domain + lead)
```

Always full when `--production`, first run, or `--domain` flag set.

### 6. Researcher agents

Three **agent type definitions**, many parallel invocations. Same pattern as
`df-feature-column` (one type, N invocations per column).

| Agent type | Parameters | Writes to | Spawn count |
|-----------|------------|-----------|-------------|
| `df-researcher-library` | `{library, sources, since}` | `libraries/<track>/<lib>.live.md` | one per stale library |
| `df-researcher-domain` | `{domain, sources, web_search}` | `domain/<name>/<file>.live.md` | one per enabled domain |
| `df-researcher-role` | `{role, sources, web_search}` | `role/<name>/<file>.live.md` | one per enabled role |

Why not 15+ files? They would duplicate fetch/extract logic. The per-library
configuration lives in `sources.json`, not in agent files.

**Contract:** JSON-in, JSON-out. Each invocation writes ONLY to its own
namespace. Output JSON reports `{files_written, new_items, updated_items,
sources_fetched, sources_failed, next_suggested_refresh}`.

**Parallelism:** the orchestrator skill emits a single assistant message with
multiple `Agent` tool calls (batch ≤10). Additional waves if the stale set
exceeds the cap.

### 7. Hooks

Hooks run in the harness, not inside the LLM. They cannot be bypassed by
prompt injection or "the model decided to skip this step."

| Hook | Type | Trigger | Purpose | New in |
|------|------|---------|---------|--------|
| `post-generate-lint.py` | PostToolUse | After Write/Edit of `.py` | pyflakes check on generated code | v0.2 |
| `pre-train-validate.sh` | PreToolUse (Bash) | Before `train.py` | Block training if raw validation didn't pass | v0.2 |
| `pre-pipeline-refresh.py` | UserPromptSubmit | `/dataforge run`, `/dataforge analyze` | Auto-refresh stale KB areas before pipeline starts | **v0.4** |
| `pre-codegen-freshness.py` | PreToolUse (Write/Edit) | Writing `.py` with tracked imports | Warn (or block) if `libraries/<lib>.live.md` is stale | **v0.4** |
| `pre-fit-guard.py` | PreToolUse (Write) | Generating any `.fit()` call | Block unless `.test_split_saved` exists | **v0.4** |
| `pre-train-pipeline-gate.sh` | PreToolUse (Bash) | Before `train.py` | Block unless `.pipeline_fitted` + leakage gate passed | **v0.4** |
| `pre-deploy-lint.py` | PreToolUse (Write) | Generating deploy app | Block app code that re-implements scalers/encoders/imputers | **v0.4** |

### 8. Memory

Per-project, persisted in `memory/`:

| File | Purpose |
|------|---------|
| `experiments.json` | Run history (configs, metrics, artifact paths, git SHA) |
| `decisions.md` | Why each choice was made (human-readable) |
| `failed_transforms.json` | Transforms/models that failed — skipped on resume |
| `best_pipelines.json` | Winning configs — seeds future runs |
| `architecture_plan.json` | What the architect phase decided |

`memory_read.py` and `memory_write.py` use Windows-safe locking (`msvcrt`
fallback) — the same pattern is reused for `meta.json` updates.

---

## Schemas

| Schema | Purpose | Status |
|--------|---------|--------|
| `schema/project-config.json` | Per-project config — `project_type`, `project_subtype`, `architect_mode`, `test_split`, `pipeline_artifacts`, `knowledge_snapshot_*` | v0.3 + extended in v0.4 |
| `schema/expert-output.json` | `expert_output` (per-expert findings) and `lead_verdict` (consolidated) | v0.3 |
| `schema/memory-schema.json` | `experiments.json`, `best_pipelines.json` shapes | v0.3 |
| `schema/sources.json` | KB source whitelist with TTL and fetch state | **v0.4 new** |
| `schema/knowledge-entry.json` | Researcher output unit | **v0.4 new** |
| `schema/architecture-plan.json` | Track-agnostic architect phase output | **v0.4 new** |

---

## Forward compatibility (v0.5 / v0.6)

These v0.4.0 decisions are load-bearing for future tracks and must not change:

- `project-config.json` already has `project_type`, `project_subtype`, `architect_mode`.
- `architecture-plan.json` `chosen_approach` is `oneOf {tabular,dl,rag}_approach` — DL and RAG shapes are already defined.
- Router dispatches on `project_type`. v0.4 implements only the tabular branch but DL/RAG branches exist and route to stubs.
- `project_type_detect.py` already returns correct results for image folders, audio folders, and document folders.
- KB layout has `track/dl/`, `track/rag/`, `libraries/dl/`, `libraries/rag/` directories as empty skeletons.
- Researcher agents are parameterized — adding DL libraries or RAG roles requires only `sources.json` edits, no new agent files.
- Expert agent contract (`ExpertRecommendation` shape) is generic — DL and RAG experts will use the same JSON shape.
- `dataforge-architect` accepts any track passed in; not hardcoded to tabular.
- Setup wizard asks which tracks the user wants enabled (tabular always yes; DL/RAG default off in v0.4 since stubs).

---

## Roadmap

| Version | Theme |
|---------|-------|
| v0.1.0 | Initial release |
| v0.2.0 | Modular skill + workflow architecture |
| v0.3.0 | Expert agent layer |
| **v0.4.0** | **Continuous learning + foundational fixes + multi-track foundation (current)** |
| v0.5.0 | Deep Learning track (CV, NLP, time-series, audio, multimodal) |
| v0.6.0 | RAG track (text, multimodal, doc-KB, agentic) |
| v0.7.0+ | Cron-based KB refresh, cross-project insight sharing |
