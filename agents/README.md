# DataForge Agents

Sub-agents spawned by DataForge skills for parallel execution. Each is a Markdown
file with YAML frontmatter defining its name, description, and allowed tools.

Agents live in `~/.claude/agents/` after installation (via `bash install.sh`).

## How Agents Work

DataForge skills spawn these agents using Claude Code's `Agent` tool. Multiple
agents can run **simultaneously** -- this is how DataForge achieves parallel
EDA, parallel feature engineering, and parallel model training.

Agents follow a strict **JSON-in -> JSON-out contract**: the skill passes task
parameters in the message, the agent calls Python scripts from `~/.claude/scripts/`,
and returns a JSON result as its last output line.

---

## Agent Inventory

| Agent | Purpose | Spawned by | Parallelism |
|-------|---------|-----------|-------------|
| `df-ingest` | Load data from any format | dataforge-preprocess | Sequential |
| `df-validate` | Quality gate (exit codes 0/1/2) | dataforge-preprocess, pipeline | Sequential (gate) |
| `df-eda-column` | Per-column EDA analysis + plot | dataforge-eda | Parallel (batch <= 10) |
| `df-eda-global` | Correlation heatmap, target dist, missing matrix | dataforge-eda | Parallel with column agents |
| `df-feature-column` | Per-column feature engineering | dataforge-preprocess | Parallel (batch <= 10) |
| `df-train-model` | Train one model with 5-fold CV | dataforge-modeling | Parallel (all models at once) |
| `df-evaluate` | Rank models, write leaderboard | dataforge-modeling | Sequential |
| `df-interpret` | SHAP feature importance | dataforge-modeling | Parallel with df-visualize |
| `df-visualize` | Confusion matrix, ROC, residuals | dataforge-modeling | Parallel with df-interpret |
| `df-deploy` | Generate Streamlit/FastAPI app | dataforge-deploy | Sequential |
| `df-report` | Assemble HTML/PDF report | dataforge-report | Sequential |
| `df-monitor` | Data/concept drift detection | dataforge-experiment | Sequential |

---

## Parallel Execution Diagram

```
EDA stage:
  [df-eda-column: col1] [df-eda-column: col2] ... [df-eda-global]  (parallel)

Feature stage:
  [df-feature-column: col1] [df-feature-column: col2] ...          (parallel)

Training stage:
  [df-train-model: xgboost] [df-train-model: lightgbm]
  [df-train-model: randomforest] [df-train-model: logistic]        (ALL at once)

Post-training:
  [df-interpret: best_model] [df-visualize: all plots]             (parallel pair)
```

---

## Adding a New Agent

1. Create `agents/df-{name}.md` with frontmatter (name, description, tools)
2. Write process instructions that call scripts from `~/.claude/scripts/`
3. Define the JSON output schema
4. Add a spawn instruction in the relevant skill's SKILL.md
5. Run `bash install.sh` to deploy
6. Update this README and `CHANGELOG.md`

### Agent Template

```markdown
---
name: df-{name}
description: Brief description
tools: Read, Write, Bash
---

# DataForge -- {Name} Agent

## Inputs
- param1: description

## Process
1. Run script: python3 ~/.claude/scripts/{script}.py ...
2. Verify output files
3. Return JSON result

## Output
{"agent": "df-{name}", "status": "success|failure", ...}
```
