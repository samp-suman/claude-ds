# Domain Reference: Manufacturing

## Key Performance Indicators (KPIs)
- Overall Equipment Effectiveness (OEE) = Availability × Performance × Quality
- Mean Time Between Failures (MTBF)
- Mean Time To Repair (MTTR)
- First Pass Yield (FPY)
- Defects Per Million Opportunities (DPMO)
- Cpk / Ppk (process capability indices)
- Scrap rate / Rework rate
- Downtime percentage

## Critical Manufacturing Features

| Feature | Typical Range | Significance |
|---------|-------------|--------------|
| OEE | 60–85% | World-class ≥ 85%, < 60% = significant losses |
| Cpk | 0.5–2.0 | < 1.0 = not capable, ≥ 1.33 = acceptable, ≥ 1.67 = good |
| MTBF | Hours–years | Equipment-dependent, trend matters more than absolute |
| Temperature | Process-specific | Deviation from setpoint = quality risk |
| Vibration | Process-specific | Increasing trend = wear/failure precursor |
| Pressure | Process-specific | Out-of-range = defect or failure risk |
| Cycle time | Seconds–hours | Variation indicates process instability |

## Domain-Specific Feature Engineering
- **Rolling statistics**: Mean, std, min, max over 1h/4h/24h windows for all sensor readings
- **Rate of change**: First derivative of sensor values — captures degradation trends
- **Setpoint deviation**: `abs(actual - setpoint)` for all controlled variables
- **Interaction features**: Temperature × pressure, speed × force — physical interactions matter
- **Cumulative features**: Total cycles since maintenance, cumulative operating hours
- **Time since events**: Hours since last maintenance, last tool change, last defect
- **Batch/lot features**: Batch mean quality, supplier lot quality history
- **Alarm counts**: Number of alarms in recent windows (1h, 8h, 24h)
- **Shift features**: Operator shift, day/night, weekend — human factors affect quality
- **Environmental**: Ambient temperature, humidity — affect process stability

## Common Pitfalls
1. **Sensor noise vs signal**: Raw sensor data needs smoothing (moving average, Kalman filter) before feature extraction
2. **Rare event prediction**: Equipment failures are rare (1:1000+ cycles) — severe imbalance
3. **Temporal dependencies**: Sensor readings are autocorrelated — random CV splits are wrong, use time-based
4. **Multivariate interactions**: Individual sensors may be in range, but combinations indicate failure
5. **Right censoring**: Equipment still running = survival data, not classification
6. **Concept drift**: Equipment degrades, processes change, new materials introduced
7. **High-frequency data**: Sampling rate matters — downsampling may lose failure signatures
8. **Mixed units**: Sensors in different units/scales — always normalize per sensor

## Preferred Metrics
- **Predictive maintenance**: Precision-recall AUC, lead time accuracy, false alarm rate
- **Quality prediction**: F1 for defect detection, Cpk improvement
- **Anomaly detection**: AUC-ROC, F1, detection lead time
- **Yield optimization**: R², RMSE on yield percentage
- **Remaining useful life**: RMSE, MAE on time-to-failure

## Analysis Types
- **SPC (Statistical Process Control)**: Control charts (X-bar, R, p, c), run rules
- **Predictive maintenance**: Survival analysis, degradation modeling, anomaly detection
- **Root cause analysis**: Decision trees, SHAP for defect drivers
- **Process optimization**: DOE, response surface methodology
- **Anomaly detection**: Isolation Forest, Autoencoders, DBSCAN for process anomalies

## SPC-Specific Knowledge
- **Control limits**: UCL/LCL at ±3σ from process mean (NOT specification limits)
- **Nelson rules**: 8 rules for detecting non-random patterns in control charts
- **Cpk vs Ppk**: Cpk = within-subgroup, Ppk = overall — both matter
- **Western Electric rules**: Zone-based pattern detection
- **Process capability**: Cp ≥ 1.33 minimum, ≥ 2.0 for safety-critical

## Red Flags
- Random train/test split on time-series sensor data (must use temporal split)
- Sensor readings used without lag features (current reading doesn't predict future failure)
- No rolling/window aggregations on raw sensor data
- Defect prediction without tool/batch/lot context
- Model ignores maintenance events (maintenance resets baseline)
- Cpk/OEE used as input feature without understanding they're derived metrics
