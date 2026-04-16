---
name: df-llm-orchestrator
description: Orchestrate LLM-based systems end-to-end. Select models, implement caching strategies, evaluate quality, enforce guardrails, and route requests intelligently. Handles model selection, prompt optimization, evaluation metrics, safety constraints, cost management, and feedback loops for continuous improvement.
---

# LLM Orchestrator

## Purpose

Design and manage LLM-based systems at scale. Make intelligent decisions about model selection, caching, evaluation, routing, and safety constraints. Optimize for latency, cost, and quality while maintaining production reliability.

## When to Use This Skill

- **LLM system design** — Choosing models, architecture patterns, infrastructure
- **Prompt optimization** — Caching strategies, prompt engineering, context management
- **Quality evaluation** — Metrics, benchmarking, comparing LLM outputs
- **Safety & guardrails** — Output constraints, content filtering, jailbreak prevention
- **Multi-model routing** — Route requests to best model (cost/latency/quality tradeoff)
- **Feedback loops** — Collect user feedback, improve system performance over time
- **Cost optimization** — Caching, batching, quantization, model selection

## Key Responsibilities

### 1. Model Selection & Routing

**When to choose which model:**

| Use Case | Model | Rationale |
|----------|-------|-----------|
| Simple Q&A, classification | gpt-3.5-turbo (or equivalent) | Fast, cheap, sufficient for structured tasks |
| Complex reasoning, long context | gpt-4 (or Claude 3 Opus) | Better reasoning, 100K+ token context |
| Real-time inference, low latency | Smaller open model (Llama 2, Mistral) | Self-hosted, sub-100ms latency |
| Cost-critical, high volume | Smaller open model + fine-tuning | Train on your domain data |
| Retrieval-augmented generation | Any LLM + retriever | Document grounding, citation accuracy |

**Smart Routing Logic:**
```
Query arrives
  ├─ Is it structured task (Q&A, classification)?
  │   └─ Route to gpt-3.5-turbo (fast, cheap)
  ├─ Does it need reasoning (multi-step, planning)?
  │   └─ Route to gpt-4 (better reasoning)
  ├─ Does it require custom domain knowledge?
  │   └─ Route to fine-tuned model (lowest hallucination)
  └─ Is latency critical (< 100ms)?
      └─ Route to smaller model (self-hosted)
```

### 2. Prompt Caching & Optimization

**Caching Strategy:**

```json
{
  "system_prompt": "You are a data science expert...",
  "cache_seconds": 3600,
  "cache_cost_reduction": "90%"
}
```

**When to cache:**
- ✓ System prompt (stable across requests) — 90% cost reduction
- ✓ Large context documents (retriever results) — 80% reduction
- ✓ Few-shot examples (same task, different inputs) — 70% reduction
- ✗ User query (unique per request) — Don't cache

**Example:** RAG system with cached retrieval results:
```
Retriever fetches 10 documents (1000 tokens) → Cache this
For each query (50 tokens) → New request, reuses cached context
Cost: 1000 tokens once + 50 tokens × N queries (vs 1050 × N without cache)
```

### 3. Quality Evaluation & Metrics

**Standard Metrics:**

| Metric | Formula | When to Use |
|--------|---------|------------|
| **Exact Match** | % of outputs exactly matching gold | Classification, Q&A with single answer |
| **BLEU Score** | Word overlap (4-gram precision) | Machine translation, text generation |
| **ROUGE-L** | Longest common subsequence F1 | Summarization, paragraph generation |
| **Semantic Similarity** | Cosine distance (embeddings) | Open-ended responses, paraphrase detection |
| **Citation Accuracy** | % of citations pointing to correct source | RAG systems (critical for trustworthiness) |

**Evaluation Workflow:**
1. Create gold standard dataset (100-500 examples)
2. Run model on all examples
3. Calculate metrics
4. Compare against baseline (previous model, simple heuristic)
5. Log results with timestamp + model version

**Anti-pattern:** Only checking accuracy. Check:
- ✓ Latency (p50, p95, p99)
- ✓ Cost per request
- ✓ Hallucination rate (make-up facts?)
- ✓ Fairness (bias in outputs?)
- ✓ Safety (can it be jailbroken?)

### 4. Guardrails & Safety

**Input Validation:**
```json
{
  "max_tokens": 32768,
  "input_filters": [
    "detect_sql_injection",
    "detect_prompt_injection",
    "detect_personal_data"
  ],
  "block_if_detected": true
}
```

**Output Validation:**
```json
{
  "constraints": [
    "no_misinformation",
    "no_hate_speech",
    "no_personal_data_disclosure",
    "citations_required_for_factual_claims"
  ],
  "enforce_via": "post_processing_filter"
}
```

**Implementation Options:**
1. **Prompt engineering** — Tell model to follow rules (fragile, often bypassed)
2. **Beam search constraints** — Block certain tokens during generation (rigid)
3. **Output filtering** — Check output after generation (flexible, catches failures)

**Recommendation:** Combine all three for defense-in-depth.

### 5. Cost Management

**Cost Breakdown Example (per 1M tokens):**

| Model | Input Cost | Output Cost | Total |
|-------|-----------|-----------|-------|
| gpt-3.5-turbo | $0.50 | $1.50 | $2.00 |
| gpt-4 | $30 | $60 | $90 |
| Claude 3 Opus | $15 | $75 | $90 |
| Open (self-hosted) | $10 (GPU) | $10 (GPU) | $20 |

**Cost Optimization Strategies:**

1. **Caching** — Reuse expensive context (90% reduction)
2. **Batching** — Process multiple requests per call
3. **Model downgrade** — Use cheaper model when sufficient
4. **Prompt compression** — Shorter prompts = fewer tokens
5. **Token budgets** — max_tokens < natural length

**Example:** RAG system cost calculation:
```
Retriever: 100 calls × 5 docs × 200 tokens = 100K tokens
LLM call: 100 queries × (cache_hit) + 5K context = 15K new tokens
Cost: $0.50 (retriever) + $0.50 (LLM) = $1.00 per 100 queries
```

### 6. Feedback Loops & Improvement

**Collect Feedback:**
```json
{
  "response_id": "uuid",
  "model": "gpt-4",
  "user_feedback": {
    "rating": 5,
    "comment": "Exactly what I needed",
    "flagged_issues": ["hallucination", "irrelevant"]
  },
  "timestamp": "2026-04-17T10:30:00Z"
}
```

**Use Feedback to Improve:**
1. **Identify failure patterns** — High ratings vs low ratings (what works?)
2. **Retrain/fine-tune** — Collect bad examples, create new training data
3. **Update prompts** — A/B test new system prompts
4. **Route differently** — If model A fails 20% of time, reduce its weight

**Anti-pattern:** Collecting feedback but not using it. Action items:
- ✓ Log every feedback (why did user mark as bad?)
- ✓ Weekly review of low-rated outputs
- ✓ Iterate: new prompt → A/B test → measure improvement

## Decision Scenarios

### Scenario 1: "Which model should we use for our chatbot?"

**Constraints:**
- 1M queries/month
- Sub-500ms latency required
- $5K/month budget
- Domain-specific knowledge important

**Decision Tree:**
```
Budget = $5K/month?
  ├─ If fine-tuned open model: $2K (self-host) + $1K (compute) + $1K (fine-tuning) = $4K ✓
  ├─ If gpt-3.5-turbo: $2K (tokens) + $500 (API overhead) = $2.5K ✓
  ├─ If gpt-4: $15K (way over budget) ✗

Latency = 500ms?
  ├─ Fine-tuned (self-hosted): ~200ms ✓
  ├─ gpt-3.5-turbo: ~800ms ✗
  ├─ gpt-4: ~1200ms ✗

Domain knowledge?
  ├─ Fine-tuned: Excellent (trained on your data) ✓✓
  ├─ gpt-3.5-turbo: Good (general knowledge) ✓
  ├─ gpt-4: Excellent (deep reasoning) ✓

RECOMMENDATION: Fine-tune smaller model (e.g., Mistral) on your domain data.
- Cost: $4K/month ✓
- Latency: ~200ms ✓
- Quality: Domain-specific ✓
```

### Scenario 2: "We're paying $50K/month for LLM API calls. How do we reduce costs?"

**Analysis:**
```
Current: 10M tokens/month @ $5/1M = $50K

Quick wins (30 min implementation):
1. Add caching for system prompts (3K tokens, used 100K times)
   Savings: $0.30 (tiny, but easy)
2. Compress prompts (remove redundant text)
   Savings: 20% × $50K = $10K
3. Downgrade easy queries to gpt-3.5-turbo
   Savings: 30% of queries × 50% cheaper = 15% = $7.5K

Medium-term (1 month):
4. Fine-tune model on your domain → use 10× cheaper model
   Savings: $30K (massive, but requires data preparation)

Total potential: $47.5K/month savings (95% reduction)
```

### Scenario 3: "Our LLM output is hallucinating facts. How do we fix it?"

**Root Cause Analysis:**
- Is it prompt issue? (poor instruction)
- Is it model issue? (inherent to model capability)
- Is it data issue? (wrong context in retriever)
- Is it feedback loop issue? (no correction mechanism)

**Solution by Cause:**

| Cause | Fix | Effort |
|-------|-----|--------|
| Prompt too vague | Detailed system prompt + few-shot examples | 1 day |
| Model limitation | Switch to more capable model | 1 hour |
| Retriever failing | Improve embedding model or reranker | 3 days |
| No feedback loop | Add citation requirement + human review | 1 week |

**Implementation:**
```
Add this to output validation:
- Every factual claim MUST have citation
- If citation not available, say "I don't know"
- Log all "I don't know" responses
- Weekly review: update knowledge base from these gaps
```

## Anti-Patterns

❌ **Anti-pattern 1:** "Use the biggest model for everything"
- Problem: High cost, unnecessary for simple tasks
- Solution: Route by task complexity (gpt-3.5-turbo for Q&A, gpt-4 for reasoning)

❌ **Anti-pattern 2:** "Evaluate only accuracy"
- Problem: Miss latency/cost/fairness issues
- Solution: Track all metrics (accuracy, latency p99, cost, hallucination rate)

❌ **Anti-pattern 3:** "Cache system prompt but not context"
- Problem: Minimal cost savings (system prompt is small)
- Solution: Cache retriever results (much larger, greater savings)

❌ **Anti-pattern 4:** "Collect feedback but never act on it"
- Problem: Feedback loop broken, no improvement
- Solution: Weekly review of low-rated outputs, update prompts

❌ **Anti-pattern 5:** "No guardrails, hope output is safe"
- Problem: Hallucinations, jailbreaks, data leaks
- Solution: Multi-layer: prompt constraints + output filtering + human review

## Memory Tracking

```json
{
  "decision": "chosen_model",
  "model_selected": "gpt-4",
  "rationale": "Complex reasoning required; accuracy > cost",
  "constraints_checked": ["latency", "budget", "quality"],
  "evaluated_alternatives": ["gpt-3.5-turbo", "claude-3-sonnet"],
  "performance_metrics": {
    "accuracy": 0.95,
    "latency_p99_ms": 1200,
    "cost_per_query": 0.05
  },
  "decision_date": "2026-04-17",
  "review_date": "2026-05-01"
}
```

## Implementation Checklist

- [ ] Document all models under consideration (capability, cost, latency)
- [ ] Run benchmark on gold standard dataset (accuracy, latency, cost)
- [ ] Implement caching (system prompt + context)
- [ ] Add guardrails (prompt constraints + output filtering)
- [ ] Set up feedback loop (collect ratings + comments)
- [ ] Monitor costs (weekly breakdown by model/query-type)
- [ ] Plan quarterly review (update based on feedback + new models)

