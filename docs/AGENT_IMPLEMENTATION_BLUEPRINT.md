---
title: DataForge Agent Implementation Blueprint
subtitle: Concrete specs for 8 consolidated agents
date: 2026-04-17
status: Ready for implementation
---

# DataForge Agent Implementation Blueprint

## Agent 1: `df-data-architect`

### Purpose
Own the data lifecycle: raw → ingested → transformed → production-ready.

### Input Contract
```json
{
  "data_source": "s3://bucket/file.csv or local path",
  "data_format": "csv|parquet|json|sql_query",
  "volume_estimate_gb": 10,
  "update_frequency": "daily|weekly|monthly|once",
  "schema_description": "Optional: describe expected columns",
  "constraints": {
    "max_size_mb": 5000,
    "required_columns": ["id", "date", "value"]
  }
}
```

### Output Contract
```json
{
  "ingestion_plan": {
    "approach": "batch|streaming|hybrid",
    "partitioning": "by date|by domain|by hash",
    "format": "parquet|csv",
    "compression": "snappy|gzip",
    "expected_size_mb": 500,
    "estimated_cost_$/day": 2.5
  },
  "layer_design": {
    "raw_data": "/data/raw/{date}/ — archived, never modified",
    "interim": "/data/interim/{date}/ — transforms logged",
    "processed": "/data/processed/ — validated, production-ready"
  },
  "lineage_tracking": {
    "decision_log": "memory/data_decisions.json",
    "transform_history": "memory/transform_state.json",
    "audit_trail": "memory/audit_trail.md"
  },
  "quality_gates": {
    "ingest_check": ["schema_match", "no_nulls_in_id", "duplicates < 0.1%"],
    "profile_check": ["outliers characterized", "missing values < 20%"],
    "transform_check": ["output matches contract", "value ranges reasonable"]
  },
  "recovery_strategy": {
    "on_schema_mismatch": "alert human, do not process",
    "on_missing_values": "threshold-based: <5% drop, 5-30% impute, >30% flag",
    "on_duplicates": "log pattern, dedup, track reason"
  }
}
```

### Key Decisions
1. **Batch vs Streaming** — Data arrival frequency + latency requirement
2. **Incremental vs Full Refresh** — Schema stability determines strategy
3. **Partitioning Strategy** — Date, domain, or hash (impacts query speed)
4. **Compression** — Snappy (fast), gzip (small) based on access patterns
5. **Archival Policy** — Keep raw data for 2 years (reproducibility)

### Memory Tracking
```json
{
  "run_id": "2026-04-17_data_architect_001",
  "data_source": "titanic.csv",
  "ingestion_approach": "batch",
  "rationale": "One-time dataset, small volume",
  "outcomes": {
    "rows_ingested": 891,
    "columns": 12,
    "missing_pct": 0.02,
    "duplicates": 0,
    "processing_time_seconds": 2.3
  },
  "next_time": "This data format is clean; prioritize encoding categorical features"
}
```

---

## Agent 2: `df-quality-engineer`

### Purpose
Ensure data quality at every stage; detect degradation before problems cascade.

### Input Contract
```json
{
  "stage": "ingest|profile|transform|evaluate",
  "data": "path/to/data.parquet",
  "schema": {"column_name": "dtype"},
  "quality_thresholds": {
    "missing_values_pct": 20,
    "class_imbalance_ratio": 0.1,
    "outlier_pct": 5,
    "duplicate_rate": 0.001
  }
}
```

### Output Contract
```json
{
  "stage": "ingest",
  "quality_checks": {
    "hard_blocks": [
      {
        "check": "schema_match",
        "status": "PASS",
        "details": "All columns match expected schema"
      }
    ],
    "soft_warnings": [
      {
        "check": "missing_values",
        "status": "WARN",
        "value": 2.3,
        "threshold": 20,
        "action": "continue but flag for imputation"
      }
    ]
  },
  "report": "memory/quality_report_{stage}_{timestamp}.json",
  "next_actions": [
    "Proceed to next stage",
    "OR investigate missing values",
    "OR stop and alert human"
  ]
}
```

### Quality Checks by Stage

**Ingest Stage:**
- Schema match ✓ (hard block)
- No nulls in ID columns ✓ (hard block)
- Duplicates < 0.1% ✓ (soft warning)
- Data types correct ✓ (soft warning)
- Encoding issues (e.g., UTF-8 problems) ✓ (soft warning)

**Profile Stage:**
- Missing values < 20% ✓ (soft warning)
- Outliers characterized ✓ (soft warning)
- Class imbalance (for classification) ✓ (info)
- Numeric ranges sensible ✓ (soft warning)

**Transform Stage:**
- Output shape matches contract ✓
- Value ranges after transform sensible ✓
- No new nulls introduced ✓
- Encoding applied correctly ✓

**Evaluate Stage:**
- Train/test sizes balanced ✓
- No leakage detected ✓
- Metrics calculated ✓
- Fairness check passed ✓

### Drift Detection
```json
{
  "metric": "missing_value_percentage",
  "baseline": 2.3,
  "current": 15.0,
  "threshold_alert": 20,
  "threshold_block": 30,
  "status": "WARN — approaching threshold",
  "action": "Investigate why missing values increased 6x"
}
```

### Memory Tracking
```json
{
  "run_id": "2026-04-17_quality_001",
  "stage": "ingest",
  "data": "titanic.csv",
  "checks": {
    "passed": ["schema_match", "no_nulls_in_id"],
    "warned": ["missing_values: 0.02%"]
  },
  "decisions": "Missing values < threshold; proceed to next stage",
  "outcomes": "Data passed quality gate; no delays"
}
```

---

## Agent 3: `df-feature-architect`

### Purpose
Transform raw features into predictive power; design reusable feature infrastructure.

### Input Contract
```json
{
  "data": "path/to/processed_data.parquet",
  "target": "column_name",
  "problem_type": "regression|classification|clustering",
  "domain": "auto|finance|healthcare|ecommerce",
  "feature_budget": 50,
  "constraints": {
    "max_cardinality": 1000,
    "interpretability_required": true,
    "latency_critical": false
  }
}
```

### Output Contract
```json
{
  "feature_engineering": {
    "new_features": [
      {"name": "age_at_sale", "type": "numeric", "source": "year_built", "reason": "Domain knowledge: age is predictive"},
      {"name": "rooms_per_area", "type": "numeric", "source": "[bedrooms, sqft]", "reason": "Density feature"}
    ],
    "encoded_features": [
      {"name": "zip_code", "encoding": "target_encode", "cardinality": 3000, "reason": "High cardinality; target encode for embedding"}
    ]
  },
  "scaling": {
    "numeric_features": "StandardScaler for ridge/lasso; raw for trees",
    "scaling_rationale": "Different models need different scaling"
  },
  "selection": {
    "features_before": 500,
    "features_after": 50,
    "removed": [
      {"name": "feature_x", "reason": "correlation > 0.95 with feature_y", "importance": "< 0.01"}
    ]
  },
  "feature_store": {
    "version": "2026-04-17_v1",
    "columns": ["feature_1", "feature_2", ...],
    "lineage": "memory/feature_lineage.json",
    "compute_time_minutes": 5
  }
}
```

### Feature Engineering Patterns

**Domain Features (by problem type):**
```
Time-based: year, month, day_of_week, is_holiday
Rates: ratio_a_to_b, growth_rate, velocity
Aggregates: sum, mean, std per group
Interactions: multiply features if interaction term improves model
```

**Encoding Strategy:**
```
Numeric: StandardScaler for ridge/lasso; raw for trees
Categorical < 10 unique: one-hot encode
Categorical 10-100 unique: target encode
Categorical > 100 unique: embedding or hash
```

**Feature Selection (one of three approaches):**
```
1. Importance-based: Remove features with importance < threshold
2. RFE: Recursive elimination; keep top N features
3. SHAP-based: Use SHAP values to select features; more interpretable
```

### Memory Tracking
```json
{
  "run_id": "2026-04-17_feature_001",
  "domain": "finance",
  "raw_features": 200,
  "engineered_features": 20,
  "selected_features": 50,
  "encoding_decisions": {
    "zip_code": "target_encode (3000 categories)",
    "age": "raw numeric (already meaningful)"
  },
  "feature_importance": {"age": 0.25, "income": 0.20, ...},
  "outcomes": "Feature engineering improved accuracy from 0.82 to 0.85",
  "next_time": "Target encoding works well for high-cardinality features in this domain"
}
```

---

## Agent 4: `df-modeler`

### Purpose
Select, train, and tune models that respect business constraints and data realities.

### Input Contract
```json
{
  "X_train": "path/to/X_train.parquet",
  "y_train": "path/to/y_train.parquet",
  "X_test": "path/to/X_test.parquet",
  "y_test": "path/to/y_test.parquet",
  "problem_type": "regression|classification|multiclass",
  "constraints": {
    "latency_ms": 50,
    "budget_$/day": 10,
    "interpretability": "required|preferred|not_required",
    "fairness": {"protected_attribute": "protected_group", "max_disparate_impact": 0.05}
  },
  "evaluation_metric": "r2|accuracy|f1|auc",
  "tuning_budget": {"trials": 50, "time_minutes": 60}
}
```

### Output Contract
```json
{
  "baseline_model": {
    "type": "Ridge|LogisticRegression|XGBoost",
    "metrics": {"train": 0.75, "test": 0.72},
    "rationale": "Simple, interpretable, fast baseline"
  },
  "challenger_models": [
    {
      "type": "LightGBM",
      "hyperparameters": {"max_depth": 8, "learning_rate": 0.05},
      "metrics": {"train": 0.82, "test": 0.80},
      "latency_ms": 15,
      "cost_$/day": 5
    }
  ],
  "selected_model": {
    "type": "LightGBM",
    "reason": "Best tradeoff: accuracy 0.80 + latency 15ms + cost $5/day",
    "hyperparameters": {...},
    "feature_importances": {...}
  },
  "evaluation": {
    "train_test_split": "temporal|stratified|random",
    "cross_validation": "5-fold, stratified",
    "metrics": {"accuracy": 0.80, "precision": 0.85, "recall": 0.75, "f1": 0.80},
    "fairness": {"disparate_impact": 0.04, "status": "PASS"}
  },
  "training_log": "memory/training_{timestamp}.json",
  "model_artifact": "models/model_{timestamp}.pkl"
}
```

### Model Selection Logic
```
1. Baseline: Ridge (regression) or Logistic (classification)
   - Fast, interpretable, often good enough
   
2. Check constraints:
   - Latency < 10ms? → Use simple model (trees, not neural nets)
   - Large dataset (> 1M rows)? → XGBoost/LightGBM
   - Need interpretability? → Logistic or shallow trees
   - Imbalanced data? → Handle class weights, not SMOTE
   
3. Challenger models (test 2-3 alternatives):
   - LightGBM (speed + accuracy)
   - XGBoost (proven, stable)
   - Neural network (only if above fail)
   
4. Evaluation:
   - Offline metrics (train/test)
   - Fairness check (disparate impact)
   - Error analysis (where does model fail?)
   
5. Deployment readiness:
   - Can we serialize/version this model?
   - Can we monitor drift?
   - Can we rollback quickly?
```

### Hyperparameter Tuning
```json
{
  "strategy": "Bayesian|GridSearch|RandomSearch",
  "budget": {"trials": 50, "time_minutes": 60},
  "objectives": ["maximize accuracy", "minimize latency"],
  "search_space": {
    "max_depth": [5, 6, 7, 8, 9, 10],
    "learning_rate": [0.01, 0.05, 0.1],
    "num_leaves": [31, 63, 127]
  },
  "early_stopping": "If no improvement for 10 trials, stop",
  "best_params": {...}
}
```

### Memory Tracking
```json
{
  "run_id": "2026-04-17_modeler_001",
  "problem_type": "classification",
  "dataset": "titanic",
  "baseline": {"type": "LogisticRegression", "accuracy": 0.78},
  "challenger": {"type": "LightGBM", "accuracy": 0.82},
  "selected": "LightGBM",
  "reason": "4% accuracy improvement + interpretable feature importances",
  "tuning_time": "12 minutes for 50 trials",
  "outcomes": "Model ready for deployment; no fairness issues",
  "next_time": "LightGBM effective for this problem type; try it first"
}
```

---

## Agent 5: `df-model-interpreter`

### Purpose
Explain what your model learned and why it makes its predictions.

### Input Contract
```json
{
  "model": "path/to/model.pkl",
  "X_test": "path/to/X_test.parquet",
  "y_test": "path/to/y_test.parquet",
  "problem_type": "regression|classification",
  "interpretation_depth": "global|local|both",
  "fairness_protected_attribute": "group_column",
  "subgroup_analysis": ["group_1", "group_2"]
}
```

### Output Contract
```json
{
  "global_explanation": {
    "feature_importance": {
      "type": "SHAP|permutation|tree_importance",
      "top_features": [
        {"name": "age", "importance": 0.25, "interpretation": "Strong positive relationship"},
        {"name": "income", "importance": 0.20}
      ],
      "plots": ["feature_importance.png", "beeswarm.png"]
    },
    "interpretation": "Model relies heavily on age and income; other features matter less"
  },
  "local_explanations": {
    "sample_id": 42,
    "prediction": 0.75,
    "explanation": "High prediction due to: age +0.2, income +0.15, education -0.05",
    "nearest_neighbors": "Most similar samples are: [43, 67, 89]"
  },
  "error_analysis": {
    "high_error_regions": [
      {"feature": "age", "range": "> 80", "errors": "Model underestimates"},
      {"feature": "income", "range": "< 20k", "errors": "Class imbalance, hard to predict"}
    ],
    "improvement_suggestions": [
      "Collect more data for age > 80",
      "Use class weights to improve minority class performance"
    ]
  },
  "fairness_analysis": {
    "disparate_impact": 0.04,
    "by_subgroup": {
      "group_1": {"accuracy": 0.85, "precision": 0.90},
      "group_2": {"accuracy": 0.72, "precision": 0.68}
    },
    "threshold_adjustment": "Can increase fairness to 0.95 by adjusting decision boundary",
    "recommendation": "Retrain with class weights or use different threshold per group"
  },
  "comparison_vs_baseline": {
    "baseline_model": "LogisticRegression",
    "challenger_model": "LightGBM",
    "feature_agreement": "70% of top 10 features overlap",
    "interpretation": "Both models agree on most important features; LightGBM captures nonlinearity"
  },
  "reports": {
    "global_report": "reports/global_explanation_{timestamp}.html",
    "fairness_report": "reports/fairness_analysis_{timestamp}.html",
    "error_report": "reports/error_analysis_{timestamp}.html"
  }
}
```

### Interpretation Workflows

**Workflow 1: Global Model Explanation**
1. Compute SHAP values for all test samples
2. Generate feature importance ranking
3. Create beeswarm plot (feature variance)
4. Create force plot (sample-level contribution)
5. Output: "Top 5 features drive 80% of model predictions"

**Workflow 2: Error Analysis**
1. Identify high-error samples
2. Cluster by features (where does error concentrate?)
3. Root cause: "Model fails on age > 80; only 10 samples in training"
4. Recommendation: "Collect more data for underrepresented groups OR use different model"

**Workflow 3: Fairness Analysis**
1. Compute metrics by protected attribute group
2. Check for disparate impact
3. Threshold adjustment: Can we tune decision boundary per group?
4. Recommendation: Retrain with fairness constraint or use different threshold

### Memory Tracking
```json
{
  "run_id": "2026-04-17_interpreter_001",
  "model": "LightGBM",
  "top_features": ["age", "income", "education"],
  "feature_agreement_with_baseline": 0.70,
  "fairness": {
    "disparate_impact": 0.04,
    "recommendation": "Model fair; disparate impact < 5%"
  },
  "error_concentration": "age > 80, income < 20k",
  "next_time": "Prioritize collecting data for underrepresented groups"
}
```

---

## Agent 6: `df-rag-orchestrator`

### Purpose
Build production RAG systems for semantic search, Q&A, and knowledge retrieval.

### Input Contract
```json
{
  "documents": "s3://bucket/docs/ or path/to/docs/",
  "document_types": ["pdf", "html", "markdown"],
  "query_type": "search|qa|generation",
  "retrieval_strategy": "dense|sparse|hybrid",
  "scale": {"documents": 1000, "vectors": 1000000},
  "constraints": {
    "latency_ms": 500,
    "cost_$/month": 100
  }
}
```

### Output Contract
```json
{
  "chunking_strategy": {
    "method": "semantic|recursive|fixed_size",
    "chunk_size": 512,
    "overlap": 50,
    "preservation": "section_boundaries",
    "rationale": "Preserve semantic meaning; allow context overlap"
  },
  "embedding_selection": {
    "model": "text-embedding-3-large",
    "dimension": 1536,
    "fine_tuning": "no|yes",
    "cost_per_million_tokens": 2,
    "retrieval_metric": "cosine_similarity"
  },
  "vector_index": {
    "backend": "Pinecone|FAISS|Weaviate|Chroma",
    "scale": 1000000,
    "indexes": ["dense", "sparse"],
    "metadata_filters": ["date", "author", "domain"],
    "cost_$/month": 50
  },
  "retrieval_pipeline": {
    "step_1": "Sparse retrieval (BM25): top 100 candidates",
    "step_2": "Dense retrieval (embedding similarity): top 50 candidates",
    "step_3": "Reranking (cross-encoder): top 5 final results",
    "step_4": "Deduplication: remove overlapping chunks"
  },
  "context_assembly": {
    "merge_overlapping": true,
    "add_citations": true,
    "citation_format": "[source_doc:page:section]",
    "context_limit_tokens": 4000
  },
  "quality_metrics": {
    "retrieval_recall@10": 0.92,
    "reranking_mrr": 0.87,
    "citation_accuracy": 0.98,
    "latency_p99_ms": 350
  }
}
```

### RAG Workflow

**Step 1: Chunking**
```
Input: 1000 research papers (PDF)
→ Parse PDFs (preserve structure: sections, tables, equations)
→ Split by semantic boundaries (intro, methods, results, conclusion)
→ Overlap chunks 10% (maintain context)
→ Output: 50k chunks, 512 tokens each
```

**Step 2: Embedding**
```
Input: 50k chunks
→ Use OpenAI text-embedding-3-large (1536-dim)
→ Batch process (100 chunks at a time)
→ Store in Pinecone with metadata (doc_id, page, section)
→ Output: 50k embeddings
```

**Step 3: Retrieval**
```
Query: "What is the main finding in paper X about mechanism Y?"
→ BM25 (sparse): Find papers mentioning "mechanism Y" → 100 candidates
→ Dense (embedding): Find semantically similar to query → 50 candidates
→ Rerank (cross-encoder): Score top 5 by relevance → [paper_X_section3, ...]
→ Dedup: Remove overlapping chunks from same section
→ Final: Top 3 unique, relevant chunks with citations
```

**Step 4: Context Assembly**
```
Retrieved chunks:
- Paper X, section 3: "Finding A was..."
- Paper X, section 4: "This builds on finding A..."
- Paper Y, section 2: "Similar to finding A..."

Assembled context:
"Finding A was [citation: Paper X, section 3]. This mechanism builds on finding A [citation: Paper X, section 4] and is similar to findings in [citation: Paper Y, section 2]."
```

### Memory Tracking
```json
{
  "run_id": "2026-04-17_rag_001",
  "corpus": "100 research papers",
  "chunking": "semantic, 512 tokens, 10% overlap",
  "embedding_model": "text-embedding-3-large",
  "retrieval_strategy": "hybrid (BM25 + dense + rerank)",
  "quality": {
    "retrieval_recall@10": 0.92,
    "latency_ms": 350
  },
  "outcomes": "RAG system deployed; 92% of relevant docs in top 10",
  "next_time": "Semantic chunking outperforms fixed-size; keep this strategy"
}
```

---

## Agent 7: `df-deployment-architect`

### Purpose
Deploy models to production; handle real-world constraints: latency, scale, cost.

### Input Contract
```json
{
  "model": "path/to/model.pkl",
  "model_type": "sklearn|xgboost|tensorflow|onnx",
  "model_size_mb": 50,
  "inference_latency_baseline_ms": 15,
  "requirements": {
    "qps": 1000,
    "latency_p99_ms": 100,
    "availability": 0.999,
    "budget_$/month": 500,
    "update_frequency": "daily|weekly|monthly"
  },
  "constraints": {
    "interpretability": "required|preferred|not_required",
    "rollback_speed": "< 5 minutes"
  }
}
```

### Output Contract
```json
{
  "deployment_strategy": {
    "serving_type": "batch|online|streaming",
    "rationale": "Online serving required for real-time predictions"
  },
  "infrastructure": {
    "compute": "4 × GPU (NVIDIA A100)",
    "memory_gb": 64,
    "replicas": 4,
    "estimated_cost_$/month": 400
  },
  "optimization": {
    "quantization": "int8 (1MB, 0.5ms latency, < 0.1% accuracy loss)",
    "caching": "Redis (top 1k patterns cached, 99% hit rate)",
    "batching": "8 samples per batch = 4ms/batch = 2000 QPS",
    "result": "Latency 100ms, QPS 1000, cost $400/month"
  },
  "deployment_plan": {
    "containerization": "Docker image + K8s manifests",
    "rollout": "Canary (5% traffic, 1 hour) → Full (100% traffic)",
    "rollback": "Instant if error rate > 5% or latency > 200ms"
  },
  "monitoring": {
    "metrics": ["latency_p99", "error_rate", "feature_drift", "prediction_distribution"],
    "dashboards": ["inference_metrics", "resource_utilization", "cost_tracking"],
    "alerts": [
      "Latency p99 > 200ms → escalate",
      "Error rate > 5% → automatic rollback",
      "Feature drift detected → investigate"
    ]
  },
  "versioning": {
    "model_registry": "MLflow or custom",
    "version_tagging": "2026-04-17_v1_shadow, 2026-04-17_v1_canary, 2026-04-17_v1_prod",
    "experiment_tracking": "Log all metrics for comparison"
  }
}
```

### Deployment Patterns

**Pattern 1: Batch Inference (offline predictions)**
```
Use when: Predictions not time-sensitive
How: Spark job, daily batch, write to data warehouse
Cost: < $50/day
Example: Daily churn score for all users
```

**Pattern 2: Real-Time HTTP API (online)**
```
Use when: User-facing, low-latency required
How: FastAPI, containerized, Kubernetes
Cost: $200-1000/month depending on QPS
Example: Fraud detection during transaction
```

**Pattern 3: Streaming (online feature computation)**
```
Use when: Features needed in real-time
How: Kafka topics, stream processors, feature store
Cost: $500-5k/month depending on throughput
Example: Recommendation engine for e-commerce
```

### Optimization Strategies

**Latency Optimization:**
1. Quantization: int8 reduces model size + improves latency
2. Caching: Store predictions for top patterns
3. Batching: Process multiple samples at once
4. GPU: Faster matrix operations (if model supports)

**Cost Optimization:**
1. Spot instances: 70% discount, for non-critical workloads
2. Reserved instances: 30% discount, for baseline capacity
3. Auto-scaling: Scale up during peak, down during off-peak
4. Model compression: Smaller model = cheaper inference

### Memory Tracking
```json
{
  "run_id": "2026-04-17_deploy_001",
  "model": "LightGBM (fraud detection)",
  "deployment_strategy": "real-time HTTP API",
  "infrastructure": "4 GPUs, Kubernetes",
  "optimization": "int8 quantization + Redis caching",
  "results": {
    "latency_p99_ms": 95,
    "qps": 1200,
    "cost_$/month": 380,
    "uptime": 0.999
  },
  "rollout": "Canary 1h, then full rollout; automatic rollback enabled",
  "outcomes": "Production-ready; meets all SLOs",
  "next_time": "int8 quantization effective; use for future models"
}
```

---

## Agent 8: `df-decision-checkpoint` (System Coordinator)

### Purpose
Coordinate decision-making across the full pipeline; prevent anti-patterns; learn from failures.

### Input Contract
```json
{
  "stage": "requirements|data|features|modeling|evaluation|deployment|monitoring",
  "decisions_so_far": {...},
  "constraints": {...},
  "ask_for_validation": true
}
```

### Output Contract
```json
{
  "stage": "features",
  "decision": "Use target encoding for zip_code (3000 unique)",
  "validation": {
    "constraint_check": ["latency OK", "interpretability OK"],
    "anti_pattern_check": ["No hardcoded encodings (good)", "Feature documented (good)"],
    "recommendation": "Proceed to modeling",
    "warnings": []
  },
  "next_checkpoint": "Stage 4: Are constraints still respected in model selection?"
}
```

### Stage Gates

**Stage 1: Requirements Clarification**
```
Questions:
- What's the business objective? (Revenue? CTR? Cost savings?)
- Who uses the output? (Marketing? Finance? Operations?)
- What's success? (R² = 0.8? MAPE < 10%?)
- Constraints? (Latency, fairness, interpretability, cost?)
- Timeline? (2 weeks? 6 months?)

Checkpoint:
- Requirements clear and measurable? YES → proceed
- NO → ask clarifying questions; do not proceed to data
```

**Stage 2: Data Strategy**
```
Questions:
- Is data representative? (Training ≈ production?)
- Are labels reliable? (If user-generated, inter-rater agreement > 0.8?)
- Is there a data flywheel? (Will predictions improve future labels?)
- Data quality? (Missing < 20%? Duplicates < 0.1%?)

Checkpoint:
- Data quality sufficient? YES → proceed
- NO → data cleaning or collect new data
```

**Stage 3: Feature & Model Selection**
```
Questions:
- Baseline selected? (Ridge/Logistic/XGBoost?)
- Features documented? (What each feature is, why it exists?)
- Model respects constraints? (Latency, interpretability, fairness?)
- Feature engineering time spent? (Should be < 50% of total)

Checkpoint:
- Features ready? Model selected? YES → proceed
- NO → feature engineering or model selection
```

**Stage 4: Evaluation**
```
Questions:
- Offline metrics sufficient? (Or do we need online A/B test?)
- Fairness checked? (Disparate impact by subgroup?)
- Monitoring plan written? (What metrics to track? Thresholds?)
- Can we rollback? (Rollback procedure documented?)

Checkpoint:
- Evaluation complete? Monitoring plan ready? YES → deploy
- NO → do not deploy; address gaps
```

**Stage 5: Deployment & Monitoring (after going live)**
```
Questions:
- Is model degrading? (Track feature drift, prediction distribution)
- Any subgroup failures? (Fairness metrics per cohort?)
- Is the feedback loop working? (New data improving future training?)
- Has any hard alert triggered? (Auto-rollback if error rate > 5%)

Checkpoint:
- All metrics normal? YES → continue
- NO → investigate, possibly rollback
```

### Anti-Pattern Detection (20+ patterns)

**Pattern 1: Model-First Bias**
```
Symptom: Spending 70% time on model, 10% on data, 10% on monitoring
Fix: Redirect to 20% requirements, 40% data, 20% features, 20% evaluation
```

**Pattern 2: Ignoring Label Quality**
```
Symptom: Assuming labels are ground truth without checking
Fix: Check inter-rater agreement; sample labels; use active learning
```

**Pattern 3: No Monitoring Plan**
```
Symptom: "We'll monitor after deployment"
Fix: Write monitoring plan BEFORE training starts
```

**Pattern 4: Train/Test Contamination**
```
Symptom: Data leakage in features or temporal ordering
Fix: Use temporal split for time series; stratified split for classification
```

**Pattern 5: No Baseline**
```
Symptom: Comparing Model A vs Model B without baseline
Fix: Use Ridge (regression) or Logistic (classification) as baseline
```

**Pattern 6: Ignoring Constraints**
```
Symptom: Optimizing accuracy without considering latency/cost
Fix: Model selection respects latency, budget, fairness constraints
```

**Pattern 7: One-Off Features**
```
Symptom: Hardcoded SQL, not reproducible at inference
Fix: Features stored in feature store or inference code
```

**Pattern 8: Ignoring Class Imbalance**
```
Symptom: Assuming accuracy is the right metric
Fix: Use precision/recall/F1; handle imbalance with class weights
```

**Pattern 9: No Offline/Online Alignment**
```
Symptom: Offline metrics great, online metrics poor
Fix: A/B test to validate offline findings; understand discrepancies
```

**Pattern 10: Forgetting Fairness**
```
Symptom: Optimizing for average, ignoring subgroups
Fix: Check performance by demographic group; adjust thresholds if needed
```

### Memory Tracking
```json
{
  "run_id": "2026-04-17_checkpoint_001",
  "stages_completed": ["requirements", "data", "features", "modeling", "evaluation"],
  "decisions_logged": [
    {"stage": "features", "decision": "target_encoding", "outcome": "accuracy +0.03"},
    {"stage": "modeling", "decision": "LightGBM", "outcome": "latency 15ms < 100ms target"}
  ],
  "anti_patterns_detected": 0,
  "next_run": "Started with baseline (Logistic); saved 2 hours vs starting with XGBoost"
}
```

---

## Integration & Workflow

### Pipeline Orchestration
```
User: "Analyze titanic dataset, predict Survived"
    ↓
df-decision-checkpoint: Ask clarifying questions
    ↓ (confirms: business metric is accuracy; constraints: < 100ms latency)
df-data-architect: Ingest titanic.csv
    ↓
df-quality-engineer: Quality checks (ingest stage)
    ↓
df-feature-architect: Engineer + select features
    ↓
df-modeler: Train models (baseline + challenger)
    ↓
df-model-interpreter: Explain, check fairness
    ↓
df-deployment-architect: Plan deployment
    ↓
df-decision-checkpoint: Validate all stages, log decisions
    ↓
Deploy to production
    ↓
df-decision-checkpoint: Monitor, learn, next run improves
```

### Memory & Learning
```
Run 1: Baseline (Logistic) takes 30 minutes
  → memory/decisions.json logs: "Started with Ridge; very quick"
  
Run 2: User: "Now analyze new dataset, same problem type"
  → df-decision-checkpoint loads memory
  → Suggests: "Last time Ridge was quick baseline; use it again"
  → Saves time; focuses on what's different (new data)
```

---

## Testing Strategy

### Unit Tests (per agent)
```
✓ Agent loads input correctly
✓ Agent produces correct output schema
✓ Agent handles edge cases (empty data, missing columns, etc.)
```

### Integration Tests (full pipeline)
```
✓ Data flows from df-data-architect to df-quality-engineer
✓ Features flow from df-feature-architect to df-modeler
✓ Model flows from df-modeler to df-deployment-architect
✓ Memory updates across agents
```

### End-to-End Tests
```
✓ Run full pipeline on titanic.csv
✓ Run full pipeline on different problem types (regression, classification)
✓ Run full pipeline twice; verify learning (second run faster)
```

---

## Implementation Timeline

**Week 1:**
- [ ] Create agent scaffolds (stub files)
- [ ] Define input/output contracts
- [ ] Build memory persistence layer

**Week 2:**
- [ ] Implement df-data-architect
- [ ] Implement df-quality-engineer
- [ ] Write integration tests

**Week 3:**
- [ ] Implement df-feature-architect
- [ ] Implement df-modeler
- [ ] Write integration tests

**Week 4:**
- [ ] Implement df-model-interpreter
- [ ] Implement df-deployment-architect
- [ ] Write integration tests

**Week 5:**
- [ ] Implement df-decision-checkpoint
- [ ] Full end-to-end testing
- [ ] Learning loop integration

---

