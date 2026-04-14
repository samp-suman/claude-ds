---
area: data-scientist
category: role
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area data-scientist
status: seed
schema_version: 1.0
---

# Data Scientist — Methodology Knowledge

## Core principles

### [ds-001] Hold out a test set BEFORE looking at data
**Summary:** Stratified split immediately after ingest, save row hashes, never touch until final eval. EDA on the train partition only. Otherwise EDA decisions leak.
**Pitfall:** This is the single most common "model worked in dev, failed in prod" cause.

### [ds-002] Fit transformers on train only
**Summary:** Imputers, scalers, encoders, target-encoders all leak when fit on train+test. Use `sklearn.Pipeline` so `.fit()` only sees train and `.transform()` is the only thing the test/prod data ever calls.
**When to use:** Always. CSV-to-CSV preprocessing is the anti-pattern.

### [ds-003] Pick the metric BEFORE training
**Summary:** Don't optimize accuracy, then report F1, then quote AUC. The metric drives decisions: imbalance -> PR-AUC, cost-asymmetric -> expected cost, regression with skewed target -> MAE in original units, ordinal -> quadratic kappa.

### [ds-004] CV scheme matches deployment shape
**Summary:** Time series -> walk-forward. Grouped IDs (patient/customer/store) -> GroupKFold. Imbalanced -> StratifiedKFold. Random k-fold is rarely the right default.

### [ds-005] Baseline before ML
**Summary:** Always train a constant predictor, a linear model, and a single decision tree first. If your fancy model can't beat them by a wide margin, you have a bug.

### [ds-006] One change at a time
**Summary:** Change feature engineering OR model OR hyperparameters per experiment, never all at once. Otherwise you can't attribute the gain.

### [ds-007] Calibrate when probabilities are used downstream
**Summary:** Tree ensembles produce uncalibrated scores. If a downstream system thresholds them, wrap with `CalibratedClassifierCV` (sigmoid for small data, isotonic for >1k positives).

## Pitfalls

- Optimizing on validation set repeatedly creates implicit overfitting. Hold out a final test set you only touch ONCE.
- Removing outliers before splitting leaks information about the test distribution.
- One-hot-encoding high-cardinality columns explodes dimensionality - use target encoding or hashing.
- Reporting CV mean without std hides instability.
- Forgetting to seed all RNGs (numpy, sklearn, lightgbm, torch) makes runs non-reproducible.

## Recommended workflow

1. Ingest -> raw validate -> stratified test holdout (sentinel `.test_split_saved`)
2. EDA on train only (per-column + global)
3. Feature engineering as Pipeline steps
4. Fit pipeline on train, transform train+test via `.transform()`
5. Post-FE leakage gate (corr > 0.95 -> HARD STOP)
6. CV on train, retrain on full train, evaluate ONCE on test
7. Calibrate, interpret (SHAP), deploy

## Key sources

- Sebastian Raschka "Machine Learning Q and AI", "Python Machine Learning"
- Andrew Ng "Machine Learning Yearning"
- Kaggle Grandmaster interview series
- Chip Huyen "Designing Machine Learning Systems"
- Karpathy "A Recipe for Training Neural Networks" (transferable principles)
