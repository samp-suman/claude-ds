# DataForge — Sub-Agents Reference

Sub-agents live in `~/.claude/agents/` (installed from this directory via `install.sh`).
Each is a Markdown file that Claude Code loads as a specialized agent.

## How Agents Work

The main orchestrator (`skills/dataforge/SKILL.md`) spawns these agents using
Claude Code's `Agent` tool. Multiple agents can run **simultaneously** — this is
how DataForge achieves parallel EDA and parallel model training.

Agents communicate via a strict **JSON-in → JSON-out contract**: the orchestrator
passes task parameters in the message, the agent returns a JSON result as its
last output line.

---

## Agent Catalog

### df-ingest

**File:** `df-ingest.md`
**Purpose:** Loads a dataset from any supported source into `data/raw/`
**Called by:** Orchestrator at Step 2
**Parallelism:** Sequential (one dataset at a time)
**Output:**
```json
{"agent": "df-ingest", "status": "success", "raw_path": "...", "n_rows": 0, "n_cols": 0}
```

---

### df-validate

**File:** `df-validate.md`
**Purpose:** Runs all quality gates. Signals HARD STOP (exit_code 2) on critical failures.
**Called by:** Orchestrator at Step 3
**Parallelism:** Sequential — must complete before any other stage
**Exit codes:** 0 (pass), 1 (warnings), 2 (HARD STOP)
**Output:**
```json
{"agent": "df-validate", "exit_code": 0, "status": "PASS", "n_warnings": 0}
```

---

### df-eda-column ⚡ PARALLEL

**File:** `df-eda-column.md`
**Purpose:** EDA for a single column — stats JSON + distribution plot
**Called by:** Orchestrator at Step 5, spawned **N times simultaneously** (one per column)
**Batch size:** ≤ 10 parallel at once
**Output:**
```json
{
  "agent": "df-eda-column",
  "column": "age",
  "col_type": "numeric",
  "null_pct": 2.5,
  "recommended_transforms": ["median_imputation", "standard_scaling"]
}
```

---

### df-feature-column ⚡ PARALLEL

**File:** `df-feature-column.md`
**Purpose:** Applies EDA-recommended transforms to a single column
**Called by:** Orchestrator at Step 6, spawned **N times simultaneously**
**Batch size:** ≤ 10 parallel at once
**Output:**
```json
{
  "agent": "df-feature-column",
  "column": "age",
  "transforms_applied": ["median_imputation", "standard_scaling"],
  "dropped": false
}
```

---

### df-train-model ⚡⚡ PARALLEL (biggest impact)

**File:** `df-train-model.md`
**Purpose:** Trains one ML model with 5-fold CV, saves .pkl + metrics JSON
**Called by:** Orchestrator at Step 7, **ALL models spawned in one parallel batch**
**Models:** xgboost, lightgbm, randomforest, logistic/linear, catboost, ridge, lasso
**Output:**
```json
{
  "agent": "df-train-model",
  "model": "lightgbm",
  "status": "success",
  "metrics": {"roc_auc": 0.923, "f1": 0.887},
  "artifact_path": "src/models/lightgbm.pkl"
}
```

---

### df-evaluate

**File:** `df-evaluate.md`
**Purpose:** Ranks all trained models, writes leaderboard, updates memory
**Called by:** Orchestrator at Step 8 (after all training agents complete)
**Output:**
```json
{
  "agent": "df-evaluate",
  "best_model": "lightgbm",
  "best_metric": "roc_auc",
  "best_score": 0.923,
  "leaderboard_path": "src/models/leaderboard.json"
}
```

---

### df-interpret ⚡ PARALLEL with df-visualize

**File:** `df-interpret.md`
**Purpose:** SHAP analysis + feature importance plots for the best model
**Called by:** Orchestrator at Step 9 (parallel with df-visualize)
**Output:**
```json
{
  "agent": "df-interpret",
  "top_features": ["age", "fare", "pclass"],
  "artifacts": {"shap_summary": "reports/shap_summary.png"}
}
```

---

### df-visualize ⚡ PARALLEL with df-interpret

**File:** `df-visualize.md`
**Purpose:** Generates confusion matrix, ROC curve, residual plot, pairplot
**Called by:** Orchestrator at Step 9 (parallel with df-interpret)
**Output:**
```json
{
  "agent": "df-visualize",
  "artifacts": {"confusion_matrix": "reports/confusion_matrix.png"}
}
```

---

### df-deploy

**File:** `df-deploy.md`
**Purpose:** Generates a complete Streamlit or FastAPI app in `app/`
**Called by:** Orchestrator at Step 10
**Output:**
```json
{
  "agent": "df-deploy",
  "target": "streamlit",
  "run_command": "cd app && streamlit run app.py"
}
```

---

### df-report

**File:** `df-report.md`
**Purpose:** Assembles final HTML/PDF report + writes inference.py + README
**Called by:** Orchestrator at Step 11
**Output:**
```json
{
  "agent": "df-report",
  "html_path": "reports/final_report.html",
  "pdf_path": "reports/final_report.pdf"
}
```

---

### df-monitor

**File:** `df-monitor.md`
**Purpose:** Detects data drift and concept drift between training and new data
**Called by:** User via `/dataforge monitor <project-dir> --new-data <path>`
**Output:**
```json
{
  "agent": "df-monitor",
  "drift_detected": false,
  "recommendation": "stable|monitor|retrain"
}
```

---

## Parallel Execution Diagram

```
Step 5 — EDA:
  [df-eda-column: col1] [df-eda-column: col2] [df-eda-column: col3] ... (parallel)

Step 6 — Features:
  [df-feature-column: col1] [df-feature-column: col2] ... (parallel)

Step 7 — Training:
  [df-train-model: xgboost] [df-train-model: lightgbm]
  [df-train-model: randomforest] [df-train-model: logistic]  (ALL simultaneous)

Step 9 — Interpret + Visualize:
  [df-interpret: lightgbm] [df-visualize: all plots]  (simultaneous)
```

---

## Adding a New Agent

1. Create `agents/df-{name}.md` following the template below
2. Add a spawn instruction in `skills/dataforge/SKILL.md`
3. Run `bash install.sh`
4. Update this README and `CHANGELOG.md`

### Agent Template

```markdown
---
name: df-{name}
description: Brief description (shown in Claude Code agent picker)
tools: Read, Write, Bash
---

# DataForge — {Name} Agent

## Inputs
- param1: description
- param2: description

## Process
[step by step instructions]

## Output
{json block — always as final line}
```
