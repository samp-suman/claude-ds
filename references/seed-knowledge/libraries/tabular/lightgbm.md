---
area: lightgbm
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area lightgbm
status: seed
schema_version: 1.0
applies_to_versions: ">=4.0,<5.0"
---

# LightGBM — API Knowledge

## Important APIs and defaults

### [lgbm-001] Categorical features by name
**Summary:** Pass `categorical_feature=[...]` (list of column names) when calling `.fit()`. LightGBM's native categorical handling outperforms one-hot for high-cardinality columns.
**Code:**
```python
model.fit(X_train, y_train, categorical_feature=["city", "device"])
```

### [lgbm-002] `n_jobs=-1` plus `verbosity=-1`
**Summary:** Default verbosity is noisy. Set `verbosity=-1` to silence info logs while keeping warnings.

### [lgbm-003] `objective="quantile"` for prediction intervals
**Summary:** Train multiple quantile models (e.g., 0.05, 0.5, 0.95) for distribution-free intervals. Cheaper than conformal prediction for many use cases.

### [lgbm-004] `class_weight="balanced"` or `is_unbalance=True`
**Summary:** Either works for imbalance. Equivalent to setting `scale_pos_weight` manually. Don't combine with explicit weights.

### [lgbm-005] Early stopping via callback (4.0+)
**Summary:** `early_stopping_rounds` is deprecated as a fit kwarg; use `callbacks=[lgb.early_stopping(50)]`.
**Code:**
```python
model.fit(X_train, y_train,
          eval_set=[(X_val, y_val)],
          callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])
```

### [lgbm-006] DART boosting for less overfitting
**Summary:** `boosting_type="dart"` drops trees during training. Slower but often gains 0.5-1% on noisy datasets. No early stopping support.

### [lgbm-007] `feature_pre_filter=False` for tuning
**Summary:** Default `True` removes constant-like features at dataset construction; this can interact badly with hyperparameter search. Disable when tuning.

## Tuning starting points

- `num_leaves=31`, `max_depth=-1`, `min_child_samples=20`
- `learning_rate=0.05`, `n_estimators=2000` with early stopping
- `feature_fraction=0.8`, `bagging_fraction=0.8`, `bagging_freq=5`
- `reg_alpha=0`, `reg_lambda=0`

## Pitfalls

- `num_leaves > 2^max_depth` overfits (when both are set).
- Categorical feature must be int-encoded OR pandas `category` dtype, not string in numpy array.
- Forgetting that `predict()` returns class probabilities for binary classification by default (unlike sklearn's `predict()` which returns labels).

## Key sources

- https://lightgbm.readthedocs.io/en/latest/Parameters.html
- https://github.com/microsoft/LightGBM/releases
