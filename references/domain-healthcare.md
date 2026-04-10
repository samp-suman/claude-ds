# Domain Reference: Healthcare

## Key Performance Indicators (KPIs)
- Sensitivity/Recall (most critical — missing a diagnosis is worse than a false alarm)
- Specificity, PPV, NPV
- AUC-ROC for screening models
- C-statistic for survival models
- NNT (Number Needed to Treat)

## Critical Clinical Features

| Feature | Normal Range | Clinical Significance |
|---------|-------------|----------------------|
| HbA1c | < 5.7% | ≥ 6.5% = diabetes (ADA threshold) |
| BMI | 18.5–24.9 | ≥ 30 = obese, clinical risk bins matter |
| Blood Pressure | < 120/80 | Stage 1: 130-139/80-89, Stage 2: ≥ 140/90 |
| Heart Rate | 60–100 bpm | Bradycardia < 60, Tachycardia > 100 |
| Glucose (fasting) | 70–100 mg/dL | 100–125 = prediabetes, ≥ 126 = diabetes |
| Cholesterol (total) | < 200 mg/dL | 200–239 = borderline, ≥ 240 = high |
| eGFR | > 60 mL/min | < 60 = kidney disease, stages matter |
| Hemoglobin | M: 14-18, F: 12-16 g/dL | Low = anemia, high = polycythemia |
| WBC | 4,500–11,000/µL | High = infection/inflammation |
| Creatinine | 0.7–1.3 mg/dL | Elevated = kidney dysfunction |

## Domain-Specific Feature Engineering
- **Clinical bins**: Don't treat vitals as continuous — bin into clinical risk categories
- **BMI**: Calculate from height/weight if not present: `weight_kg / (height_m ^ 2)`
- **Comorbidity indices**: Charlson Comorbidity Index, Elixhauser
- **Length of stay**: Derived from admission/discharge dates
- **Readmission window**: 30-day readmission flag is standard
- **Age groups**: Pediatric (<18), Adult (18-64), Elderly (≥65)
- **ICD/CPT grouping**: Roll up to category level, not individual codes
- **Lab result trends**: Delta between sequential lab values more predictive than single values
- **Medication interactions**: Flag concurrent medications with known interactions

## Common Pitfalls
1. **Treating clinical thresholds as continuous**: HbA1c of 6.4 vs 6.6 crosses a diagnostic boundary — bin, don't scale
2. **Ignoring censoring**: Survival data needs Cox regression or Kaplan-Meier, not standard classification
3. **Leakage from future data**: Discharge diagnosis available at admission time? That's leakage
4. **Class imbalance in rare diseases**: Prevalence can be 1:1000+. Use recall-focused metrics, never accuracy
5. **Confounders**: Age and sex confound nearly everything in clinical data
6. **HIPAA considerations**: PHI columns (name, DOB, SSN, MRN) must be excluded — not just for privacy but they're also leakage

## Preferred Metrics
- **Diagnosis/screening**: Sensitivity (recall) as primary, with AUC-ROC
- **Prognosis**: C-statistic, calibration plots
- **Risk stratification**: AUC-ROC, Net Reclassification Index
- **Treatment response**: NNT, absolute risk reduction

## Red Flags
- Model uses patient ID, MRN, or encounter ID as a feature
- Accuracy used as primary metric for imbalanced diagnosis task
- Future information (discharge status, outcome date) available in features
- Lab values outside physiological range kept without investigation
- No age/sex adjustment in the model
