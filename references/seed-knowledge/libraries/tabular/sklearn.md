---
area: sklearn
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area sklearn
status: seed
schema_version: 1.0
applies_to_versions: ">=1.4,<2.0"
---

# scikit-learn — API Knowledge

## Recent / important APIs

### [sk-001] `set_output(transform="pandas")` for column-name preservation
**Summary:** Since 1.2, transformers can return DataFrames not arrays. Call `pipeline.set_output(transform="pandas")`. Critical for SHAP and debugging.
**Code:**
```python
pipeline.set_output(transform="pandas")
```

### [sk-002] `HistGradientBoostingClassifier/Regressor` natively handles NaN
**Summary:** Don't impute before HistGB - it has built-in missing-value support and is often as fast as LightGBM. Also supports `categorical_features` directly without one-hot.

### [sk-003] `ColumnTransformer` is the canonical preprocessor
**Summary:** Build per-column-group transformers, compose into a Pipeline. Use `make_column_selector(dtype_include="number")` for typed routing.
**Pitfall:** `remainder="drop"` is the default - silently drops columns you didn't list.

### [sk-004] `Pipeline` for leakage-free CV
**Summary:** `cross_val_score(pipeline, X, y, cv=5)` fits the entire pipeline on each fold's train. Manual CV with imputers fit on full X is the canonical leakage bug.

### [sk-005] `TargetEncoder` (1.3+)
**Summary:** Built-in target encoder with CV smoothing. No more category_encoders dependency for basic use.
**Pitfall:** Still needs `cv` parameter on its own to avoid leakage when used outside a Pipeline.

### [sk-006] `CalibratedClassifierCV`
**Summary:** Wraps any classifier to produce calibrated probabilities. Use `method='isotonic'` for >1k positives, `'sigmoid'` for less.

### [sk-007] Metaestimators that respect Pipeline
**Summary:** `GridSearchCV`, `RandomizedSearchCV`, `HalvingGridSearchCV` all clone the pipeline per fit - safe. Use them around the pipeline, not inside.

## Deprecations to watch

- `sklearn.externals.joblib` removed long ago - use top-level `joblib`.
- `n_jobs` semantics: `-1` uses all cores; in containers prefer explicit numbers.
- `OneHotEncoder(sparse=...)` -> `sparse_output=...` since 1.2.

## Pitfalls

- Forgetting to call `.set_output(transform="pandas")` and losing column names downstream.
- Using `np.random.seed()` instead of passing `random_state=` to estimators.
- Fitting on a numpy array then predicting on a DataFrame (column order may differ).
- `LabelEncoder` is for targets, NOT features. Use `OrdinalEncoder` for features.

## Key sources

- https://scikit-learn.org/stable/whats_new.html
- https://scikit-learn.org/stable/modules/compose.html
