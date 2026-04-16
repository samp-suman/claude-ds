# dataforge-experiment

Experiment tracking, comparison, drift monitoring, and memory management for DataForge projects.

## Usage

```
/dataforge-experiment status <project-dir>                      # View experiment history + decisions
/dataforge-experiment compare <project-dir>                     # Compare experiments across runs
/dataforge-experiment monitor <project-dir> --new-data <path>   # Detect data/concept drift
/dataforge-experiment history <project-dir>                     # Full run history
```

Or via the router:

```
/dataforge status <project-dir>
/dataforge monitor <project-dir> --new-data <path>
```

## What it does

- **Status** — Prints a summary of all experiments: configs, metrics, best pipeline, and key decisions made during the run.
- **Compare** — Side-by-side comparison of multiple experiment runs with metric deltas.
- **Monitor** — Detects data drift (feature distribution shifts) and concept drift (model performance degradation) between training data and new incoming data. Recommends retraining when thresholds are exceeded.
- **History** — Full chronological log of all runs with timestamps, parameters, and outcomes.

## Memory files

Each project stores experiment memory in its `memory/` directory:

| File | Contents |
|------|----------|
| `experiments.json` | Run history (configs, metrics, artifact paths) |
| `decisions.md` | Why each choice was made |
| `failed_transforms.json` | What didn't work (skipped on resume) |
| `best_pipelines.json` | Winning configs (seeds future runs) |
