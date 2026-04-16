# Changelog

All notable changes to DataForge are documented here.
Format: [Semantic Versioning](https://semver.org/) — `## [version] YYYY-MM-DD`

---

## Roadmap

### v0.4.0 — Continuous Learning + Foundational Fixes + Multi-Track Foundation (in progress)
- Knowledge base subsystem with researcher agents, refresh hooks, setup wizard
- Architect phase with expert recommendations and ask/semi/auto modes
- Pipeline-based DS-process discipline (fitted sklearn Pipelines, no train/serve skew)
- LEARNINGS.md fixes: post-FE leakage gate, model-specific preprocessing, held-out test set
- Three-track architecture (tabular implemented; dl/rag skeletons for v0.5/v0.6)

---

## [0.4.0-alpha] in progress — docs: user-friendly README overhaul

### Changed
- `README.md` — Rewritten for end-users: clear setup, quick start, all commands, supported inputs, quality gates, extending guide. Removed version status/roadmap (kept in CHANGELOG)
- `skills/dataforge/README.md` — Rewritten with routing table and links to each skill

### Added
- Per-skill README.md files (10 new): dataforge-preprocess, dataforge-eda, dataforge-modeling, dataforge-experiment, dataforge-deploy, dataforge-report, dataforge-pipeline, dataforge-analysis, dataforge-learn, dataforge-knowledge — each with usage examples and descriptions
- Main README links to each skill README in the "Skills reference" table

---

## [0.4.0-alpha] in progress — Multi-Track Foundation

### Added (forward-compat foundation)

**Schemas**
- `schema/sources.json` — knowledge-source whitelist with TTL, tier, fetch state
- `schema/architecture-plan.json` — track-agnostic architect-phase output (tabular/dl/rag oneOf)
- `schema/knowledge-entry.json` — researcher-output knowledge unit with kind/tier/track
- `schema/project-config.json` — added `project_type`, `project_subtype`, `architect_mode`, `knowledge_snapshot_path/version`, `primary_metric_user_chosen`, `architecture_plan_path`, `test_split`, `pipeline_artifacts`; new pipeline_status flags (`architect`, `test_split`, `pipeline_fit`)

**Scripts**
- `scripts/project_type_detect.py` — track + subtype detection from input path signals (tabular/dl/rag); ships in v0.4.0 so v0.5/v0.6 don't retrofit detection
- `scripts/seed_kb.py` — modular KB seeder; copies `references/seed-knowledge/` into `~/.claude/dataforge/knowledge/` as `*.live.md`; supports `--force`, `--dry-run`; updates `meta.json` per area. Fixed: library area key now resolves to file stem (e.g. `sklearn`) instead of collapsing every library under `tabular`.
- `scripts/seed_sources.py` — parses `references/seed-sources/**/*.md` and populates `~/.claude/dataforge/knowledge/sources.json` with the whitelist; idempotent, preserves runtime state fields
- `scripts/learn_orchestrator.py` — backend for `/dataforge-learn`. `plan` subcommand reads `meta.json` + `sources.json` + config, computes stale areas, emits spawn manifest in parallel waves (<=10 per wave). `status` subcommand reports per-area freshness
- `scripts/merge_knowledge.py` — post-researcher merge: walks every `*.live.md`, parses embedded `json knowledge-entry` fenced blocks, dedupes by id, extracts cross-cutting entries to `shared/cross-cutting.md`, rebuilds `index.md`, patches `meta.json` (`last_refreshed_at`, `entry_count`, `source: researcher`) and `sources.json` (`last_fetched`, `last_hash`, `last_status`) atomically
- `scripts/knowledge_query.py` — read-only backend for `/dataforge-knowledge`: `show <area>`, `search <query>`, `status`, `diff`

**Researcher Agents (3)**
- `agents/df-researcher-library.md` — fetches library changelogs/whatsnew pages, extracts knowledge-entry items, writes to `libraries/<track>/<lib>.live.md`; supports optional WebSearch fallback
- `agents/df-researcher-domain.md` — fetches domain research/case studies, writes to `domain/<name>/techniques.live.md`
- `agents/df-researcher-role.md` — fetches thought-leader content per role, writes to `role/<name>/techniques.live.md`

**Skills (2)**
- `skills/dataforge-learn/SKILL.md` — `/dataforge-learn [all|library|domain|role] [--area <name>] [--source <url>] [--web-search] [--force]`: calls orchestrator, spawns researchers in parallel waves, calls merge, prints summary
- `skills/dataforge-knowledge/SKILL.md` — `/dataforge-knowledge [show|search|status|diff] [area|query]`: read-only wrapper around `knowledge_query.py`

**Seed sources** (`references/seed-sources/`)
- `libraries/tabular.md` — 8 libraries, 16 URLs (sklearn, xgboost, lightgbm, catboost, polars, pandas, optuna, shap)
- `domain/domains.md` — 7 domains, 14 URLs
- `role/roles.md` — 6 roles, 18 URLs

**Knowledge Base skeleton** (`~/.claude/dataforge/knowledge/`)
- Track-aware layout: `libraries/{tabular,dl,rag,common}`, `track/{tabular,dl,rag}`, `domain/`, `role/`, `shared/`
- `meta.json`, `sources.json`, `index.md`, `shared/cross-cutting.md`
- Empty `track/dl/{cv,nlp,timeseries,audio,multimodal}` and `track/rag/{text,multimodal,doc-kb,agentic}` namespaces reserved for v0.5/v0.6

**Seed knowledge** (`references/seed-knowledge/`) — 21 baseline files ready to refresh
- 7 domains: real-estate, finance, healthcare, retail, marketing, manufacturing, social
- 6 active roles: data-scientist, ml-engineer, data-engineer, mlops, statistician, ai-researcher
- 8 tabular libraries: sklearn, xgboost, lightgbm, catboost, polars, pandas, optuna, shap
- Every seed file has frontmatter (`area`, `seeded_at`, `refresh_command`, `applies_to_versions`) so researcher agents can update modularly

---

## [0.3.0] 2026-04-10 — Expert Agent Layer

### Added

**Scripts**
- `scripts/domain_detect.py` — Auto-detect dataset domain from column names, filename patterns, value patterns. 6 domains: healthcare, finance, marketing, retail, social, manufacturing. Falls back to "general" if confidence < 0.5
- `scripts/expert_triage.py` — Compute complexity score per pipeline stage (preprocessing/eda/modeling), decide expert depth: skip (<0.2), light (0.2-0.5), full (>0.5). Force full if --production, --first-run, or --domain-flag

**Expert Agents (9)**
- `agents/df-expert-lead.md` — Lead expert: collates all findings, resolves conflicts, applies auto-corrections, returns verdict (approve/flag/block)
- `agents/df-expert-datascientist.md` — Senior Data Scientist (10+ yr): pipeline review, model selection, overfitting detection, bias analysis
- `agents/df-expert-statistician.md` — Senior Statistician (10+ yr): distribution assumptions, hypothesis testing, imputation validity, data leakage
- `agents/df-expert-healthcare.md` — Healthcare domain: clinical features, diagnostic thresholds (HbA1c, BMI, vitals), HIPAA, confounders
- `agents/df-expert-finance.md` — Finance domain: risk scoring, fraud detection, regulatory compliance, temporal leakage, fair lending
- `agents/df-expert-marketing.md` — Marketing domain: CLV, churn modeling, RFM segmentation, attribution, A/B test validity
- `agents/df-expert-retail.md` — Retail domain: demand forecasting, price elasticity, basket analysis, seasonality, stockout handling
- `agents/df-expert-social.md` — Social media domain: engagement metrics, sentiment analysis, bot detection, network effects
- `agents/df-expert-manufacturing.md` — Manufacturing domain: sensor data, predictive maintenance, SPC, yield optimization, anomaly detection

**Domain Reference Docs (6)**
- `references/domain-healthcare.md` — Clinical feature ranges, KPIs, feature engineering recipes, common pitfalls
- `references/domain-finance.md` — Credit scoring tiers, fraud metrics (KS, Gini), regulatory considerations, temporal validation
- `references/domain-marketing.md` — RFM framework, churn definition, CLV calculation, cohort analysis, campaign metrics
- `references/domain-retail.md` — Demand forecasting, price elasticity, basket analysis, inventory signals, seasonality
- `references/domain-social.md` — Engagement metrics, sentiment analysis, bot detection, virality signals, text preprocessing
- `references/domain-manufacturing.md` — OEE, SPC (Cpk/Ppk), sensor aggregation, predictive maintenance, Nelson rules

**Schema**
- `schema/expert-output.json` — JSON Schema for expert finding contract (severity, auto_correctable, correction_action) and lead verdict contract (actions_taken, advisories, blocks)

### Changed
- `skills/dataforge-pipeline/SKILL.md` — Added 3 expert checkpoints (after preprocessing, EDA, modeling) with triage-based triggering
- `skills/dataforge-analysis/SKILL.md` — Added 1 expert checkpoint (after EDA)
- `skills/dataforge-preprocess/SKILL.md` — Added optional expert checkpoint (standalone mode)
- `skills/dataforge-modeling/SKILL.md` — Added optional expert checkpoint (standalone mode)
- `docs/ARCHITECTURE.md` — Updated layer diagram with expert layer, added expert system documentation, replaced roadmap
- `agents/README.md` — Added 9 expert agents to inventory, expert triage flow diagram

### Architecture Decisions
- Adaptive triage over blanket review — experts only run when complexity warrants it, saving tokens
- Lead expert spawned fresh each checkpoint to avoid bias accumulation
- Domain/methodology experts spawned once, continued via SendMessage across stages
- Domain auto-detection runs once, result cached for all subsequent checkpoints
- Expert findings cached in `{OUTPUT_DIR}/data/interim/expert_cache/` for cross-stage context

---

## [0.2.0] 2026-04-10 — Modular Skill + Workflow Restructure

### Breaking Changes
- Monolithic `skills/dataforge/SKILL.md` replaced with modular skill architecture
- Scripts moved from `skills/dataforge/scripts/` to top-level `scripts/`
- References moved from `skills/dataforge/references/` to top-level `references/`
- Schema moved from `skills/dataforge/schema/` to top-level `schema/`
- Hooks moved from `skills/dataforge/hooks/` to top-level `hooks/`
- Extensions moved from `skills/dataforge/extensions/` to top-level `extensions/`
- `requirements.txt` moved from `skills/dataforge/` to repo root
- All agent script paths updated: `~/.claude/skills/dataforge/scripts/` -> `~/.claude/scripts/`
- Install layout changed: scripts, references, schema, hooks now install to `~/.claude/` directly

### Added

**Atomic Skills (skills/dataforge-*/)**
- `dataforge-preprocess/SKILL.md` — Data ingestion, validation, profiling, feature engineering
- `dataforge-eda/SKILL.md` — Exploratory data analysis (parallel per-column + global + domain insights)
- `dataforge-modeling/SKILL.md` — Model training, evaluation, SHAP interpretation, visualization
- `dataforge-experiment/SKILL.md` — Experiment tracking, comparison, drift monitoring
- `dataforge-deploy/SKILL.md` — Streamlit/FastAPI/Flask app generation
- `dataforge-report/SKILL.md` — HTML/PDF report generation

**Workflows (skills/dataforge-analysis/, skills/dataforge-pipeline/)**
- `dataforge-analysis/SKILL.md` — Data Analysis workflow: preprocess -> EDA -> report
- `dataforge-pipeline/SKILL.md` — Full pipeline workflow: all skills in sequence

**New Agent**
- `df-eda-global.md` — Dedicated global EDA agent (split from df-eda-column --mode=global)

**New Commands**
- `/dataforge analyze <dataset>` — Data analysis without modeling
- `/dataforge compare <project-dir>` — Compare experiments across runs
- `/dataforge-preprocess ingest|validate|profile|features` — Preprocessing sub-commands
- `/dataforge-eda column|global|summary` — EDA sub-commands
- `/dataforge-modeling train|evaluate|interpret|visualize` — Modeling sub-commands
- `/dataforge-experiment status|compare|monitor|history` — Experiment sub-commands

**Documentation**
- `CLAUDE.md` — Root project constitution with full skill/workflow reference
- `docs/ARCHITECTURE.md` — System design with layer diagram and data flow
- `docs/COMMANDS.md` — Complete command reference for all skills and workflows

### Changed
- `skills/dataforge/SKILL.md` — Rewritten as pure router (~130 lines, down from 400)
- `install.sh` — Rewritten for new modular layout (installs skills, scripts, refs, schema, hooks)
- `agents/README.md` — Updated for new skill-based architecture
- `README.md` — Updated for v0.2.0 architecture

### Architecture Decisions
- Flat skill directories (`skills/dataforge-eda/`, not nested) — matches Claude Code discovery
- Scripts unchanged — all 14 Python scripts are standalone CLI tools, only invocation paths changed
- Workflows reference skills by name — no logic duplication
- Each skill independently invocable with `user-invokable: true`
- Router is convenience layer, not required gateway

---

## [0.1.0] 2026-04-04 — Initial Release

### Added

**Core Skill (skills/dataforge/)**
- `SKILL.md` — Main orchestrator: 8 user commands, 12-step full pipeline, parallel execution rules, quality gate logic, memory contract, error handling table
- `requirements.txt` — All Python dependencies pinned (pandas, scikit-learn, xgboost, lightgbm, catboost, shap, matplotlib, seaborn, joblib, pyflakes, jinja2, etc.)

**Python Scripts (skills/dataforge/scripts/)**
- `ingest.py` — Multi-format data loader: CSV, TSV, JSON, JSONL, Parquet, Excel, SQLite, SQLAlchemy URI, HTTP URL, Pickle
- `profile.py` — Dataset profiler: per-column stats, problem type auto-detection, correlation with target, class balance
- `validate.py` — Quality gate with exit codes 0/1/2: min samples, target existence, target variance, target leakage (≥0.99 correlation), class imbalance, high missing, duplicates, constant columns, ID-like columns
- `eda.py` — Per-column EDA (numeric, categorical, datetime) + global mode (correlation heatmap, target distribution, missing matrix)
- `features.py` — Per-column feature transforms: median/mode imputation, log/yeo-johnson transforms, standard scaling, clip outliers, one-hot/label/target encoding, datetime extraction
- `train.py` — Model registry CLI: XGBoost, LightGBM, RandomForest, Logistic/Linear, Ridge, Lasso, CatBoost, SVM (classification + regression + clustering). 5-fold CV, artifact saving
- `evaluate.py` — Model ranking by primary metric, leaderboard JSON, comparison bar chart
- `interpret.py` — SHAP TreeExplainer/LinearExplainer/KernelExplainer, beeswarm + bar chart + native feature importance
- `visualize.py` — Confusion matrix, ROC curve, residual plot, prediction vs actual, pairplot
- `deploy_detect.py` — Heuristic deployment target selection: Streamlit / FastAPI / Flask
- `report.py` — Jinja2 HTML report with embedded images (EDA, model leaderboard, SHAP, eval plots), optional WeasyPrint PDF
- `memory_read.py` — Reads all memory files, returns consolidated JSON with summary
- `memory_write.py` — Concurrent-safe writes (fcntl/msvcrt locking) with append/update/merge/reset modes

**Reference Docs (skills/dataforge/references/)**
- `model-catalog.md` — Model selection table per problem type, hyperparameter starting points, dataset size rules
- `feature-recipes.md` — Decision tree for transform selection, encoding reference, imputation guide
- `metric-guide.md` — When to use ROC-AUC vs F1 vs accuracy vs R² vs RMSE; interpretation ranges
- `deploy-targets.md` — Streamlit vs FastAPI vs Flask decision matrix, Docker reference, cloud deployment notes
- `leakage-patterns.md` — 5 leakage pattern types with examples and detection methods
- `quality-gates.md` — Hard stop thresholds, warning thresholds, override protocol

**Schema (skills/dataforge/schema/)**
- `memory-schema.json` — JSON Schema for experiments, best_pipelines, failed_transforms memory files
- `project-config.json` — JSON Schema for dataforge.config.json (written into generated projects)

**Hooks (skills/dataforge/hooks/)**
- `post-generate-lint.py` — PostToolUse hook: pyflakes check on generated Python files inside DataForge projects
- `pre-train-validate.sh` — PreToolUse hook: blocks train.py if .validation_passed sentinel is absent

**Extensions**
- `extensions/kaggle/` — Kaggle dataset download via kaggle API
- `extensions/mlflow/` — MLflow experiment tracking integration

**Sub-Agents (agents/)**
- `df-ingest.md` — Data ingestion agent
- `df-validate.md` — Validation gate agent (exit code 0/1/2)
- `df-eda-column.md` — Per-column EDA agent (spawned in parallel, one per column)
- `df-feature-column.md` — Per-column feature engineering agent (parallel)
- `df-train-model.md` — Per-model training agent (all models parallel in one batch)
- `df-evaluate.md` — Model ranking + leaderboard agent
- `df-interpret.md` — SHAP + feature importance agent (parallel with df-visualize)
- `df-visualize.md` — Visualization suite agent (parallel with df-interpret)
- `df-deploy.md` — Deployment app generator (Streamlit/FastAPI/Flask)
- `df-monitor.md` — Data/concept drift detection agent
- `df-report.md` — HTML/PDF report + inference.py + README assembly agent

**Install**
- `install.sh` — Copies all files to `~/.claude/skills/dataforge/` and `~/.claude/agents/`
- Hooks wired into `~/.claude/settings.json`

**Documentation**
- `README.md` — Full installation, usage, architecture overview, step-by-step guide
- `agents/README.md` — All agents explained
- `skills/dataforge/README.md` — Skill internals
- `skills/dataforge/scripts/README.md` — Each script's CLI interface
- `skills/dataforge/references/README.md` — Reference doc index
- `CHANGELOG.md` — This file

### Architecture Decisions
- Repo name: `claude-ds` (kept as-is per user preference)
- Plugin/skill name: `DataForge` (invoked as `/dataforge`)
- Skills and agents use Claude Code's native Markdown format
- Python scripts handle all computation; agent .md files handle orchestration
- Parallel execution via Claude Code's native `Agent` tool (not threads/processes)
- Memory persists in generated project folder (JSON + Markdown, no external DB)
- CLAUDE.md written into every generated project for auto-activation on next session

## [0.1.1] 2026-04-04 — Bug fixes from Titanic test

### Fixed
- `validate.py`: Replaced UTF-8 icons (✓ ⚠ ✗) with ASCII tags ([OK] [WARN] [STOP]) to fix Windows cp1252 encoding error on console output
- `profile.py` → renamed to `data_profiler.py`: Was shadowing Python's stdlib `profile` module when scripts directory was on sys.path, causing SHAP `LinearExplainer` to fail with `module 'profile' has no attribute 'run'`
- `SKILL.md`: Updated Step 4 profile command to use `data_profiler.py`
- `scripts/README.md`: Updated script name reference

### Tested
- Full pipeline verified on Titanic dataset (891 rows, 12 columns, binary classification)
- Parallel training: LightGBM, XGBoost, RandomForest, Logistic — all 4 simultaneously
- Leaderboard: Logistic Regression ranked 1st (ROC-AUC: 0.8511)
- SHAP: Top feature = Sex (SHAP=1.16) — correct for Titanic domain
- All 27 artifacts generated: EDA plots, model .pkl files, confusion matrix, ROC curve, SHAP charts, pairplot, final_report.html (569KB)
