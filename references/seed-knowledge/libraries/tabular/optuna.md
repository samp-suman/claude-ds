---
area: optuna
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area optuna
status: seed
schema_version: 1.0
applies_to_versions: ">=3.5,<5.0"
---

# Optuna — Hyperparameter Optimization

## Idioms

### [opt-001] Study + objective pattern
**Summary:**
```python
def objective(trial):
    params = {
        "learning_rate": trial.suggest_float("lr", 1e-3, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "num_leaves": trial.suggest_int("num_leaves", 15, 255),
    }
    model = LGBMClassifier(**params)
    score = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc").mean()
    return score

study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=100, timeout=3600)
```

### [opt-002] TPE > random > grid for >5 params
**Summary:** `TPESampler` is the default for good reason. `CmaEsSampler` for continuous-only. `GridSampler` only for tiny spaces.

### [opt-003] Pruners save compute
**Summary:** `MedianPruner` or `HyperbandPruner` cuts off trials that are obviously losing. Need to call `trial.report(intermediate_value, step)` and `trial.should_prune()`.

### [opt-004] Multi-objective optimization
**Summary:** Return a tuple (e.g., (accuracy, latency)) and `create_study(directions=["maximize", "minimize"])`. Pareto front via `study.best_trials`.

### [opt-005] Study persistence with SQLite
**Summary:** `storage="sqlite:///optuna.db"` lets you resume studies and view in `optuna-dashboard`.

### [opt-006] Distributed optimization
**Summary:** Multiple processes with `load_if_exists=True` and shared storage backend cooperate on the same study automatically.

## Tuning best practices

- Always use `log=True` for learning rate and regularization params.
- Use `suggest_float(..., step=...)` to discretize where you don't need fine resolution.
- Cap `n_trials` AND `timeout` - whichever hits first.
- Run a dummy `objective` once with cheap settings to check the wiring before a long run.

## Pitfalls

- Optimizing on the test set leaks. CV inside the objective only.
- TPE assumes smooth landscapes; for very noisy objectives, increase `n_startup_trials`.
- Forgetting to seed the sampler -> non-reproducible runs.

## Key sources

- https://optuna.readthedocs.io/
- https://github.com/optuna/optuna/releases
