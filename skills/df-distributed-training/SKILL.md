---
name: df-distributed-training
description: Scale model training across multiple GPUs and machines. Design distributed training strategies, parallelize feature engineering, implement hyperparameter search at scale. Handle synchronization, gradient communication, and optimization for multi-GPU performance.
---

# Distributed Training

## Purpose

Efficiently train large models across multiple GPUs and machines. Parallelize feature engineering, hyperparameter tuning, and model training. Make intelligent decisions about distributed strategy (data parallelism vs model parallelism), batch sizes, communication patterns, and optimization techniques.

## When to Use This Skill

- **Large datasets** — GB+ data that doesn't fit in single GPU memory
- **Slow training** — Model takes >1 hour on single GPU
- **Massive hyperparameter search** — 100+ configurations to evaluate
- **Parallel feature engineering** — 100+ columns to compute independently
- **Time-critical training** — Need results in hours, not days
- **Production retraining** — Continuous learning at scale

## Key Responsibilities

### 1. Distributed Training Strategy

**Data Parallelism (most common):**
```
Each GPU gets different batch:
  GPU 0: Batch samples 0-999
  GPU 1: Batch samples 1000-1999
  GPU 2: Batch samples 2000-2999
  GPU 3: Batch samples 3000-3999

After training on own batch:
  Aggregate gradients → Average → Update weights
  All GPUs now have identical weights

Speedup: ~3.5x on 4 GPUs (not 4x due to communication overhead)
```

**When to use:** Standard approach, works for most models.

**Model Parallelism (advanced):**
```
Model too big to fit in single GPU memory (e.g., 100B parameters)

Each GPU handles different layers:
  GPU 0: Input → Embedding → Layer 1-2
  GPU 1: Layer 3-4
  GPU 2: Layer 5-6
  GPU 3: Layer 7 → Output

Data flows sequentially through GPUs (pipeline)

Speedup: ~2x on 4 GPUs (worse than data parallelism)
Complexity: High (requires code restructuring)
```

**When to use:** Only if model > GPU memory. Otherwise data parallelism is better.

**Hybrid Approach:**
```
Combine data parallelism (across machines) + model parallelism (across GPUs)

Example: 8 machines × 4 GPUs = 32 GPUs total
  Machines in parallel (data parallelism) → each machine uses model parallelism
  
Speedup: 4x from model parallelism × 6x from data parallelism = ~20x
Complexity: Very high (debugging difficult)
```

**Decision Tree:**
```
Model fits in single GPU memory?
  ├─ YES: Use data parallelism
  │       Training time acceptable?
  │       ├─ YES: Single GPU fine
  │       └─ NO: Data parallelism across multiple GPUs
  │
  └─ NO: Model too large
         ├─ Use model parallelism (complex)
         ├─ Or reduce model size + data parallelism
         └─ Or use mixed precision (16-bit floats)
```

### 2. Parallel Feature Engineering

**Column-wise Parallelization:**

Most feature engineering is embarrassingly parallel — compute each feature independently.

```
Features to compute: ['age_normalized', 'income_log', 'credit_score_scaled', ...]

Parallel approach:
  Worker 0: Compute age_normalized on all rows
  Worker 1: Compute income_log on all rows
  Worker 2: Compute credit_score_scaled on all rows
  Worker 3: Compute location_encoded on all rows
  (all in parallel)
  
Sequential approach (avoid):
  For each row:
    Compute age_normalized
    Compute income_log
    Compute credit_score_scaled
    ... (N rows × M features = N×M operations)

Speedup: ~M times (number of features)
```

**Implementation:**
```python
# Bad (sequential)
for feature in features:
    df[feature] = compute_feature(df, feature)

# Good (parallel)
results = parallel_map(
    compute_feature, 
    [(df, f) for f in features],
    num_workers=4
)
df_new = pd.concat(results, axis=1)
```

**When parallelization breaks:**
- ✓ Features independent → parallelize
- ✗ Feature A depends on Feature B → can't parallelize
- Solution: Topological sort (compute B first, then A)

### 3. Parallel Hyperparameter Search

**Grid Search (exhaustive, slow):**
```
Parameters: 
  learning_rate: [0.001, 0.01, 0.1]
  batch_size: [32, 64, 128]
  dropout: [0.2, 0.5, 0.8]

Total combinations: 3 × 3 × 3 = 27
Training time per model: 1 hour
Total time (sequential): 27 hours
```

**Parallel Grid Search:**
```
Same 27 combinations, but train in parallel (4 workers):
  Worker 0: Train models 0, 4, 8, ...
  Worker 1: Train models 1, 5, 9, ...
  Worker 2: Train models 2, 6, 10, ...
  Worker 3: Train models 3, 7, 11, ...

Total time: 27 hours / 4 workers = ~7 hours (minus communication)
Speedup: ~3.5x (not 4x due to overhead)
```

**Bayesian Optimization (smarter, fewer trials):**
```
Don't try all 27 combinations. Use machine learning to guess good ones.

Iteration 1: Try random configs (5 configs)
  Best: learning_rate=0.01, batch_size=64, dropout=0.5

Iteration 2: Bayes optimizer suggests configs near best
  Try 5 more around that area
  
Iteration 3-5: Refine further

Total configs tried: 25 (vs 27 in grid search)
But much faster convergence — find best config in 5 iterations vs 27
```

**Tool Comparison:**

| Tool | Method | Best For |
|------|--------|----------|
| **Scikit-Optimize** | Bayesian | Small hyperparameter spaces (< 10 params) |
| **Optuna** | Tree-based + Bayesian | Large spaces, pruning bad trials early |
| **Ray Tune** | Population-based | Massive parallel (100+ workers) |
| **Hyperband** | Multi-fidelity | When you have cheap estimates (learning curves) |

**Hyperband Example:**
```
Allocate budget to promising configs:

Round 1: Train 81 configs for 1 epoch
  Keep top 27

Round 2: Train 27 configs for 3 epochs
  Keep top 9

Round 3: Train 9 configs for 9 epochs
  Keep top 3

Round 4: Train 3 configs for 27 epochs
  Winner!

Total epochs: 81×1 + 27×3 + 9×9 + 3×27 = 243
(vs 81×27 = 2187 for training all to end)
9x faster!
```

### 4. Multi-GPU Synchronization

**Synchronous Updates (common):**
```
All GPUs train on their batch:
  GPU0: gradient = backprop(batch0)
  GPU1: gradient = backprop(batch1)
  GPU2: gradient = backprop(batch2)
  GPU3: gradient = backprop(batch3)

All GPUs wait:
  BARRIER: Wait until all 4 complete

Average gradients:
  avg_gradient = (g0 + g1 + g2 + g3) / 4

Update weights:
  weights = weights - learning_rate * avg_gradient

All GPUs have identical weights
```

**Asynchronous Updates (faster, less stable):**
```
No waiting/barrier:
  GPU0 updates immediately with g0
  GPU1 updates immediately with g1
  GPU2 updates immediately with g2
  GPU3 updates immediately with g3

Weights may be stale (GPU3 uses old weights from GPU0)
Faster: no waiting
Less stable: can diverge

Use only if: training is very stable (high learning rate tolerance)
```

**Recommendation:** Synchronous (standard) unless you need every % speedup.

### 5. Batch Size & Gradient Accumulation

**Scaling Batch Size with GPUs:**

```
Single GPU:
  Batch size: 32
  GPU memory: 8GB
  Training time: 1000 iterations

4 GPUs (data parallelism):
  Total batch size: 32 × 4 = 128
  Per-GPU batch: 32
  GPU memory: 8GB (same)
  Training time: 1000 / 4 = 250 iterations

Effective batch size increased 4x, iterations reduced 4x
```

**Gradient Accumulation (when batch too small):**

```
Scenario: Need batch size 512, but 4 GPUs × 32 = 128

Solution:
  Accumulate gradients over 4 forward/backward passes
  
  Step 1: loss = forward(batch 128) + backward() [no update]
  Step 2: loss += forward(batch 128) + backward() [no update]
  Step 3: loss += forward(batch 128) + backward() [no update]
  Step 4: loss += forward(batch 128) + backward() + UPDATE
  
  Effective batch size: 128 × 4 = 512
  Cost: 4x more iterations, but weight updates only every 4 steps
```

### 6. Communication Optimization

**Gradient Compression (for slow networks):**
```
Standard: Send all gradients (128MB per iteration)
Slow on 1Gbps network: 1 second per iteration (wasteful)

Solution: Compress gradients
  Option 1: 16-bit floats instead of 32-bit → 2x smaller
  Option 2: Quantization (round to nearest 8-bit value) → 4x smaller
  Option 3: Only send top 1% gradients → 100x smaller (risky)

Trade-off: Compression reduces communication, but may hurt accuracy
```

**Ring AllReduce (efficient gradient averaging):**
```
Standard approach: Master → Collect all gradients → Average → Broadcast
Problem: Master becomes bottleneck

Ring AllReduce:
  GPU0 → GPU1 → GPU2 → GPU3 → GPU0 (circular)
  Each GPU sends/receives with one neighbor
  
Bandwidth: N-1 hops per GPU (vs 2 hops in broadcast)
Much better for 8+ GPUs
```

## Decision Scenarios

### Scenario 1: "Training takes 24 hours on single GPU. How do we speed up?"

**Analysis:**
```
Current: 24 hours on 1 GPU
Goal: Finish in <4 hours

Options:
1. Use 8 GPUs with data parallelism
   Expected speedup: ~7x (accounting for overhead)
   Time: 24 / 7 ≈ 3.5 hours ✓

2. Use mixed precision (float16)
   Expected speedup: ~1.5-2x
   Time: 24 / 2 ≈ 12 hours (not enough)

3. Reduce model size (fewer parameters)
   Expected speedup: depends on model
   Time: varies (may hurt accuracy)

4. Increase batch size (if GPU memory allows)
   Expected speedup: depends on current batch
   Time: varies

RECOMMENDATION: Combination of 1 + 2 + 4
- Use 8 GPUs (7x faster)
- Add mixed precision (1.5x faster)
- Increase batch size from 32 → 128 (1.5x faster)
- Total: 7 × 1.5 × 1.5 ≈ 15x speedup
- Time: 24 / 15 ≈ 1.5 hours ✓✓
```

### Scenario 2: "Hyperparameter tuning takes too long (100+ configs × 1 hour each = 100 hours)"

**Analysis:**
```
Current: 100 configs × 1 hour = 100 hours
Goal: Finish in < 10 hours

Option 1: Parallel grid search (10 workers)
  100 configs / 10 workers = 10 configs per worker
  10 configs × 1 hour = 10 hours per worker
  Parallel: 10 hours ✓

Option 2: Bayesian optimization
  Only try 30 promising configs (not all 100)
  30 × 1 hour = 30 hours
  With 3 workers: 10 hours ✓

Option 3: Hyperband (multi-fidelity)
  Train all 100 configs for 10% epochs → keep top 30
  Train 30 configs for 40% epochs → keep top 10
  Train 10 configs for 100% epochs → find best
  Total: 100×0.1 + 30×0.4 + 10×1 = 10 + 12 + 10 = 32 config-hours
  With 3 workers: 32 / 3 ≈ 11 hours (close)

RECOMMENDATION: Bayesian + parallel (Option 2)
- Use Optuna (smart selection)
- Parallelize with 10 workers
- Time: ~3-5 hours ✓✓ (much better)
```

## Anti-Patterns

❌ **Anti-pattern 1:** "Just add more GPUs, no optimization"
- Problem: Speedup plateaus at 4-8 GPUs (communication overhead)
- Solution: Optimize batch size, gradient compression, ring AllReduce

❌ **Anti-pattern 2:** "Synchronous updates always better"
- Problem: Slower due to waiting for slowest GPU
- Solution: For 8+ GPUs, consider asynchronous (if training stable)

❌ **Anti-pattern 3:** "Grid search on all 100 hyperparameter combinations"
- Problem: Takes forever (100+ hours)
- Solution: Bayesian optimization (30 configs) or Hyperband (10 hours)

❌ **Anti-pattern 4:** "Sequential feature engineering"
- Problem: Features compute one at a time (N×M operations)
- Solution: Parallelize independent features (~M times faster)

❌ **Anti-pattern 5:** "No batch size scaling when adding GPUs"
- Problem: Learning instability (effective batch size doesn't scale)
- Solution: Scale batch size linearly (batch_size *= num_gpus)

## Memory Tracking

```json
{
  "training_decision": "distributed_strategy",
  "strategy": "data_parallelism",
  "num_gpus": 8,
  "expected_speedup": 7.0,
  "batch_size_per_gpu": 32,
  "total_batch_size": 256,
  "gradient_compression": false,
  "synchronous_updates": true,
  "hyperparameter_search": "bayesian_optimization",
  "num_configs_to_try": 30,
  "implementation_date": "2026-04-17",
  "review_date": "2026-05-01"
}
```

## Implementation Checklist

- [ ] Check if model + data fit in single GPU memory
- [ ] Choose distribution strategy (data parallelism recommended)
- [ ] Set up distributed training framework (PyTorch DDP, TensorFlow Mirrored)
- [ ] Parallelize feature engineering (column-wise)
- [ ] Scale batch size with number of GPUs (careful with learning rate)
- [ ] Add gradient accumulation if needed (for large batch sizes)
- [ ] Implement Bayesian hyperparameter search (not grid search)
- [ ] Monitor communication overhead (all-reduce timing)
- [ ] Test scaling: 2 GPUs → 4 GPUs → 8 GPUs (check speedup curves)
- [ ] Implement mixed precision (float16) for 1.5-2x speedup

