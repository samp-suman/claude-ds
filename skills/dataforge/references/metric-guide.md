# DataForge — Metric Selection Guide

Reference for the `df-evaluate` agent and reporting.

## Classification Metrics

### ROC-AUC (Primary for Binary Classification)
- **Range:** 0.5 (random) to 1.0 (perfect)
- **Use when:** Class imbalance is present; need to compare across thresholds
- **Avoid when:** Only care about a specific operating point (use F1 instead)
- **Interpretation:**
  - 0.50–0.60: Poor (barely better than random)
  - 0.60–0.70: Fair
  - 0.70–0.80: Good
  - 0.80–0.90: Very Good
  - 0.90–1.00: Excellent (check for leakage if > 0.99)

### F1 Score (Primary for Multiclass; Secondary for Binary)
- **Range:** 0.0 to 1.0
- **Use when:** Class imbalance; false positives and false negatives both matter
- **Variants:** `f1_binary`, `f1_weighted` (accounts for class sizes), `f1_macro` (equal weight per class)
- **DataForge default:** `f1_weighted` for multiclass, `f1_binary` for binary

### Accuracy
- **Use when:** Classes are balanced
- **Avoid when:** Class imbalance — a model that predicts majority class has high accuracy

### Precision vs Recall Trade-off
- **High Precision needed:** Spam detection (don't want false positives)
- **High Recall needed:** Cancer screening (don't want false negatives)
- **DataForge reports both** + F1 (harmonic mean)

## Regression Metrics

### R² (Primary)
- **Range:** ≤ 0.0 (worse than mean baseline) to 1.0 (perfect)
- **Interpretation:**
  - < 0.30: Poor model or highly noisy data
  - 0.30–0.60: Moderate (many real-world problems land here)
  - 0.60–0.80: Good
  - 0.80–0.95: Very Good
  - > 0.95: Excellent (check for leakage if near 1.0)
- **Limitation:** Can be misleading for non-linear models or heteroskedastic errors

### RMSE (Root Mean Squared Error)
- **Units:** Same as target variable (interpretable)
- **Use when:** Large errors should be penalized more
- **Avoid when:** Outliers in target inflate RMSE unfairly

### MAE (Mean Absolute Error)
- **Units:** Same as target variable
- **Use when:** Want robust metric not sensitive to outliers
- **Compare with RMSE:** If RMSE >> MAE, outliers are causing large errors

## Clustering Metrics

### Silhouette Score (Primary)
- **Range:** -1.0 to 1.0
- **Interpretation:**
  - > 0.5: Strong cluster structure
  - 0.25–0.5: Reasonable structure
  - < 0.25: Weak or no structure (may need different k or algorithm)

### Inertia (K-Means)
- Used for elbow method to select k — lower is better but not comparable across k
- Report as secondary metric alongside silhouette

## Cross-Validation Metrics

DataForge always reports CV metrics:
- `cv_{metric}_mean`: Average across 5 folds
- `cv_{metric}_std`: Standard deviation across 5 folds

**Rule of thumb:** If `std > 0.03`, the model is sensitive to data split. Consider:
- More training data
- Regularization
- Simpler model

## Metric Reporting in Reports

DataForge final report includes:
1. Primary metric value (CV mean ± std)
2. Test set primary metric value
3. Full metric table (all computed metrics)
4. Model comparison bar chart
5. For classification: confusion matrix, precision-recall curve
6. For regression: residual plot, prediction vs actual scatter
