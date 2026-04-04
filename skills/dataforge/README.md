# DataForge Skill — Internals Reference

This directory contains the DataForge Claude Code skill. It is installed to
`~/.claude/skills/dataforge/` via `bash install.sh` from the repo root.

---

## Directory Structure

```
skills/dataforge/
├── SKILL.md          ← Orchestrator — the brain of DataForge
├── requirements.txt  ← Python dependencies
├── scripts/          ← Python execution layer (14 scripts)
├── references/       ← On-demand reference docs (loaded only when needed)
├── schema/           ← JSON Schema for memory + config files
├── hooks/            ← PostToolUse + PreToolUse hooks
└── extensions/       ← Optional integrations (Kaggle, MLflow)
```

---

## SKILL.md — The Orchestrator

`SKILL.md` is the most important file. It:
- Registers the `/dataforge` commands with Claude Code
- Defines the 12-step full pipeline execution order
- Contains parallel execution instructions (when to spawn N agents simultaneously)
- Defines quality gate behavior (what to do on HARD STOP vs WARNING)
- Specifies the memory contract (read at start, write at end)
- Lists all reference files and when to load each one

The orchestrator **never does computation itself** — it delegates to Python scripts
(via `Bash` tool) and sub-agents (via `Agent` tool).

### Command Registration

The `user-invokable: true` front-matter flag makes `/dataforge` available as a
slash command in Claude Code from any directory.

```yaml
---
name: dataforge
user-invokable: true
argument-hint: "[command] [dataset-path] [target-column]"
---
```

---

## Python Scripts Layer

Scripts handle all data computation. They are called via `Bash` tool by agents
and the orchestrator. Each script:
- Has a narrow CLI interface (args only, no interactive input)
- Prints a JSON result as the last line of stdout
- Uses exit codes: 0=success, 1=warning/partial, 2=fatal error

See `scripts/README.md` for full CLI reference for each script.

---

## Reference Docs Layer

Reference docs are loaded **on demand** by the orchestrator (not at startup).
This keeps token usage low — only load what's needed for the current stage.

| File | Loaded When |
|------|------------|
| `model-catalog.md` | After problem type detection |
| `feature-recipes.md` | During feature engineering |
| `metric-guide.md` | During evaluation |
| `deploy-targets.md` | During deployment |
| `leakage-patterns.md` | During validation |
| `quality-gates.md` | During validation |

See `references/README.md` for full index.

---

## Hooks

Hooks integrate with Claude Code's `settings.json` hook system.

| Hook | Type | Trigger | Action |
|------|------|---------|--------|
| `post-generate-lint.py` | PostToolUse | Write/Edit any .py file | pyflakes check |
| `pre-train-validate.sh` | PreToolUse | Any Bash call with train.py | Block if not validated |

Hooks are registered in `~/.claude/settings.json` by the install script.

---

## Extensions

Extensions are optional integrations loaded only when needed:

- **Kaggle** (`extensions/kaggle/`) — download datasets from Kaggle API
- **MLflow** (`extensions/mlflow/`) — log experiments to MLflow tracking server

Extensions follow the same pattern as the main skill: a `SKILL.md` + Python scripts.

---

## Modifying the Skill

**To change orchestration logic:** edit `SKILL.md`
**To add/change a Python computation:** edit the relevant script in `scripts/`
**To change quality gate thresholds:** edit `references/quality-gates.md` AND `scripts/validate.py`
**To add a model:** edit `references/model-catalog.md` AND `scripts/train.py`
**To add a reference doc:** create the file in `references/` + add a load instruction in `SKILL.md`

After any change:
1. Update `CHANGELOG.md`
2. Run `bash install.sh` from repo root
3. Commit and push
