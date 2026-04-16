---
name: df-feature-architect
description: Transform raw features into predictive power. Domain-specific feature engineering, intelligent encoding, statistical selection, and feature store design. Consolidated from 4 skills (feature-engineering, feature-importance-analysis, feature-store-design, ml-pipeline).
---

# Feature Architect

## Purpose

Transform 500 raw columns into 50 predictive features. Make principled decisions on encoding, scaling, interaction detection, and selection that improve both model accuracy and interpretability.

## When to Use This Skill

- **After data profiling** — Ready to engineer features
- **Domain-specific problems** — Need to add business logic features
- **High-dimensional data** — Need intelligent feature selection
- **Model improvement plateau** — Need feature interactions or domain knowledge
- **Production deployment** — Features must be reproducible and versioned

## Feature Engineering Workflow

### Phase 1: Domain Feature Engineering

**Add domain-specific features:**

```python
# Real estate example
features["age_at_listing"] = features["current_year"] - features["built_year"]
features["rooms_per_area"] = features["bedrooms"] / features["sqft"]
features["is_luxury"] = (features["price_per_sqft"] > 1000).astype(int)

# Financial example
features["debt_to_income"] = features["total_debt"] / features["annual_income"]
features["days_since_last_payment"] = (today - features["last_payment_date"]).days
features["payment_frequency"] = features["payment_count_90d"] / 90

# E-commerce example
features["customer_lifetime_value"] = features["total_spent"]
features["repeat_purchase_rate"] = features["repeat_purchases"] / features["total_purchases"]
features["average_order_value"] = features["total_spent"] / features["total_orders"]
```

**Key principle:** Use domain knowledge, not just statistical relationships.

### Phase 2: Encoding Categorical Features

**Decision tree for encoding:**

```
If cardinality < 5:
  → One-hot encode
  → Example: color (red, blue, green, yellow)

Elif cardinality 5-50:
  → Ordinal encode (if ordinal) OR target encode (if high-variance)
  → Example: education_level (HS, BS, MS, PhD)

Elif cardinality 50-1000:
  → Target encode (mean target value per category)
  → Example: zip_code (3000 unique)

Elif cardinality > 1000:
  → Target encode + regularization
  → OR embedding (learn dense vector)
  → Example: user_id (1M unique)
```

**Target Encoding:**
```python
# For regression
target_means = df.groupby("zip_code")["price"].mean()
df["zip_code_encoded"] = df["zip_code"].map(target_means)

# For classification
target_rates = df.groupby("region")["churn"].mean()
df["region_encoded"] = df["region"].map(target_rates)
```

**Why not just one-hot encode everything?** Creates explosive feature dimensions (1000 categories → 1000 columns).

### Phase 3: Scaling Numeric Features

**Decision based on model type:**

```
If using Ridge/Lasso/Neural Networks:
  → StandardScaler (mean 0, std 1)
  → Reason: Regularization penalizes large coefficients
  
If using tree-based (XGBoost, Random Forest):
  → No scaling needed (trees are scale-invariant)
  → Reason: Trees split on thresholds, not coefficients

If using distance-based (KNN, K-Means):
  → StandardScaler or MinMaxScaler
  → Reason: Distance metrics affected by scale
```

**Critical:** Fit scaler on TRAIN ONLY, apply to test.

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # Fit on train
X_test_scaled = scaler.transform(X_test)        # Apply to test (no fit!)
```

### Phase 4: Interaction Features

**Detect promising interactions:**

```python
# Start with base model
model_baseline = XGBClassifier()
model_baseline.fit(X_train, y_train)
baseline_accuracy = model_baseline.score(X_test, y_test)

# Test interactions one by one
interactions = [
  ("age", "income"),
  ("location", "property_type"),
  ("customer_age", "total_purchases")
]

for feat1, feat2 in interactions:
  X_with_interaction = X_train.copy()
  X_with_interaction[f"{feat1}_x_{feat2}"] = X_train[feat1] * X_train[feat2]
  
  model_with_interaction = XGBClassifier()
  model_with_interaction.fit(X_with_interaction, y_train)
  
  # Evaluate on test with same interaction
  X_test_interaction = X_test.copy()
  X_test_interaction[f"{feat1}_x_{feat2}"] = X_test[feat1] * X_test[feat2]
  new_accuracy = model_with_interaction.score(X_test_interaction, y_test)
  
  if new_accuracy > baseline_accuracy + 0.02:  # > 2% improvement
    print(f"Keep interaction: {feat1} × {feat2} (+{(new_accuracy - baseline_accuracy)*100:.1f}%)")
  else:
    print(f"Drop interaction: {feat1} × {feat2} (no improvement)")
```

**Rule:** Only add interactions if they improve accuracy by > 2%.

### Phase 5: Feature Selection

**Three approaches (choose based on data size & interpretability need):**

**Approach 1: Importance-Based (Fast, Interpretable)**
```python
# Train simple model
model = XGBClassifier()
model.fit(X_train, y_train)

# Get importances
importances = model.feature_importances_
selected = X_train.columns[importances >= 0.01]  # Keep > 1% importance

print(f"Removed {len(X_train.columns) - len(selected)} low-importance features")
```

**Approach 2: RFE - Recursive Feature Elimination (Balanced)**
```python
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier()
rfe = RFE(model, n_features_to_select=50)  # Keep top 50
X_train_selected = rfe.fit_transform(X_train, y_train)

selected_features = X_train.columns[rfe.support_]
print(f"Selected {len(selected_features)} features via RFE")
```

**Approach 3: SHAP-Based (Slow but Most Interpretable)**
```python
import shap

model = XGBClassifier()
model.fit(X_train, y_train)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_train)

# Mean absolute SHAP value per feature = importance
mean_shap = np.abs(shap_values).mean(axis=0)
selected = X_train.columns[mean_shap >= np.percentile(mean_shap, 90)]

print(f"Selected {len(selected)} features via SHAP")
```

---

## Feature Documentation

**Every feature needs:**

```yaml
feature_name: "zip_code_encoded"
data_type: "float32"
source_feature: "zip_code"
transformation: "target_encode"
rationale: "High cardinality (3000 unique); target encoding captures zip-code price premium"
importance: 0.18
data_availability: "at_training_and_inference_time"
freshness_requirement: "daily"
null_handling: "none (encoded from original)"
distribution:
  mean: 425000
  std: 125000
  min: 150000
  max: 2000000
```

**Why document?** So next analyst understands: what is this feature? Where does it come from? How is it computed?

---

## Feature Store Design

**Don't hardcode features in notebooks:**

```python
# BAD: Features computed in notebook, lost when notebook closes
def get_features():
    df["debt_to_income"] = df["debt"] / df["income"]
    return df

# GOOD: Features stored, versioned, reusable
def get_features(version="2026-04-17_v1"):
    # Load from feature store
    features = load_feature_store(version)
    return features

# Store versioned features
store_feature_store({
  "version": "2026-04-17_v1",
  "features": {
    "debt_to_income": df["debt_to_income"],
    "age_at_listing": df["age_at_listing"],
    ...
  },
  "metadata": {
    "computed_at": "2026-04-17T10:30:00Z",
    "rows": 1000,
    "columns": 50
  }
})
```

**Benefits:**
- Reproducibility (same features for training & inference)
- Versioning (can rollback to old features)
- Reusability (other models use same features)
- Governance (track which features used in which models)

---

## Expert Decision Examples

### Example 1: High-Cardinality Categorical

```
Feature: user_id (1M unique values out of 1M rows)
Problem: Can't one-hot encode (would create 1M columns)

Decision:
1. Target encode (map each user_id to their mean target value)
2. Regularize (add Laplace smoothing for rare users: (count * mean + prior) / (count + lambda))
3. Fallback (unknown users get global mean)

Result: 1M columns → 1 column, captures user-level signal
```

### Example 2: Imbalanced Data

```
Feature: missing_value_flag (99% 0, 1% 1)
Problem: Imbalanced, low information (most samples = 0)

Decision:
1. Check if importance > 1% (if not, remove)
2. If important, use with class weights (not over-sampling)
3. Monitor: ensure model doesn't overfit to rare cases

Result: Keep if signal strong; remove if noise
```

### Example 3: Temporal Features

```
Features: year, month, day (for time-series data)
Problem: Which features matter?

Decision:
1. Keep both year + day_of_year (captures season)
2. Drop month (redundant with day_of_year)
3. Add is_holiday flag (business logic)
4. Test: do these improve forecast accuracy?

Result: 3 temporal features → 3 columns, interpretable seasonality
```

---

## Memory Tracking

```json
{
  "run_id": "2026-04-17_feature_001",
  "domain": "real_estate",
  "raw_features": 200,
  "engineered_features": 20,
  "selected_features": 50,
  "encoding_decisions": {
    "zip_code": "target_encode (3000 categories)",
    "property_type": "one_hot (5 categories)",
    "age": "raw numeric (meaningful already)"
  },
  "feature_importance": {
    "price_per_sqft": 0.25,
    "rooms_per_area": 0.18,
    "age_at_listing": 0.12
  },
  "outcomes": {
    "baseline_accuracy": 0.82,
    "with_engineered_features": 0.85,
    "improvement": "+3.7%"
  },
  "next_time": "Target encoding works well for high-cardinality features; prioritize this"
}
```

---

## Anti-Patterns to Prevent

| Anti-Pattern | Problem | Solution |
|---|---|---|
| ❌ One-hot encode everything | Explosive dimensions | ✅ Target encode for cardinality > 50 |
| ❌ Use all features | Overfitting, noise | ✅ Select features with importance >= 0.01 |
| ❌ Scale after train/test split | Leakage | ✅ Fit scaler on train only |
| ❌ Keep feature in notebook only | Lost on reload | ✅ Store in feature store with version |
| ❌ No interaction testing | Miss nonlinear relationships | ✅ Test interactions; keep if > 2% gain |
| ❌ Hardcode feature logic | Breaks at inference | ✅ Reproducible pipeline (pickle scaler, encoder) |

---

## Implementation Checklist

- [ ] Brainstorm domain features (what makes sense in your domain?)
- [ ] Engineer domain features (add ratios, flags, aggregates)
- [ ] Encode categorical features (choose based on cardinality)
- [ ] Scale numeric features (based on model type)
- [ ] Test interactions (only if improves accuracy > 2%)
- [ ] Select features (importance >= 0.01 or RFE)
- [ ] Document every feature (what, why, source)
- [ ] Store in feature store (version, metadata)
- [ ] Test reproducibility (same features at training & inference)
- [ ] Track in memory (learn from feature engineering time investment)

