---
area: finance
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area finance
status: seed
schema_version: 1.0
---

# Finance — Domain Knowledge

## Core techniques

### [fin-001] Time-based splits, never random
**Summary:** Financial data is non-stationary. Random train/test split leaks future into past. Use walk-forward / expanding-window splits with a purge gap.
**Pitfall:** Sklearn `train_test_split(shuffle=True)` is the most common bug in finance ML.

### [fin-002] Class imbalance in fraud / default
**Summary:** Fraud rates are 0.1-2%; defaults 1-10%. Use `scale_pos_weight` (XGB/LGBM) or `class_weight="balanced"` (sklearn). Don't oversample BEFORE the split. Calibrate probabilities (`CalibratedClassifierCV`) for cost-sensitive thresholding.
**When to use:** Any binary classification with <20% positives.

### [fin-003] Threshold by expected cost, not 0.5
**Summary:** Pick the decision threshold to minimize `cost_FN * P(fn) + cost_FP * P(fp)`, not by maximizing F1. A missed fraud may cost 100x a false alarm.
**When to use:** Always for fraud, AML, credit, churn.

### [fin-004] Feature engineering for credit risk
**Summary:** Debt-to-income ratio, credit utilization, delinquency counts in last N months, account age, recent inquiries. WOE/IV transforms remain industry-standard for interpretability and regulatory submissions.

### [fin-005] Survival framing for default
**Summary:** Default isn't a one-shot event - it has a time-to-event structure. `lifelines` Cox PH or `scikit-survival` random-survival-forests outperform classification when censoring matters.

## Pitfalls

- Look-ahead bias from features computed using future data (e.g., 30-day rolling mean centered on today).
- Survivor bias when training only on accounts still open.
- Macro regime change: a model trained pre-2020 won't generalize through COVID. Always check temporal drift.
- PII: SSN, account number, full name must be hashed or dropped before any logging.

## Recommended metrics

- **Fraud / default**: PR-AUC (not ROC-AUC; class imbalance distorts ROC), KS statistic, expected cost at optimal threshold.
- **Credit scoring**: Gini = 2*AUC - 1, KS, PSI for monitoring drift.
- **Pricing / forecasting**: MASE, sMAPE, pinball loss for quantile forecasts.

## Key sources to refresh from

- Marcos Lopez de Prado - "Advances in Financial Machine Learning" (purged k-fold, meta-labeling)
- Numerai forum and tournament writeups
- Kaggle Home Credit / Santander / IEEE-CIS fraud winning solutions
- Basel III / IFRS 9 documentation for regulatory constraints
