# Changelog

All notable changes to DataForge are documented here.
Format: [Semantic Versioning](https://semver.org/) — `## [version] YYYY-MM-DD`

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
