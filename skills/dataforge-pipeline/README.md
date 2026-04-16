# dataforge-pipeline (Workflow)

The main end-to-end workflow. Orchestrates all DataForge skills in sequence to go from a raw dataset to a complete ML project with trained models, interpretability, a deployment app, and a final report.

## Usage

```
/dataforge-pipeline <dataset> <target> [--production]
/dataforge run <dataset> <target> [--production]
```

## Pipeline steps

```
ingest -> validate -> profile -> EDA -> feature engineering -> train -> evaluate
-> interpret -> visualize -> deploy -> report
```

1. **Ingest** — Load dataset into `data/raw/`
2. **Validate** — Quality gates (hard stop on critical issues)
3. **Profile** — Auto-detect problem type, compute statistics
4. **EDA** — Parallel per-column + global analysis with plots
5. **Feature engineering** — Parallel per-column transforms, fitted sklearn Pipelines
6. **Train** — All model families trained in parallel
7. **Evaluate** — Rank models, generate leaderboard
8. **Interpret** — SHAP analysis for best model
9. **Visualize** — Confusion matrix, ROC, residual plots
10. **Deploy** — Streamlit app (or FastAPI with `--production`)
11. **Report** — HTML report with all artifacts embedded

## Flags

| Flag | Effect |
|------|--------|
| `--production` | Generates FastAPI app, forces full expert review |
| `--force` | Re-run even if outputs already exist |

## Resuming

If the pipeline is interrupted, resume from where it left off:

```
/dataforge resume <project-dir>
```
