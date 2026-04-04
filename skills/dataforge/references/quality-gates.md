# DataForge — Quality Gates

Reference for `validate.py` and the `df-validate` agent.

## Hard Stop Rules (Exit Code 2 — Pipeline Must Halt)

The orchestrator must stop and report these to the user. Never override without
explicit user confirmation.

| Check | Threshold | Reason |
|-------|-----------|--------|
| Minimum samples | < 50 rows | Models cannot generalize on tiny datasets |
| Target column exists | Column not found | Pipeline has no target to optimize for |
| Target variance | Only 1 unique value | Cannot train on a constant target |
| Target leakage | Any feature correlation ≥ 0.99 with target | Feature contains future info or is derived from target |

## Warning Rules (Exit Code 1 — Continue With Mitigation)

Report these to the user before proceeding. Apply automatic mitigations.

| Check | Threshold | Automatic Mitigation |
|-------|-----------|---------------------|
| Class imbalance | Majority:minority ratio > 10:1 | Set `class_weight='balanced'` on all classifiers |
| High missing values | Any column > 50% missing | Impute with median (numeric) / mode (categorical); warn user |
| Duplicate rows | Duplicate % > 5% | Deduplicate automatically (keep first) |
| Constant columns | nunique ≤ 1 | Drop automatically |
| ID-like columns | cardinality > 0.95 AND n_rows > 100 | Drop automatically (unless it is the target column) |

## Leakage Detection Detail

Target leakage occurs when a feature:
1. Is derived FROM the target (computed after the fact)
2. Contains future information not available at prediction time
3. Is a near-duplicate of the target

Common leakage patterns (see `leakage-patterns.md` for full list):
- Correlation ≥ 0.99 with target → HARD STOP
- Feature name contains "target", "label", "y_", "output" → WARNING, flag for user review
- Datetime features with timestamps AFTER the event → WARNING

## Override Protocol

If a user explicitly wants to override a HARD STOP:
1. Ask the user to confirm in plain language: "I understand this will produce unreliable results"
2. Log the override decision in `memory/decisions.md`
3. Proceed with the pipeline but add a warning banner to the final report

## Adding New Quality Gates

To add a new validation check:
1. Add a `check_*` function to `scripts/validate.py` following the existing pattern
2. Add it to the `checks` list in `main()`
3. Document it here with threshold and rationale
