# DataForge — Feature Engineering Recipes

Reference for the `df-feature-column` agent and the orchestrator.

## Decision Tree: Which Transform to Apply

```
Column type?
├── Numeric
│   ├── Has nulls?
│   │   ├── null_pct < 30% → median_imputation
│   │   └── null_pct ≥ 30% → consider_dropping (or ask user)
│   ├── Is skewed? (|skewness| > 1)
│   │   ├── min > 0 → log_transform
│   │   └── min ≤ 0 → yeo_johnson_transform
│   ├── Has outliers? (outlier_pct > 5%) → clip_outliers
│   └── Always → standard_scaling (for linear models)
│              → (skip scaling for tree-based models)
│
├── Categorical
│   ├── Has nulls? → mode_imputation
│   ├── n_unique ≤ 2 → label_encoding (binary)
│   ├── n_unique ≤ 10 → one_hot_encoding
│   ├── n_unique 11–50 → label_encoding
│   └── n_unique > 50 (high cardinality) → target_encoding
│
├── Datetime
│   ├── extract_year
│   ├── extract_month
│   ├── extract_dayofweek
│   └── (drop original datetime column after extraction)
│
└── Boolean → label_encoding (0/1)
```

## Scaling: When To Apply

| Model Family | Needs Scaling? |
|-------------|---------------|
| Linear / Logistic Regression | YES — use standard_scaling |
| SVM / KNN | YES — use standard_scaling |
| XGBoost / LightGBM / CatBoost | NO — tree-based, invariant to scale |
| RandomForest | NO |
| Neural Networks | YES — use standard_scaling or min_max |

DataForge applies scaling in the preprocessing pipeline for linear models only.
Tree-based models receive unscaled (but imputed + encoded) features.

## Encoding Reference

### One-Hot Encoding
- Use for: nominal categoricals with ≤ 10 unique values
- Creates N-1 binary columns (drop_first=True to avoid multicollinearity)
- Prefixes new columns with original column name: `color_red`, `color_blue`

### Label Encoding
- Use for: ordinal categoricals OR high-cardinality with tree models
- Assigns integer code to each category (alphabetical by default)
- CAUTION: introduces ordinal relationship — only safe for tree models

### Target Encoding
- Use for: high-cardinality categoricals (> 50 unique values)
- Replaces category with mean of target for that category
- Requires target column to be available
- CAUTION: can cause leakage if not done properly (use cross-fold target encoding in production)
- DataForge uses simple mean encoding for training — note in final report

## Imputation Reference

### Median Imputation (numeric)
- Best for: skewed distributions (median is robust to outliers)
- Avoid: when missingness is not random (MAR/MNAR) — discuss with user

### Mean Imputation (numeric)
- Best for: normally distributed features
- Avoid: with outliers (outliers skew the mean)

### Mode Imputation (categorical)
- Best for: low-cardinality categoricals
- Creates an implicit majority-class bias for rare categories

### Forward Fill (time series)
- Use when: time-ordered data, assume value persists until next observation

## Feature Creation Ideas (Advanced)

Suggest these to the user if patterns are detected:

| Pattern | Suggested Feature |
|---------|-----------------|
| date + numeric | `days_since_event` |
| two prices | `price_ratio`, `price_difference` |
| lat + long | `distance_from_centroid` |
| counts | `log(count + 1)` |
| categorical A × categorical B | `interaction_A_B` |
| age + income | `income_per_age` |
