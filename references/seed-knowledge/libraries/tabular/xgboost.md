---
area: xgboost
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area xgboost
status: seed
schema_version: 1.0
applies_to_versions: ">=2.0,<3.0"
---

# XGBoost — API Knowledge

## Important APIs and defaults

### [xgb-001] Native categorical support (`enable_categorical=True`)
**Summary:** Since 1.5/1.6, XGBoost handles pandas `category` dtype natively. Skip one-hot for high-cardinality features.
**Code:**
```python
XGBClassifier(enable_categorical=True, tree_method="hist")
```

### [xgb-002] `device="cuda"` replaces `gpu_hist`
**Summary:** Since 2.0, GPU is selected via `device="cuda"`, not `tree_method="gpu_hist"`. The old name still works but warns.

### [xgb-003] Early stopping is a constructor argument now
**Summary:** Pre-2.0 it was a fit() kwarg; now it's `XGBClassifier(early_stopping_rounds=50)`. Pass `eval_set` to `.fit()` for it to take effect.

### [xgb-004] `objective="reg:tweedie"` for sales/insurance/zero-inflated
**Summary:** Tweedie loss handles continuous targets with a point mass at zero. Set `tweedie_variance_power` between 1 and 2 (1.5 is a good start).

### [xgb-005] `monotone_constraints` for compliance and physics
**Summary:** Enforce that "more X -> more Y" (or the reverse). Crucial in credit, healthcare, pricing where monotonicity is required.
**Code:**
```python
XGBClassifier(monotone_constraints={"income": 1, "debt": -1})
```

### [xgb-006] `interaction_constraints` for trust
**Summary:** Limit which features can interact in a tree. Useful for partial-dependence interpretability.

### [xgb-007] `scale_pos_weight` for imbalance
**Summary:** Set to `n_neg / n_pos`. Cheaper than SMOTE and doesn't distort the data distribution.

## Tuning starting points

- `n_estimators=2000`, `learning_rate=0.05`, `early_stopping_rounds=50`
- `max_depth=6`, `min_child_weight=1`
- `subsample=0.8`, `colsample_bytree=0.8`
- `reg_alpha=0`, `reg_lambda=1`
- For imbalance: `scale_pos_weight=n_neg/n_pos`

## Pitfalls

- Forgetting `eval_set` so early stopping silently no-ops.
- Predicting probabilities with `predict()` instead of `predict_proba()`.
- Treating `feature_importances_` (gain-based by default) as causal - it isn't.
- Mixing scikit-learn API (`XGBClassifier`) with native API (`xgb.train`) and confusing param names.

## Key sources

- https://xgboost.readthedocs.io/en/stable/changes.html
- https://xgboost.readthedocs.io/en/stable/parameter.html
