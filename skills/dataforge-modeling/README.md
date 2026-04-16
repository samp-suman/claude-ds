# dataforge-modeling

Parallel model training, evaluation, ranking, SHAP interpretation, and visualization.

## Usage

```
/dataforge-modeling train <dataset> <target>        # Train all models in parallel, evaluate, rank
/dataforge-modeling evaluate <project-dir>          # Re-rank existing trained models
/dataforge-modeling interpret <project-dir>         # Generate SHAP plots for best model
/dataforge-modeling visualize <project-dir>         # Generate evaluation plots (confusion matrix, ROC, etc.)
```

Or via the router:

```
/dataforge train <dataset> <target>
```

## What it does

1. **Train** — Trains all applicable model families in parallel (one agent per model). Each model uses 5-fold cross-validation. Saves `.pkl` artifacts and metrics JSON.
2. **Evaluate** — Ranks all trained models by primary metric, generates a comparison bar chart, and writes `leaderboard.json`.
3. **Interpret** — Generates SHAP beeswarm plot, SHAP bar chart, and native feature importance for the best model.
4. **Visualize** — Confusion matrix, ROC curve (classification), residual plot + prediction-vs-actual (regression), and feature pairplot.

## Supported models

| Problem type | Models |
|-------------|--------|
| Binary classification | LightGBM, XGBoost, RandomForest, Logistic Regression, CatBoost |
| Multiclass | Same as binary (reports f1_weighted) |
| Regression | LightGBM, XGBoost, RandomForest, Ridge, Lasso |
| Clustering | KMeans, DBSCAN, Hierarchical |
