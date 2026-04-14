---
area: manufacturing
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area manufacturing
status: seed
schema_version: 1.0
---

# Manufacturing — Domain Knowledge

## Core techniques

### [mfg-001] Predictive maintenance framing
**Summary:** Three valid framings: (a) binary "fail in next N hours", (b) RUL (remaining useful life) regression, (c) survival/hazard. Pick based on label availability. RUL needs run-to-failure histories; binary needs censoring care.

### [mfg-002] Sensor data preprocessing
**Summary:** Resample to a common cadence, fill short gaps with interpolation, longer gaps as flags. Apply Butterworth or Savitzky-Golay filters BEFORE feature extraction. Use `tsfresh` or `tsflex` for automated time-series features.

### [mfg-003] Anomaly detection on streams
**Summary:** Isolation Forest, LOF, autoencoders for unsupervised. For known fault signatures use matched filters / template matching. Always set thresholds on a quiet baseline period, not the whole dataset.

### [mfg-004] Quality control / SPC features
**Summary:** Control-chart features (CUSUM, EWMA, Western Electric rules) are still gold-standard. Add them as inputs to ML models rather than replacing them.

### [mfg-005] Operating-regime conditioning
**Summary:** A pump at 50% load behaves differently than at 90%. Train regime-conditional models or include load/RPM/temperature as explicit features. Otherwise the model averages across regimes and misses faults.

## Pitfalls

- Survivor bias: machines that ran for years are over-represented; early failures are under-sampled.
- Concept drift: maintenance schedules, raw materials, and operator changes shift the distribution. Monitor and retrain quarterly.
- Imbalanced failures: most days are "normal". Use focal loss or PR-AUC, not accuracy.
- Sensor calibration drift produces fake anomalies. Always cross-check against redundant sensors.

## Recommended metrics

- **Predictive maintenance**: precision@time-window, recall@lead-time, alarm-rate per day.
- **RUL**: scoring function from PHM challenges (asymmetric: late predictions cost more), MAE in hours.
- **Quality**: F1 on defective class, capability indices (Cp, Cpk).

## Key sources

- NASA C-MAPSS turbofan dataset and benchmarks
- PHM Society data challenges
- Siemens / GE / Honeywell industrial AI whitepapers
- "Hands-On Industry 4.0" books and Vibration Institute notes
