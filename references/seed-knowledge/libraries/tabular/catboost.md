---
area: catboost
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area catboost
status: seed
schema_version: 1.0
applies_to_versions: ">=1.2,<2.0"
---

# CatBoost — API Knowledge

## Why pick CatBoost

### [cb-001] Best out-of-the-box for categorical-heavy data
**Summary:** Ordered target statistics + CTR features handle high-cardinality categoricals without manual encoding. Often the best single model for retail / marketing / ad-tech with no tuning.

### [cb-002] Pass categorical features as a list
**Summary:**
```python
CatBoostClassifier(cat_features=["city", "channel"])
```
Strings work directly - no need to encode first.

### [cb-003] `text_features` for short text columns
**Summary:** Built-in BoW + bigram + naive-Bayes featurization for text columns. Saves a separate text pipeline for product titles, search queries.

### [cb-004] Default symmetric oblivious trees
**Summary:** All splits at the same depth use the same feature. Faster inference, slightly weaker fit. Set `grow_policy="Lossguide"` for LightGBM-style growth when accuracy matters.

### [cb-005] `loss_function="Quantile:alpha=0.9"`
**Summary:** Quantile regression for prediction intervals.

### [cb-006] Built-in overfitting detector
**Summary:** `od_type="Iter"` + `od_wait=50` is roughly equivalent to early stopping. Default uses validation pool.

## Tuning starting points

- `iterations=2000`, `learning_rate=0.03`, `od_wait=50`
- `depth=6`, `l2_leaf_reg=3`
- `random_strength=1`, `bagging_temperature=1`

## Pitfalls

- Verbose by default; set `verbose=100` or `silent=True`.
- GPU training requires NVIDIA + CUDA; no AMD support.
- Model size on disk is larger than XGBoost/LightGBM for the same ensemble.
- `cat_features` indices must be ints if you pass a numpy array; column names if pandas.

## Key sources

- https://catboost.ai/docs/
- https://github.com/catboost/catboost/releases
