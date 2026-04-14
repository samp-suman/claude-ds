---
area: ml-engineer
category: role
track: common
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area ml-engineer
status: seed
schema_version: 1.0
---

# ML Engineer — Serving and Optimization Knowledge

## Core principles

### [mle-001] Train/serve symmetry via fitted pipelines
**Summary:** Pickle the entire `sklearn.Pipeline` (preprocessor + model). The serving app does `pipeline.transform(raw_input)` then `predict()`. Never reimplement preprocessing in app code.
**Pitfall:** Train/serve skew is the #1 cause of "good offline, bad online" models.

### [mle-002] Inference latency budget
**Summary:** Establish p50/p95/p99 targets BEFORE picking the model. A 200ms XGBoost inference is fine for batch but blows a 50ms real-time SLO. Profile with `py-spy` or `scalene`, optimize the slowest 1%.

### [mle-003] Model artifact versioning
**Summary:** Every model gets `{name}_{train_hash}_{timestamp}.pkl` plus a manifest with: training data hash, library versions, metrics, git SHA. Serve by manifest, not by filename.

### [mle-004] Batch vs online vs streaming
**Summary:** Batch (Airflow/Prefect) is cheapest and most reliable. Online (FastAPI/BentoML) for <1s SLOs. Streaming (Kafka + Flink) only when you truly need event-by-event reaction. Default to batch.

### [mle-005] Model size optimization
**Summary:** XGBoost / LightGBM models compress 5-10x with `joblib.dump(..., compress=3)`. ONNX export shrinks further and removes the Python runtime dependency. For deep models: quantization (INT8), pruning, distillation.

### [mle-006] Container reproducibility
**Summary:** Pin EVERY dependency including transitive (`pip-compile` -> `requirements.txt` with hashes). Build on `python:3.11-slim`, multi-stage to drop build deps. Never `:latest`.

### [mle-007] Health checks and graceful shutdown
**Summary:** `/health` (liveness, instant) + `/ready` (readiness, only true after model loaded). Handle SIGTERM to drain in-flight requests. Without these, K8s rolling updates drop traffic.

## Pitfalls

- Loading the model on every request instead of once at startup.
- Logging full request payloads (PII risk + log volume blow-up).
- No timeout on prediction calls -> a slow request blocks the worker.
- Synchronous prediction in async frameworks (FastAPI def vs async def) wastes the event loop.
- Ignoring CPU vs GPU memory layouts when porting from notebook to server.

## Tools to know

- **Serving**: BentoML, Ray Serve, FastAPI + Uvicorn, TorchServe, Triton, MLflow models.
- **Optimization**: ONNX Runtime, OpenVINO, TensorRT, llama.cpp for LLMs.
- **Profiling**: py-spy, scalene, austin, line_profiler.
- **Load testing**: locust, k6, vegeta.

## Key sources

- Chip Huyen "Designing Machine Learning Systems"
- Google "Rules of Machine Learning"
- Made With ML / MLOps Community blog
- Anyscale / Ray docs on model serving patterns
