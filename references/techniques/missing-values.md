# Missing Value Handling Techniques

Comprehensive guide to handling missing data across different problem contexts.

---

## 1. Mean/Median/Mode Imputation

**When to use**:
- MCAR (Missing Completely At Random) data
- < 30% missing in numeric columns
- No complex relationships between features
- Quick baseline approach

**Pros**:
- Fast, no hyperparameter tuning
- Works with any algorithm
- Preserves dataset size

**Cons**:
- Ignores feature relationships
- Reduces variance artificially
- Can create distributional artifacts at the imputation value

**Code pattern**:
```python
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='median')  # or 'mean', 'most_frequent'
X_imputed = imputer.fit_transform(X_train)
```

**Failure cases**:
- Skewed data where mean is pulled by outliers → use median
- Categorical data → use mode
- MAR/MNAR data → biased estimates

---

## 2. Forward/Backward Fill

**When to use**:
- Time series data exclusively
- Missingness is ordered/temporal
- Values change slowly over time (e.g., sensor readings, stock prices)

**Pros**:
- Preserves temporal structure
- Simple, no parameters
- Good for slow-changing signals

**Cons**:
- Only valid for time series
- Can propagate stale values far into future
- Biased if missingness has pattern

**Code pattern**:
```python
df['col'].fillna(method='ffill')  # Forward fill
df['col'].fillna(method='bfill')  # Backward fill
df['col'].fillna(method='ffill', limit=3)  # Limit propagation
```

**When it fails**:
- Non-time-series data (spatially distributed, cross-sectional) → use another method
- Gaps > 10% of data length → last value becomes stale
- Abrupt changes in process → propagates wrong value

---

## 3. KNN Imputation

**When to use**:
- < 40% missing (computational cost increases with missingness)
- Complex feature relationships exist
- Data has meaningful distance metric (continuous or mixed types)
- Time series with gaps (structurally missing, not MCAR)

**Pros**:
- Respects local feature structure
- Handles multivariate missing patterns
- Can work with mixed numeric/categorical

**Cons**:
- Computationally expensive (O(n²) per imputation)
- Hyperparameter choice (k) affects results
- Can amplify noise in sparse regions

**Code pattern**:
```python
from sklearn.impute import KNNImputer
imputer = KNNImputer(n_neighbors=5)
X_imputed = imputer.fit_transform(X_train)
```

**Failure cases**:
- High-dimensional data (curse of dimensionality) → PCA first
- Very large missing blocks → data is too sparse to borrow information
- Outliers in neighboring features → use robust distance metric

---

## 4. MICE / IterativeImputer

**When to use**:
- 20-50% missing data
- Complex multivariate missing patterns (MAR/MNAR suspected)
- Multiple columns with missingness
- Need probabilistic imputation

**Pros**:
- Handles multivariate patterns
- Preserves relationships between features
- Generates multiple imputations for uncertainty quantification

**Cons**:
- Slower than simpler methods
- Assumes missing data are missing at random (MAR)
- Requires careful tuning of imputation models

**Code pattern**:
```python
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
imputer = IterativeImputer(max_iter=10, random_state=42)
X_imputed = imputer.fit_transform(X_train)
```

**How it works**:
1. Start with mean/median imputation
2. Fit predictive model to each column using other columns
3. Predict missing values
4. Repeat until convergence

**When it fails**:
- MCAR data → simpler methods more efficient
- Circular dependencies between features → convergence issues
- Very large datasets → slow

---

## 5. MissForest (Random Forest Imputation)

**When to use**:
- Mixed numeric/categorical data (native support)
- Non-linear feature relationships
- > 40% missing is still manageable
- Need robust approach without distributional assumptions

**Pros**:
- Handles mixed data types naturally
- Captures non-linear relationships
- Robust to outliers (tree-based)
- R/Python implementations available

**Cons**:
- Moderate computational cost
- Fewer hyperparameters to tune (but may need adjustment)
- Not as interpretable as linear imputation

**Code pattern**:
```python
# R: missForest::missForest(X)
# Python: similar via sklearn Random Forest in an iterative loop
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

def missforest_step(X, cat_cols, num_cols):
    for col in X.columns:
        X_train = X.drop(col, axis=1)
        y_train = X[col]
        if col in cat_cols:
            model = RandomForestClassifier()
        else:
            model = RandomForestRegressor()
        mask = X[col].isna()
        if mask.sum() > 0:
            model.fit(X_train[~mask], y_train[~mask])
            X.loc[mask, col] = model.predict(X_train[mask])
    return X
```

---

## 6. Indicator (Missingness Flag) Feature

**When to use**:
- Missingness itself is informative
- Absence of a value predicts target
- Data is structurally missing (e.g., item not purchased → price is NA)
- Combined with other imputation methods

**Pros**:
- Preserves information about missingness
- Lets model learn from absence pattern
- Works with any imputation strategy

**Cons**:
- Adds feature dimensionality
- Only useful if missingness is predictive
- Can cause overfitting if taken too far

**Code pattern**:
```python
df['col_is_missing'] = df['col'].isna().astype(int)
df['col'] = df['col'].fillna(df['col'].median())  # Then impute
```

**When to use this pattern**:
- Real estate: no price listed → is listing active? → correlated with target
- E-commerce: no review date → product discontinued? → affects purchase likelihood
- Healthcare: missing lab value → test not ordered → patient health status signal

---

## 7. Soft Impute (SVD-Based Matrix Completion)

**When to use**:
- Sparse matrices (e.g., rating matrices, document-term matrices)
- > 60% missing but data is low-rank
- Recommendation systems, NLP embeddings
- Need efficient computational approach

**Pros**:
- Efficient for very sparse matrices
- Leverages low-rank structure
- Scales to massive matrices (millions of rows/cols)

**Cons**:
- Assumes data is low-rank (not all datasets are)
- Requires tuning rank parameter
- Less intuitive than other methods

**Code pattern**:
```python
from sklearn.decomposition import TruncatedSVD

def soft_impute(X, max_iter=10, rank=10, threshold=1e-3):
    X_filled = X.fillna(X.mean())
    for _ in range(max_iter):
        U, s, Vt = TruncatedSVD(n_components=rank).fit(X_filled).fit_transform()
        X_reconstructed = U @ np.diag(s) @ Vt
        X_filled[X.isna()] = X_reconstructed[X.isna()]
    return X_filled
```

**Application examples**:
- Netflix prize challenge (movie ratings matrix)
- TF-IDF document matrices with sparse terms
- Sensor networks with gaps in readings

---

## Decision Tree for Missing Value Strategy

```
Start: Analyze missingness pattern

├─ Random (MCAR)?
│  └─ < 30%? → Mean/Median Imputation
│  └─ > 30%? → KNN or MICE
│
├─ Time Series?
│  └─ < 10% gaps? → Forward/Backward Fill
│  └─ > 10% gaps? → KNN (structured) or Indicator + Simple Impute
│
├─ Sparse Matrix (<<50% data)?
│  └─ → Soft Impute (SVD)
│
├─ Mixed Numeric/Categorical?
│  └─ → MissForest or MICE
│
├─ Missingness Informative?
│  └─ → Indicator Feature + choice above
│
└─ MAR/MNAR Suspected?
   └─ → MICE (multiple imputations) or sensitivity analysis
```

---

## Common Pitfalls

1. **Using mean on skewed data** → outliers pull mean; use median
2. **Not checking MCAR assumption** → biased estimates if MAR/MNAR
3. **Imputing before splitting train/test** → data leakage
4. **Using imputation statistics from full dataset** → leaks test information
5. **Forgetting about indicator columns** → lose missingness signal
6. **KNN with high-dimensional data** → curse of dimensionality; use PCA first

---

## References

- Rubin, D. B. (1976). "Inference and missing data"
- Little & Rubin (2002). "Statistical Analysis with Missing Data"
- Stekhoven & Bühlmann (2012). "MissForest — non-parametric missing value imputation"
