---
title: DataForge Expert Consolidation — 72 Skills → 8 Powerhouse Agents
date: 2026-04-17
methodology: Expert-driven synthesis without API calls; combining best practices from 72 downloaded skills
---

# DataForge Expert Consolidation
## Transforming 72 Skills into 8 Consolidated, Production-Grade Agents

> This document consolidates learnings from 72 analyzed skills into an expert-designed agent architecture for DataForge. We combine best practices, eliminate redundancy, and create composable agents that leverage the full ecosystem.

---

## Executive Summary

### What We're Consolidating

**Domains Covered:**
- 16 SEO Skills → (Out of scope for DataForge)
- 12 RAG/LLM Skills → 1 `df-rag-orchestrator` agent
- 15 ML/Modeling Skills → 2 agents: `df-modeler` + `df-model-interpreter`
- 18 Data Engineering/Processing Skills → 2 agents: `df-data-architect` + `df-quality-engineer`
- 11 MLOps/Deployment Skills → 1 agent: `df-deployment-architect`

**Key Principle:** Rather than skill-by-skill agents, we build **domain-expert agents** that:
1. **Combine overlapping expertise** (3-5 skills per agent)
2. **Specialize in decision-making** (not just execution)
3. **Handle constraints and tradeoffs** (real-world constraints)
4. **Learn from prior runs** (memory-based iteration)
5. **Validate at each stage** (quality gates, not just at end)

---

## Part 1: The 8 Consolidated Agents

### Agent 1: `df-data-architect` 
**Consolidates:** data-pipeline-engineer, data-ingestion-multi-source, etl-pipeline-design, large-scale-data-processing, data-quality-checks

**Purpose:** Own the data lifecycle — from raw data to production-ready features.

**Key Responsibilities:**
- **Source Assessment** — Evaluate: data formats, volumes, freshness, schema stability
- **Architecture Selection** — Choose: batch vs stream vs hybrid; storage layer design
- **Ingestion Strategy** — Parallel processing, incremental updates, error recovery
- **Schema Contracts** — Enforce: versioning, backward compatibility, column-level validation
- **Lineage Tracking** — Log: which transforms, which inputs/outputs, decisions rationale
- **Incremental Processing** — Never recompute; track state via `memory/transform_state.json`

**Expert Decisions:**
```
Scenario: New data arrives (50GB monthly)
df-data-architect decides:
  - Batch vs stream? (monthly update → batch)
  - Full refresh vs incremental? (schema stable → incremental)
  - Storage format? (Parquet for ML; CSV for reporting)
  - Compression? (Yes; 10GB → 2GB)
  - Partitioning strategy? (By date, by domain)
  - Retry logic? (3 retries; exponential backoff)
  - Archival? (Keep raw data for 2 years)
```

**Anti-Patterns to Prevent:**
1. ❌ Full dataset refreshes every run → ✅ Incremental with change detection
2. ❌ Coupled to source schema → ✅ Explicit contracts + version management
3. ❌ Quality checks only at end → ✅ Gates at EVERY layer (ingest → profile → transform)
4. ❌ Delete raw data → ✅ Archive for reproducibility
5. ❌ Hardcoded dates/logic → ✅ Dynamic templating + config-driven

---

### Agent 2: `df-quality-engineer`
**Consolidates:** data-quality-checks, data-drift-detection, monitoring-ml, online-offline-consistency

**Purpose:** Ensure data quality at every stage; detect degradation before it becomes a problem.

**Key Responsibilities:**
- **Ingest Quality** — Missing values, duplicates, schema violations, outliers
- **Transform Quality** — After each major transform, validate output contracts
- **Drift Detection** — Monitor: distribution shifts, concept drift, missing values trend
- **Consistency Checks** — Train/test alignment, online/offline alignment, label quality
- **Quality Reports** — Produce dashboards and alerts (hard blocks vs soft warnings)
- **Recovery Triggers** — When quality check fails, recommend: fix data, roll back transform, investigate

**Expert Decisions:**
```
Scenario: 20% missing values in a feature
df-quality-engineer decides:
  - Is it acceptable? (If feature importance < 0.02, yes; otherwise no)
  - How to handle? (If < 5%: drop rows; 5-30%: impute; >30%: remove feature)
  - Imputation method? (Mean for numeric, mode for categorical; if skewed → median)
  - Validate choice? (Compare model metrics before/after; if < 2% drop, accept)
```

**Quality Gate Structure:**
```
{
  "stage": "preprocess",
  "checks": {
    "hard_blocks": [
      "schema_match: FAIL → stop",
      "no_nulls_in_id_column: FAIL → stop"
    ],
    "soft_warnings": [
      "class_imbalance: 95:5 → continue but flag",
      "high_cardinality: 50k unique values → warn, may need grouping"
    ]
  }
}
```

---

### Agent 3: `df-feature-architect`
**Consolidates:** feature-engineering, feature-importance-analysis, feature-store-design, ml-pipeline

**Purpose:** Transform raw features into predictive power; design reusable feature infrastructure.

**Key Responsibilities:**
- **Domain Feature Engineering** — Create domain-specific features (date features, business logic)
- **Scaling & Encoding** — Normalize, standardize, one-hot/target encode; choose per data distribution
- **Feature Selection** — RFE, permutation importance, SHAP-based; avoid overfitting
- **Feature Store Design** — Versioning, online/offline alignment, feature lineage
- **Feature Documentation** — What each feature is, why it exists, when to recompute
- **Interaction Features** — When beneficial; avoid combinatorial explosion

**Expert Decisions:**
```
Scenario: Predicting house price with 500 raw features
df-feature-architect:
1. Domain features: (sale_year - built_year) = age, (bedrooms/total_rooms) = ratio
2. Encode: zip_code (3k unique) → target encode; color (5 categories) → one-hot
3. Scaling: numeric → StandardScaler (for ridge/lasso); keep raw for trees
4. Selection: Remove features with corr > 0.95 (redundant); remove < 0.01 importance
5. Interactions: Test (age × location) and (rooms × area) only if base features fail
6. Result: 500 → 50 features; 15% accuracy gain
```

**Anti-Patterns:**
1. ❌ Use all features → ✅ Select with importance metrics
2. ❌ Hardcode encoding → ✅ Parameterize; store encoders for deployment
3. ❌ Scale after train/test split → ✅ Fit scaler on train; apply to test
4. ❌ Forget to scale for deployment → ✅ Save scaler; load at inference time

---

### Agent 4: `df-modeler`
**Consolidates:** ml-system-design-interview, model-selection, offline-vs-online-evaluation, experiment-tracking-advanced

**Purpose:** Select, train, and tune models that respect business constraints and data realities.

**Key Responsibilities:**
- **Baseline Selection** — Ridge/Logistic/XGBoost based on problem type + data size
- **Model Selection** — Tree vs linear vs deep learning; ensemble vs single
- **Constraint Handling** — Latency, budget, fairness, interpretability; model choice respects these
- **Hyperparameter Tuning** — Bayesian, grid search, early stopping; no guessing
- **Train/Test Alignment** — Time series: temporal split; classification: stratified; no leakage
- **Experiment Tracking** — Log: hyperparams, metrics, dataset version, runtime, reproducibility

**Expert Decisions:**
```
Scenario: Fraud detection on 10M transactions
df-modeler decides:
1. Constraint: Real-time (< 100ms), XAI required, False negative cost >> false positive
2. Baseline: Logistic Regression (fast, interpretable, good baseline)
3. Challenger: LightGBM (faster than XGBoost, good for imbalanced data)
4. Handling imbalance: Class weights; not SMOTE (time series data leaks)
5. Tuning: Bayesian with 50 trials; optimize for precision (control false positives)
6. Evaluation: Offline (precision, recall, F1); online (A/B test on 10% traffic)
7. Deployment: LightGBM (15ms latency) beats any deep learning option
```

**Key Principle:** **Design for monitoring, not just training.**
- Train on past 90 days
- Validate on most recent 7 days
- Plan drift monitoring before training starts
- Build fallback to baseline

---

### Agent 5: `df-model-interpreter`
**Consolidates:** model-interpretability-lime, model-interpretability-shap, feature-importance-analysis, llm-evaluation

**Purpose:** Explain what your model learned and why it makes its predictions.

**Key Responsibilities:**
- **Feature Importance** — Global (SHAP, permutation) and local (LIME, SHAP force plots)
- **Fairness Analysis** — Disparate impact, calibration by subgroup, threshold tuning
- **Error Analysis** — When model fails, what patterns emerge? How to fix?
- **Model Comparison** — Which model learned better? On what data splits?
- **Debug Reports** — Actionable findings for stakeholders (non-technical + technical)
- **Production Monitoring** — Track top features, fairness metrics, calibration over time

**Expert Decisions:**
```
Scenario: Model predicts 80% accuracy, but 2% accuracy on minority group
df-model-interpreter:
1. SHAP analysis: Feature X (protected attribute proxy) has high importance
2. Fairness check: 95% accuracy for majority, 60% for minority
3. Root cause: Training data 10:1 imbalance; model optimizes for majority
4. Solution: Rebalance with class weights; retrain; check fairness metrics
5. Production check: Monitor prediction distribution by subgroup; alert if disparity > 5%
```

**Interpretation Workflows:**
```
Workflow 1: Global Explanation
  - SHAP bar plot: top 10 features driving all predictions
  - Beeswarm plot: feature importance variance across samples
  - Output: "Model relies heavily on features X, Y, Z"

Workflow 2: Local Explanation (single prediction)
  - SHAP force plot: which features pushed this prediction up/down?
  - LIME: nearest neighbors showing what changed the prediction
  - Output: "Prediction = 0.75 because customer age (feature 5) pushed it +0.2"

Workflow 3: Fairness Analysis
  - Confusion matrix by subgroup
  - Calibration curve per subgroup
  - Threshold analysis: can we improve fairness without hurting accuracy?
```

---

### Agent 6: `df-rag-orchestrator`
**Consolidates:** rag-data-ingestion, rag-chunking-strategy, rag-embedding-selection, rag-vector-indexing, rag-retrieval-optimization, rag-context-ranking

**Purpose:** Build production RAG systems for semantic search, Q&A, and knowledge retrieval.

**Key Responsibilities:**
- **Document Ingestion** — Parse PDF, HTML, markdown, tables; preserve structure
- **Chunking Strategy** — Size (recursive splitting, semantic boundaries); overlap
- **Embedding Selection** — Model choice (dense vs sparse); fine-tune vs off-the-shelf
- **Vector Index Design** — FAISS, Pinecone, Weaviate; hybrid search (dense + sparse)
- **Retrieval Ranking** — BM25 + dense; rerank with cross-encoder; remove redundancy
- **Context Assembly** — Merge top-K chunks; add citations; maintain coherence

**Expert Decisions:**
```
Scenario: Build Q&A over 1000 research papers (100GB text)
df-rag-orchestrator:
1. Chunking: Split by paper section (not arbitrary 512-token chunks)
   - Preserves semantic boundaries: intro, methods, results, conclusion
   - Overlap: 100 tokens between chunks (preserve context)
2. Embedding: OpenAI text-embedding-3-large (1536-dim)
   - Dense retrieval; good for semantic matching
3. Index: Pinecone (serverless; handles 1B vectors)
   - Metadata filters: by date, by author, by domain
4. Retrieval: Hybrid search
   - BM25 (sparse): keywords + exact matches
   - Dense: semantic similarity (top 20 candidates)
   - Rerank: Cross-encoder (BAAI/bge-reranker-large) picks top 5
5. Context assembly: Merge overlapping chunks; add paper citations
6. Result: Accurate, attributed, traceable answers
```

**RAG Quality Metrics:**
```
- Retrieval recall@10: % of relevant documents in top 10
- Reranking MRR: Mean reciprocal rank of first relevant document
- Citation accuracy: % of claims properly attributed
- Latency: p99 < 500ms
```

---

### Agent 7: `df-deployment-architect`
**Consolidates:** deployment-ml, microservices-ml-architecture, high-scale-inference-design, batch-inference-pipeline, low-latency-system-design

**Purpose:** Deploy models to production; handle real-world constraints: latency, scale, cost.

**Key Responsibilities:**
- **Serving Choice** — Batch (offline) vs online (real-time); which is cost-effective?
- **Latency Optimization** — Model quantization, caching, GPU/CPU selection
- **Scale Design** — Load balancing, autoscaling, circuit breakers, graceful degradation
- **Cost Analysis** — CPU vs GPU; on-demand vs reserved; inference cost per prediction
- **Monitoring** — Drift, latency SLO, error rates, model versioning
- **Rollback Strategy** — A/B testing, canary deployments, instant rollback

**Expert Decisions:**
```
Scenario: Deploy fraud detection model; need < 50ms latency at 100k QPS
df-deployment-architect:
1. Model: LightGBM (15MB, 2ms inference); not deep learning
2. Quantization: ONNX + int8 (1MB, 0.5ms inference, < 0.1% accuracy loss)
3. Serving: FastAPI + 4 GPU nodes (each handles 25k QPS)
   - Async handling
   - Batch inference (8 samples/batch = 4ms per batch)
   - Result: 25k QPS per node × 4 nodes = 100k QPS
4. Caching: Redis (top 1k fraud patterns cached, 99% hit rate)
5. Cost: $400/month on GPU (vs $2k/month for larger model)
6. Monitoring: Prediction latency p99, feature drift, false positive rate
7. Rollback: Canary deployment (5% traffic) for 1 hour before full rollout
```

**Deployment Patterns:**
```
Pattern 1: Batch Inference (daily batch processing)
  - When: Predictions not time-sensitive
  - How: Spark job, write to data warehouse, accessible for reporting
  - Cost: < $50/day

Pattern 2: Real-Time HTTP API (online predictions)
  - When: User-facing, low-latency requirement
  - How: FastAPI, containerized, deployed on Kubernetes
  - Cost: $200-1000/month depending on QPS

Pattern 3: Streaming (online feature computation)
  - When: Features needed in real-time (fraud detection, recommendation)
  - How: Kafka topics, stream processors, feature store
  - Cost: $500-5k/month depending on throughput
```

---

### Agent 8: `df-decision-checkpoint` (System Coordinator)
**Consolidates:** ml-system-design-interview, offline-vs-online-evaluation, feedback-loop-learning, decision-tracking-system

**Purpose:** Coordinate decision-making across the full pipeline; prevent anti-patterns; learn from failures.

**Key Responsibilities:**
- **Stage Gate Reviews** — At each pipeline stage, ask: is this ready for the next stage?
- **Constraint Validation** — Do decisions respect latency, budget, fairness constraints?
- **Anti-Pattern Detection** — Warn about 20+ known pitfalls (model-first bias, no monitoring, etc.)
- **Decision Logging** — Why did we choose this model? This feature? This metric?
- **Learning Loop** — Failed approach? Log it; next run skips it or learns from it
- **Stakeholder Communication** — What are we building? Why? What could go wrong?

**Expert Decisions:**
```
Stage 1: Requirements (before data touches)
- Question: "What's the business metric?" (Revenue? CTR? Cost savings?)
- Question: "Who uses the output?" (Marketing? CS? Finance?)
- Question: "What's success?" (R² = 0.8? MAPE < 10%?)
- Question: "Constraints?" (Latency, fairness, interpretability, cost?)
- Checkpoint: If any unclear, STOP. No data exploration yet.

Stage 2: Data Strategy (before feature engineering)
- Review: Is data representative of production?
- Review: Are labels reliable? (If user-generated, check inter-rater agreement)
- Review: Is there a data flywheel? (Will predictions improve future labels?)
- Checkpoint: If data quality insufficient, pause modeling.

Stage 3: Feature & Model Selection (before training)
- Review: Have we selected baselines? (Ridge/Logistic/XGBoost)?
- Review: Are features documented? (What each feature means, why it exists?)
- Review: Does model selection respect constraints?
- Checkpoint: If feature engineering takes > 50% of time, you're over-engineering.

Stage 4: Evaluation (before deployment)
- Review: Offline metrics sufficient? (Or do we need online A/B test?)
- Review: Fairness checked? (Disparate impact by subgroup?)
- Review: Monitoring plan written? (What metrics to track? Alert thresholds?)
- Checkpoint: If no monitoring plan, do not deploy.

Stage 5: Deployment & Monitoring (after going live)
- Review: Is model degrading? (Track feature drift, prediction distribution)
- Review: Any subgroup failures? (Fairness metrics per cohort?)
- Review: Is the feedback loop working? (New data improving future training?)
- Checkpoint: If drift detected, automated rollback plan kicks in.
```

**Anti-Pattern Detection (20+ known pitfalls):**
```
1. ❌ Model-first bias → Spending 70% time on model, 10% on data, 10% on monitoring
   ✅ Redirect: Spend 20% requirements, 40% data, 20% features, 20% evaluation
   
2. ❌ Ignoring label quality → Assuming labels are ground truth
   ✅ Check: Inter-rater agreement, label noise, active learning to improve labels
   
3. ❌ No monitoring plan → "We'll monitor after deployment"
   ✅ Require: Monitoring design BEFORE training starts
   
4. ❌ Train/test contamination → Leakage in features or temporal ordering
   ✅ Check: Time series? Use temporal split. Classification? Stratified split.
   
5. ❌ No baseline → Comparing Model A vs Model B without baseline
   ✅ Require: Ridge (regression) or Logistic (classification) as baseline
   
6. ❌ Ignoring constraints → Optimizing accuracy without considering latency/cost
   ✅ Check: Model selection respects latency, budget, fairness constraints
   
7. ❌ One-off features → Hardcoded SQL, not reproducible at inference
   ✅ Require: Features stored in feature store or inference code
   
8. ❌ Imbalanced data, no handling → Assuming accuracy is the right metric
   ✅ Check: Class distribution; use precision/recall/F1, not accuracy
   
9. ❌ No offline/online alignment → Offline metrics great, online metrics poor
   ✅ Check: Does A/B test validate offline findings? If not, why?
   
10. ❌ Forgetting about fairness → Optimizing for average, ignoring subgroups
    ✅ Check: Performance by demographic group; adjust thresholds if disparate
```

---

## Part 2: Skill Consolidation Mapping

### Consolidated Skills Summary

| Original Skills (72) | Consolidated Agent | Count |
|-------|---------|-------|
| data-pipeline-engineer, data-ingestion-multi-source, etl-pipeline-design, large-scale-data-processing, data-quality-checks | `df-data-architect` | 5 |
| data-quality-checks, data-drift-detection, monitoring-ml, online-offline-consistency | `df-quality-engineer` | 4 |
| feature-engineering, feature-importance-analysis, feature-store-design, ml-pipeline | `df-feature-architect` | 4 |
| ml-system-design-interview, model-selection, offline-vs-online-evaluation, experiment-tracking-advanced | `df-modeler` | 4 |
| model-interpretability-lime, model-interpretability-shap, feature-importance-analysis, llm-evaluation | `df-model-interpreter` | 4 |
| rag-data-ingestion, rag-chunking-strategy, rag-embedding-selection, rag-vector-indexing, rag-retrieval-optimization | `df-rag-orchestrator` | 5 |
| deployment-ml, microservices-ml-architecture, high-scale-inference-design, batch-inference-pipeline, low-latency-system-design | `df-deployment-architect` | 5 |
| ml-system-design-interview, decision-tracking-system, feedback-loop-learning, offline-vs-online-evaluation | `df-decision-checkpoint` | 4 |
| **Remaining (specialist/out-of-scope)** | Reference docs | 26 |

**Remaining Skills (Reference Library, Not Agents):**
- SEO (16 skills) — Not core to DataForge
- LLM-specific (llm-caching-strategy, llm-routing-multi-model, llm-benchmarking, llm-guardrails) — Can be reference docs
- Infrastructure (ci-cd-ml, mcp-agent-orchestrator, mcp-skill-composer, mcp-skill-generator) — Can be integration points
- Domain-specific (clinical-diagnostic-reasoning, hipaa-compliance, etc.) — Trigger domain detection

---

## Part 3: Key Design Principles

### 1. Constraint-First Modeling
**Before training any model:**
- Latency: < 10ms? 100ms? 1s?
- Budget: $10/day? $1000/month?
- Fairness: Max 5% disparate impact allowed?
- Interpretability: Must stakeholders understand why?

Model selection respects these constraints, not just optimizes accuracy.

### 2. Quality Gates at Every Stage
Instead of one big validation at the end, validate after each major transform:
```
Raw Data → Quality Check 1
Ingested → Quality Check 2
Profiled → Quality Check 3
Features Selected → Quality Check 4
Models Trained → Quality Check 5
Deployed → Quality Check 6
```

### 3. Memory-Based Learning
Every run logs decisions and outcomes:
```
memory/decisions.json: {
  "feature_engineer_decision": "Used target encoding for category X",
  "outcome": "Accuracy improved from 0.82 to 0.85",
  "next_time": "Prioritize target encoding for this feature type"
}
```

Next run learns: "Last time target encoding worked best for this feature type; let's try it."

### 4. Baseline-First Iteration
Always start with:
- **Regression**: Ridge (simple, interpretable, fast baseline)
- **Classification**: Logistic Regression
- **Clustering**: K-Means

Only then try: XGBoost, neural networks, complex ensembles.

### 5. Monitoring as First-Class
Treat monitoring design as equal to model training:
```
Monitoring plan (created BEFORE training):
- Feature drift check: If feature distribution changes > 10%, alert
- Model drift check: If accuracy degrades > 2%, rollback
- Fairness check: If disparate impact > 5%, investigate
```

### 6. Anti-Pattern Prevention
Before each stage, check for known pitfalls:
- Stage 1: Are requirements clear? (not vague)
- Stage 2: Is data labeled correctly? (not noisy)
- Stage 3: Are features documented? (not arbitrary)
- Stage 4: Is monitoring planned? (not after-the-fact)
- Stage 5: Can we rollback? (not locked into production)

---

## Part 4: Implementation Roadmap

### Phase 1: Create Agent Scaffolds (2 days)
- [ ] Stub all 8 agents with basic structure
- [ ] Define input/output contracts (JSON schemas)
- [ ] Create memory persistence for each agent
- [ ] Write integration tests

### Phase 2: Implement Core Agents (1 week)
- [ ] `df-data-architect` — Full data pipeline + lineage
- [ ] `df-quality-engineer` — Quality gates + drift detection
- [ ] `df-feature-architect` — Feature engineering + selection
- [ ] `df-modeler` — Model training + tuning + evaluation

### Phase 3: Implement Interpretation & Deployment (1 week)
- [ ] `df-model-interpreter` — SHAP + fairness analysis
- [ ] `df-deployment-architect` — Serving strategy + scaling
- [ ] `df-decision-checkpoint` — Stage gating + anti-pattern detection

### Phase 4: RAG Integration (1 week)
- [ ] `df-rag-orchestrator` — Full RAG pipeline for technique library
- [ ] Integrate with reference docs (vectors for semantic search)
- [ ] Build learning loop (failed approaches → kb_gaps)

### Phase 5: Learning Loop (ongoing)
- [ ] Memory updates after each run
- [ ] Tracking decisions + outcomes
- [ ] Auto-trigger expert agents on novel situations
- [ ] Feedback loop from production monitoring

---

## Part 5: Reference Library (from 72 Skills)

### Technique Categories

1. **Data Processing** — Ingestion, validation, profiling, incremental updates
2. **Feature Engineering** — Scaling, encoding, selection, interaction detection
3. **Modeling** — Baseline selection, hyperparameter tuning, ensemble strategies
4. **Evaluation** — Metrics, fairness, calibration, error analysis
5. **Interpretation** — SHAP, LIME, feature importance, fairness analysis
6. **Deployment** — Serving strategy, latency optimization, monitoring
7. **RAG Systems** — Chunking, embedding, retrieval, reranking
8. **MLOps** — Experiment tracking, drift detection, rollback strategies

Each category has:
- **Core techniques** (always applicable)
- **Domain variants** (specific to problem type)
- **Failure modes** (what can go wrong)
- **Optimization strategies** (speed up without accuracy loss)

---

## Part 6: Conclusion

### From 72 Skills to 8 Agents

By consolidating 72 skills into 8 expert-driven agents, we:
1. **Reduce cognitive load** — 8 agents to coordinate, not 72 skills
2. **Enable specialization** — Each agent is deep expert in its domain
3. **Improve decision quality** — Multi-skill knowledge → better tradeoff handling
4. **Enable learning loops** — Memory-based iteration on prior decisions
5. **Scalability** — Adding new skills updates reference library, not agents

### Agent Synergies

```
User Input
    ↓
df-decision-checkpoint (ask clarifying questions, validate constraints)
    ↓
df-data-architect (load, validate, ingest data)
    ↓
df-quality-engineer (quality gates, drift detection)
    ↓
df-feature-architect (engineer, select, store features)
    ↓
df-modeler (train, tune, evaluate models)
    ↓
df-model-interpreter (explain, fairness check, error analysis)
    ↓
df-deployment-architect (serving, scaling, monitoring)
    ↓
df-decision-checkpoint (log decisions, trigger learning)
    ↓
Next run (learns from memory)
```

Each agent is independently testable, reusable, and improvable.

---

## References

**Analyzed Skills Repository:**
- GitHub: `curiositech/some_claude_skills`
- Total skills analyzed: 72
- Analysis method: Manual expert consolidation + pattern extraction
- Date: 2026-04-17

**Key Sources:**
- `data-pipeline-engineer/SKILL.md` — 5-stage pipeline patterns
- `ml-system-design-interview/SKILL.md` — 7-stage ML design framework
- `computer-vision-pipeline/SKILL.md` — Preprocessing + batching patterns
- Individual RAG skills — Consolidation strategy for `df-rag-orchestrator`
- Individual deployment skills — Serving patterns + optimization

