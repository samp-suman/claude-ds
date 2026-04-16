---
name: df-mlops-pipeline
description: Orchestrate production ML workflows end-to-end. Design CI/CD pipelines for models, coordinate complex DAGs, manage event-driven architectures, handle streaming data, and automate retraining. Enables continuous deployment, reproducibility, and production reliability.
---

# MLOps Pipeline

## Purpose

Build and operate production-grade ML pipelines. Orchestrate complex workflows, automate retraining, manage model versioning, enforce quality gates at each stage, and enable continuous deployment. Make ML systems reliable, auditable, and reproducible.

## When to Use This Skill

- **Pipeline orchestration** — Coordinate ETL, training, evaluation, deployment stages
- **CI/CD for ML** — Automate testing, versioning, and rollout of models
- **Event-driven workflows** — React to events (new data, model drift, retraining triggers)
- **Streaming pipelines** — Handle continuous data streams (Kafka, Pub/Sub)
- **Model versioning** — Track model lineage, enable rollback
- **Automated retraining** — Trigger retraining on schedule or on data drift
- **Production automation** — Remove manual deployment steps

## Key Responsibilities

### 1. Pipeline Orchestration Design

**Stage 1: Data Ingestion & Validation**
```
Event: New data arrives
  ├─ Ingest (fetch from source, validate schema)
  ├─ Quality check (missing values, outliers, duplicates)
  ├─ Trigger next stage if validation passes
  └─ Alert if validation fails (HARD STOP)
```

**Stage 2: Feature Engineering**
```
Event: Data validated
  ├─ Compute features (domain features, aggregates)
  ├─ Store in feature store (versioned, reusable)
  ├─ Profile features (distribution, missing %)
  └─ Trigger training stage
```

**Stage 3: Model Training**
```
Event: Features ready
  ├─ Load training data
  ├─ Train models (parallel: Ridge, XGBoost, Neural Net)
  ├─ Evaluate on holdout set
  ├─ Compare to baseline
  └─ Trigger deployment only if beats baseline
```

**Stage 4: Model Evaluation & Validation**
```
Event: Model trained
  ├─ Fairness check (disparate impact < 5%)
  ├─ Adversarial robustness check
  ├─ Latency check (inference < 100ms)
  ├─ Cost check (inference < $0.01)
  └─ Fail fast if any check fails
```

**Stage 5: Deployment**
```
Event: All validations pass
  ├─ Stage 1: Deploy to canary (1% traffic)
  ├─ Monitor for 1 hour (latency, error rate)
  ├─ Stage 2: Deploy to 10% traffic
  ├─ Monitor for 2 hours
  ├─ Stage 3: Deploy to 100% traffic
  └─ Keep old model available for quick rollback
```

**Stage 6: Monitoring & Alerting**
```
Continuous monitoring:
  ├─ Prediction latency (alert if p99 > 200ms)
  ├─ Error rate (alert if > 1%)
  ├─ Data drift (alert if feature distribution changes)
  ├─ Prediction drift (alert if output distribution changes)
  └─ Performance drift (alert if accuracy drops > 5%)
```

### 2. Workflow Orchestration Tools

**Tool Selection:**

| Tool | Strength | Best For |
|------|----------|----------|
| **Apache Airflow** | Rich ecosystem, complex DAGs | Large enterprises, complex workflows |
| **Prefect** | Cloud-native, Pythonic, modern UI | MLOps teams, cloud-first |
| **Dagster** | Asset-oriented, declarative | Data pipelines, feature management |
| **Kubeflow** | Kubernetes-native, GPU support | Large-scale parallel training |
| **GitHub Actions** | Free for public repos, tight integration | Open-source, small teams |

**Example: Airflow DAG structure**
```python
# DAG definition (declarative)
ingest_task >> validate_task >> feature_task >> train_task >> evaluate_task >> deploy_task

# Each task is atomic and can fail independently
# Retry logic built in
# Monitoring/alerting integrated
```

### 3. CI/CD for ML Models

**Traditional CI/CD (software):**
- Push code → Lint → Unit test → Build → Deploy

**ML CI/CD (must add):**
- Push code → Lint → Unit test → **Train model** → **Evaluate on test data** → **Compare to baseline** → Deploy (only if improves)

**Implementation:**

```
1. Trigger: Code merged to main
2. GitHub Actions runs:
   a. Install dependencies
   b. Run unit tests (data validation, feature encoding)
   c. Train model on snapshot data
   d. Evaluate on test set
   e. Compare metrics to baseline
   f. If better: push model to registry + approve for deployment
   g. If worse: BLOCK deployment, alert to team
3. Separate deployment pipeline:
   a. Manual approval (security)
   b. Deploy to staging → smoke test
   c. Deploy to prod with canary strategy
   d. Monitor for 1 hour before full rollout
```

**Key difference:** ML pipelines must **validate model quality**, not just code quality.

### 4. Event-Driven Workflows

**Triggers for retraining:**

| Event | Action |
|-------|--------|
| Schedule (daily/weekly) | Retrain all models |
| Data drift detected | Retrain affected models |
| Prediction accuracy drops | Immediate retraining |
| New data arrives | Incremental training |
| Model performance < baseline | Rollback + alert |

**Example: Kafka-based event stream**
```
Data source → Kafka topic
  ├─ Consumer 1: Feature computation (updates feature store)
  ├─ Consumer 2: Data quality monitoring (alerts on drift)
  └─ Consumer 3: Model retraining trigger (if conditions met)
```

### 5. Streaming Data Pipelines

**Batch vs Streaming:**

| Aspect | Batch | Streaming |
|--------|-------|-----------|
| Data arrival | Bulk, periodic (daily) | Continuous (milliseconds) |
| Latency | Hours acceptable | Sub-second required |
| Volume | GB → TB | KB → MB per message |
| Example | Daily sales report | Real-time fraud detection |

**Streaming Stack (Kafka example):**
```
Data source → Kafka (input topic)
  ├─ Kafka Streams/Apache Flink
  ├─ Real-time feature computation
  ├─ Join with feature store
  └─ Kafka (output topic) → Model inference → Action
```

**Monitoring Streaming Pipelines:**
- Consumer lag (how far behind real-time?)
- Message rate (requests/sec)
- Error rate (failed inference, data errors)
- Latency percentiles (p50, p95, p99)

### 6. Model Versioning & Artifact Management

**What to version:**

```
model-registry/
├── model-v1/
│   ├── model.pkl           # Serialized model
│   ├── preprocessing.pkl   # Encoder, scaler
│   ├── metadata.json       # Training params, metrics
│   └── requirements.txt    # Dependencies
├── model-v2/
│   └── ...
└── model-v3-prod/          # Current production
    └── ...
```

**Metadata to track:**

```json
{
  "model_id": "credit-risk-v3",
  "version": "3",
  "training_date": "2026-04-15",
  "training_data_snapshot": "20260415_snapshot.parquet",
  "accuracy_test": 0.92,
  "fairness_check": "disparate_impact=0.03",
  "latency_p99_ms": 150,
  "deployment_status": "production",
  "previous_version": "credit-risk-v2",
  "rollback_available": true
}
```

**Deployment Path:**
```
Model trained → Registered in model registry
  ├─ Staging: Deploy to test environment
  ├─ Canary: 1% production traffic
  ├─ Production: 100% traffic (if canary succeeds)
  └─ Monitoring: Track performance continuously
```

## Decision Scenarios

### Scenario 1: "How do we automate model retraining?"

**Analysis:**
```
Current: Manual retraining every Friday (labor-intensive, delays)
Goal: Automatic retraining without manual intervention

Implementation:
1. Data drift detector (runs daily)
   - Compare current feature distribution to baseline
   - If KL divergence > threshold: trigger retraining
   
2. Automated retraining job (Airflow DAG)
   - Fetch latest data
   - Train new model
   - Compare to current production model
   - If better: deploy to staging
   - Manual approval for production
   
3. Scheduled retraining (weekly baseline)
   - Even if no drift detected, retrain for freshness
   - Ensures model doesn't become stale

4. Performance-based retraining (reactive)
   - If accuracy drops > 5%: trigger emergency retraining
   - Alert team to investigate root cause
```

### Scenario 2: "Our CI/CD pipeline doesn't validate model quality"

**Problem:**
```
Current flow: Code → Tests → Deploy (no model evaluation)
Issue: Bad models get deployed silently
```

**Solution:**
```
New flow: Code → Tests → [Train model] → [Evaluate] → Deploy (only if improves)

Implementation (GitHub Actions):
1. On pull request:
   - Train model on snapshot data
   - Compare metrics to baseline
   - Block merge if worse
   - Show metrics in PR comment

2. On merge to main:
   - Train final model
   - If better: approve for deployment
   - If worse: notify team, investigate
```

### Scenario 3: "We need to deploy a new model with zero downtime"

**Canary Deployment Strategy:**
```
Hour 0:00 - 0:30: Canary (1% traffic)
  ├─ Monitor: latency, error rate, prediction quality
  ├─ Success: no anomalies
  └─ Failure: rollback immediately

Hour 0:30 - 1:30: Gradual rollout (1% → 10%)
  ├─ Monitor: latency, accuracy, user feedback
  ├─ Success: continue
  └─ Failure: rollback (keep old model running)

Hour 1:30 - 2:30: Full rollout (10% → 100%)
  ├─ Monitor: all metrics
  ├─ Success: update production, keep v1 available for 48h
  └─ Failure: rollback to v1 (single command)

Rollback is instant: traffic routing flips to old model immediately
```

## Anti-Patterns

❌ **Anti-pattern 1:** "Manual deployment — copy files to production"
- Problem: Error-prone, no rollback, no testing
- Solution: Automated canary deployment with monitoring

❌ **Anti-pattern 2:** "No model versioning — just overwrite the file"
- Problem: Can't rollback if new model is bad
- Solution: Version every model, keep last 3 versions available

❌ **Anti-pattern 3:** "Train only on schedule (weekly), not on drift"
- Problem: Miss degradation if training schedule misses drift
- Solution: Trigger retraining on both schedule AND drift detection

❌ **Anti-pattern 4:** "No quality gates — any model goes to prod"
- Problem: Bad models silently hurt business metrics
- Solution: Enforce: must beat baseline AND pass fairness checks

❌ **Anti-pattern 5:** "Streaming pipeline with no backpressure"
- Problem: Queue fills up, messages lost, downstream crashes
- Solution: Monitor consumer lag, throttle if necessary

## Memory Tracking

```json
{
  "pipeline_decision": "retraining_trigger",
  "trigger_type": "data_drift",
  "threshold_kl_divergence": 0.05,
  "retraining_frequency": "daily",
  "deployment_strategy": "canary",
  "canary_duration_minutes": 30,
  "canary_traffic_percent": 1,
  "rollback_capability": true,
  "model_registry_enabled": true,
  "implementation_date": "2026-04-17",
  "review_date": "2026-05-01"
}
```

## Implementation Checklist

- [ ] Choose orchestration tool (Airflow/Prefect/Dagster)
- [ ] Define pipeline stages with quality gates
- [ ] Implement data validation at each stage (fail fast)
- [ ] Set up model registry (versioning, metadata)
- [ ] Add model evaluation step to CI/CD (compare to baseline)
- [ ] Implement canary deployment (1% → 10% → 100%)
- [ ] Set up drift detection (automatic retraining trigger)
- [ ] Monitor all pipelines (latency, error rate, completion)
- [ ] Document rollback procedure (must be instant)
- [ ] Test disaster recovery (what if model breaks?)

