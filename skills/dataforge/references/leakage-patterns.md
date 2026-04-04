# DataForge — Data Leakage Patterns

A reference guide for the `df-validate` agent and any manual review.

## What Is Data Leakage?

Leakage occurs when information from outside the training time window (or derived
from the target itself) is used as a feature. It produces unrealistically high
model performance during training that collapses in production.

## Pattern 1: Target Derivation

Feature is computed from the target or is the same information in disguise.

**Examples:**
- `profit_margin` when target is `profit` and `revenue` is another feature
- `churn_reason` when target is `churn` (can only exist if churn happened)
- `fraud_score` when target is `is_fraud` (the score IS the label)

**Detection:** Correlation ≥ 0.99 with target → HARD STOP

## Pattern 2: Future Data Leakage

Feature uses information not yet available at prediction time.

**Examples:**
- `total_year_purchases` for a January fraud detection model (full-year data unavailable in January)
- `outcome_date` — a date field that only exists after the event occurs
- `30_day_readmission_flag` used to predict same-day discharge outcome

**Detection:** Look for column names containing "result", "outcome", "final", "total_year",
"end_date", "completion". Flag for user review.

## Pattern 3: Proxy Leakage

Feature is not the target but is a near-perfect proxy.

**Examples:**
- `employee_id` for a promotion prediction model (IDs were assigned based on seniority)
- `zip_code` binned at very fine granularity when model is predicting income

**Detection:** High correlation AND column type is categorical/ID — flag for review.

## Pattern 4: Train/Test Contamination

Test data statistics bleed into training data preprocessing.

**Examples:**
- Fitting a scaler on the full dataset before splitting train/test
- Computing mean imputation values on the full dataset

**Prevention (automatic in DataForge):** All scalers and imputers are fit ONLY on training
split, then applied to test split. Never fit on combined data.

## Pattern 5: Time-Series Leakage

For time-series problems, using future observations in features.

**Examples:**
- Rolling averages computed with future values included
- Lag features using the wrong window

**Detection:** If `problem_type = time_series`, DataForge uses time-based train/test split
and validates that no feature uses future index values.

## Column Name Red Flags (Auto-Flagged as Warnings)

The following substrings in column names trigger a warning review:
`target`, `label`, `y_`, `output`, `result`, `outcome`, `churn_`, `fraud_`,
`default_`, `converted_`, `purchased_`, `clicked_`

These are warnings, not hard stops — the column may be legitimately named this way.
Always confirm with the user before dropping.

## What DataForge Does About Leakage

1. **Correlation check** → HARD STOP if ≥ 0.99
2. **Name pattern check** → WARNING + user notification
3. **Time leakage check** → Enforced via time-based splitting for time-series problems
4. **Logged in decisions.md** → User can see what was dropped and why
