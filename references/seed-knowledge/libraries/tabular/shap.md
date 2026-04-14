---
area: shap
category: library
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area shap
status: seed
schema_version: 1.0
applies_to_versions: ">=0.45,<1.0"
---

# SHAP — Interpretability

## Core APIs

### [shap-001] `TreeExplainer` for tree models
**Summary:** Exact, fast SHAP for XGBoost / LightGBM / CatBoost / sklearn forests. Always use this when applicable.
**Code:**
```python
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)  # or .shap_interaction_values(X_sample)
```

### [shap-002] `Explainer` (auto-routing) for everything else
**Summary:** `shap.Explainer(model, X_background)` picks Tree/Linear/Permutation/Kernel automatically. Pass a small background sample (~100 rows) for non-tree models.

### [shap-003] Beeswarm summary plot
**Summary:** `shap.plots.beeswarm(shap_values)` is the gold-standard global view. Order is by mean(|SHAP|).

### [shap-004] `shap.plots.bar` for the executive view
**Summary:** Mean absolute SHAP per feature. Cleaner than beeswarm for stakeholder slides.

### [shap-005] Force plot only for single instances
**Summary:** Use sparingly - useful for case studies, not aggregate analysis.

### [shap-006] Sample for speed
**Summary:** SHAP is O(n) per row. For >10k rows take a stratified sample of ~1000 for plotting. Use `shap.sample(X, 1000)` or `shap.utils.sample`.

## Pitfalls

- Computing SHAP on test set with a TreeExplainer trained on train data is correct - DON'T retrain.
- Treating SHAP values as causal effects - they explain the model, not the world.
- Mixing classifier outputs (log-odds vs probability vs class index) - use `model_output="probability"` for direct interpretation.
- Plotting SHAP with column-order mismatched to training - always use the same DataFrame schema.
- For multiclass, `shap_values` is a list per class - pick one or sum |SHAP| across classes.

## When SHAP isn't enough

- Permutation importance (`sklearn.inspection.permutation_importance`) for model-agnostic.
- Partial dependence + ICE plots for one-feature effects.
- Counterfactual explanations (DiCE) for "what would change the prediction".

## Key sources

- https://shap.readthedocs.io/
- "Interpretable Machine Learning" (Christoph Molnar)
