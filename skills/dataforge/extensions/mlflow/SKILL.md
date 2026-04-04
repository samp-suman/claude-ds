---
name: dataforge-mlflow
description: >
  DataForge extension for MLflow experiment tracking. Logs all model runs,
  parameters, metrics, and artifacts to an MLflow tracking server.
  Activate by setting MLFLOW_TRACKING_URI environment variable.
user-invokable: false
---

# DataForge MLflow Extension

Automatically logs all DataForge training runs to MLflow.

## Setup (one-time)

1. Install: `pip install mlflow`
2. Start tracking server: `mlflow server --host 0.0.0.0 --port 5000`
3. Set environment variable: `export MLFLOW_TRACKING_URI=http://localhost:5000`

## What Gets Logged

- All model hyperparameters
- CV metrics (mean ± std) for each model
- Test set metrics
- Model artifact (.pkl)
- Feature importance plot
- SHAP summary plot

## Usage

The extension is activated automatically when `MLFLOW_TRACKING_URI` is set.
The orchestrator calls `mlflow_log.py` after each training agent completes.

## View Results

```bash
mlflow ui --host 0.0.0.0 --port 5000
# Open http://localhost:5000
```
