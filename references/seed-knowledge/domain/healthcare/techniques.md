---
area: healthcare
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area healthcare
status: seed
schema_version: 1.0
---

# Healthcare — Domain Knowledge

## Core techniques

### [hc-001] Patient-level grouping in CV
**Summary:** Multiple visits per patient -> use `GroupKFold` on patient_id. Random splits leak the same patient across train and test.
**Pitfall:** AUC mysteriously high until deployment - then fails on new patients.

### [hc-002] Time-of-prediction discipline
**Summary:** For sepsis / readmission / deterioration models, only use features available at prediction time. Lab results posted hours later cannot be inputs to a 2am alert.
**When to use:** Any clinical decision-support model.

### [hc-003] Class imbalance + cost asymmetry
**Summary:** Mortality, sepsis, readmission are 2-15% positives. False negatives are clinically dangerous. Optimize PR-AUC and recall at fixed precision (e.g., recall@PPV=0.3).

### [hc-004] ICD/CPT code embeddings
**Summary:** ICD-10 codes are hierarchical (3, 4, 5 char prefixes group families). Use truncated prefixes as features, or pretrained Med2Vec / ClinicalBERT embeddings for richer representations.

### [hc-005] Missing-not-at-random
**Summary:** A missing lab value often means "doctor didn't think it was needed" - the missingness IS information. Add `lab_X_was_measured` indicator columns rather than imputing silently.

## Pitfalls

- HIPAA / PHI: hash/strip patient_id, dates of birth (keep age-at-event), zip codes (truncate to 3 digits).
- Calibration matters more than discrimination: clinicians need probability estimates they can trust. Always check `CalibrationDisplay` and use `CalibratedClassifierCV` if needed.
- Subgroup fairness: check performance by age, sex, race, insurance type. Disparate impact is both ethical and regulatory risk.
- Site effects: a model trained at one hospital may use site-specific equipment IDs as proxies. Always cross-site validate.

## Recommended metrics

- PR-AUC, recall@fixed-precision, calibration slope and intercept, Brier score.
- For survival: concordance index (c-index), integrated Brier score.
- For subgroups: equal opportunity difference, demographic parity gap.

## Key sources

- MIMIC-III/IV benchmarks and reference implementations
- "Machine Learning for Healthcare" book (Pearl, Wang, Doshi-Velez)
- FDA SaMD (Software as Medical Device) guidance
- "Clinical Prediction Models" by Steyerberg
