---
name: dataforge-deploy
description: >
  Deployment skill for DataForge. Generates a complete, runnable Streamlit or
  FastAPI application for the best trained model. Includes app.py, requirements.txt,
  Dockerfile, and Makefile. Triggers on: "deploy", "deployment", "app", "serve",
  "streamlit", "fastapi", "api", "docker".
user-invokable: true
argument-hint: "<project-dir> [--production]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge — Deploy Skill

> Generate deployment applications (Streamlit/FastAPI/Flask) for trained models.

## Commands

| Command | What it does |
|---------|-------------|
| `/dataforge-deploy <project-dir>` | Generate Streamlit app (default) |
| `/dataforge-deploy <project-dir> --production` | Generate FastAPI app with Docker |

---

## Process

### Step 1 — Verify Prerequisites

Check that `{PROJECT_DIR}/src/models/leaderboard.json` exists.
If not: tell user to run `/dataforge-modeling train` first.

Read `{PROJECT_DIR}/dataforge.config.json` for project config.
Read `{PROJECT_DIR}/src/models/leaderboard.json` to find best model.

### Step 2 — Detect Deployment Target

```bash
~/.claude/dataforge/dfpython ~/.claude/scripts/deploy_detect.py \
  --problem-type "{PROBLEM_TYPE}" \
  --output "{PROJECT_DIR}/data/interim/deploy_config.json"
```

Add `--production` flag if user specified it.

Load `~/.claude/references/deploy-targets.md` for deployment reference.

### Step 3 — Generate App

Spawn agent: `df-deploy`

```
Task: Generate deployment app for {PROJECT_NAME}
deploy_config: {deploy_config.json contents}
output_dir: {PROJECT_DIR}
best_model: {best_model_name}
target_column: {TARGET_COL}
project_name: {PROJECT_NAME}
```

### Step 4 — Print Summary

```
Deployment generated for {PROJECT_NAME}

Target:    {streamlit|fastapi}
App:       {PROJECT_DIR}/app/app.py
Docker:    {PROJECT_DIR}/app/Dockerfile

Run:  cd {PROJECT_DIR} && make serve
```

---

## ERROR HANDLING

| Scenario | Action |
|----------|--------|
| No trained models | Tell user to run modeling first |
| Config missing | Tell user to run full pipeline |
| Deploy script error | Show stderr, diagnose |
