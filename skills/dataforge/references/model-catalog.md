# DataForge — Model Catalog

Reference for the orchestrator's model selection logic (Step 7).

## Binary Classification

| Model | Use When | Avoid When | Default Hyperparams |
|-------|----------|-----------|---------------------|
| **LightGBM** | > 1k rows, mixed features, speed priority, Kaggle-style | < 100 rows | n_estimators=300, lr=0.05, num_leaves=31 |
| **XGBoost** | Tabular data, robust baseline, well-tuned | Very high-dim sparse data | n_estimators=300, lr=0.05, max_depth=6 |
| **RandomForest** | Interpretability + robustness, noisy data | > 500k rows (memory) | n_estimators=200, max_depth=None |
| **Logistic Regression** | Linear boundary, fast inference, baseline | Non-linear patterns dominate | C=1.0, max_iter=1000 |
| **CatBoost** | > 3 high-cardinality categorical features | Pure numeric datasets | iterations=300, lr=0.05, depth=6 |
| **SVM RBF** | Small datasets with complex boundary (< 10k) | Large datasets — O(n²) | C=1.0 |

**Always train by default:** LightGBM, XGBoost, RandomForest, LogisticRegression
**Add CatBoost if:** categorical_columns > 3

## Multiclass Classification

Same as binary classification but:
- Logistic uses `multi_class='ovr'` automatically
- Report `f1_weighted` as primary metric (instead of roc_auc)
- XGBoost uses `objective='multi:softprob'` automatically

## Regression

| Model | Use When | Avoid When | Default Hyperparams |
|-------|----------|-----------|---------------------|
| **LightGBM** | > 1k rows, mixed features | Very small data | n_estimators=300, lr=0.05 |
| **XGBoost** | Strong baseline for tabular regression | Sparse data | n_estimators=300, lr=0.05 |
| **RandomForest** | Non-linear patterns, robust to outliers | Very large datasets | n_estimators=200 |
| **Linear Regression** | Linear relationship, interpretability | Non-linear data | — |
| **Ridge** | Linear with many features (collinearity) | Truly sparse features | alpha=1.0 |
| **Lasso** | Feature selection + regression | Non-linear data | alpha=0.01 |

**Always train by default:** LightGBM, XGBoost, RandomForest, Ridge, Linear

**Primary metric:** R² (higher is better). Also report RMSE and MAE.

## Clustering (No Target)

| Model | Use When | Parameters to Tune |
|-------|----------|------------------|
| **K-Means** | Spherical clusters, known k | n_clusters (auto via elbow) |
| **DBSCAN** | Arbitrary shapes, noise detection | eps, min_samples |
| **Hierarchical** | Unknown k, want dendrogram | n_clusters, linkage |

**Default:** Run K-Means (elbow method), DBSCAN, Hierarchical. Compare silhouette scores.

## Time Series

For time_series problem type, use:
1. **Linear baseline** (trend + seasonality decomposition)
2. **LightGBM** with lag features
3. **Prophet** (if fbprophet installed — check first)

Always use time-based train/test split (never random split for time series).

## Hyperparameter Starting Points (Best Practice)

### Tree Models (LightGBM / XGBoost)
- **n_estimators**: Start at 300, increase to 500 if overfitting is not seen
- **learning_rate**: 0.05 (lower = better generalization but slower)
- **max_depth**: 6 for XGBoost; -1 (unlimited) for LightGBM
- **num_leaves** (LightGBM): 31 (default); increase for complex data
- **subsample**: 0.8 (reduces overfitting)
- **colsample_bytree**: 0.8 (feature subsampling)

### RandomForest
- **n_estimators**: 200 (more = better but diminishing returns after 200)
- **max_depth**: None (full depth) — control via min_samples_split instead
- **class_weight**: "balanced" (always for classification)

### Logistic/Linear Regression
- **C** (Logistic): 1.0 — try [0.01, 0.1, 1.0, 10.0] if tuning
- **alpha** (Ridge/Lasso): 1.0 — try [0.001, 0.01, 0.1, 1.0, 10.0]

## Model Selection Intelligence

### Dataset Size Rules
| Rows | Recommended Models |
|------|------------------|
| < 100 | LogisticRegression / Linear only (avoid complex models) |
| 100–1k | All models; expect high variance |
| 1k–100k | All models; standard configuration |
| > 100k | LightGBM, XGBoost (fast); skip SVM |
| > 1M | LightGBM only (memory); consider chunking |

### Feature Type Rules
| Dominant Feature Type | Recommended First |
|----------------------|-----------------|
| All numeric | XGBoost or LightGBM |
| Many categoricals (> 30%) | CatBoost first |
| Mixed | LightGBM |
| Very high-dimensional (> 500 features) | Lasso (regression) / LogisticRegression with L1 |
| Time-indexed | LightGBM with lag features |
