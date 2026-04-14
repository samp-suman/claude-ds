---
area: mlops
category: role
track: common
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area mlops
status: seed
schema_version: 1.0
---

# MLOps — Monitoring, Drift, Deployment Reliability

## Core principles

### [mlops-001] Monitor inputs before outputs
**Summary:** Output drift is downstream of input drift. Track per-feature distributions (KS test, PSI, Wasserstein) on the live request stream against the training set. Alert on PSI > 0.2.

### [mlops-002] Three drift types
**Summary:** (a) Data drift = P(X) changes; (b) Concept drift = P(Y|X) changes; (c) Label drift = P(Y) changes. Different fixes: (a) retrain, (b) refit + maybe new features, (c) recalibrate threshold.

### [mlops-003] Shadow mode for new models
**Summary:** Deploy the new model alongside the old, run both, log predictions, compare. Promote only after N days of agreement and a metric improvement on a real holdout.

### [mlops-004] Canary + rollback
**Summary:** Route 1% -> 10% -> 50% -> 100% over hours. Auto-rollback on error-rate or latency regression. Never deploy a model on Friday afternoon.

### [mlops-005] Reproducible training
**Summary:** Capture data version (DVC / lakeFS / Delta time-travel), code version (git SHA), config (Hydra / OmegaConf), environment (poetry.lock). Re-run produces byte-identical model.

### [mlops-006] Cost monitoring
**Summary:** Inference costs grow with traffic. Track $/1k predictions, GPU utilization, batch size efficiency. Many teams overspend 5x by serving on GPUs they don't need.

### [mlops-007] Feedback loops cause silent failure
**Summary:** When model output influences future inputs (recommendations, fraud blocking, ad targeting), the training distribution drifts toward what the model already accepts. Always reserve untargeted holdouts.

## Pitfalls

- Logging the prediction but not the input feature vector - you can't debug later.
- Alerts on raw metric dips during traffic spikes (use rate-of-change, not absolute thresholds).
- Storing model artifacts on a developer's laptop instead of an artifact store.
- No retraining cadence; the model rots and nobody notices for months.
- Treating MLOps as "DevOps for ML" - it has additional concerns (data, drift, retraining) that DevOps doesn't.

## Tools to know

- **Tracking**: MLflow, Weights & Biases, Neptune, ClearML.
- **Drift**: Evidently, NannyML, WhyLabs, Fiddler, Arize.
- **Versioning**: DVC, lakeFS, Pachyderm, Delta Lake.
- **Orchestration**: Kubeflow, Metaflow, Flyte, Airflow.
- **Feature stores**: Feast, Tecton, Hopsworks.

## Key sources

- "Reliable Machine Learning" (O'Reilly, Chen, Loftus)
- Evidently AI blog (drift methodology)
- Google "ML Test Score" paper
- "Hidden Technical Debt in Machine Learning Systems" (Sculley et al.)
