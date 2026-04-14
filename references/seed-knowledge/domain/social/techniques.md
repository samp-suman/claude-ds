---
area: social
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area social
status: seed
schema_version: 1.0
---

# Social Media / Social Network — Domain Knowledge

## Core techniques

### [soc-001] Engagement is non-IID
**Summary:** Posts, likes, follows are bursty and clustered. Random splits leak influence cascades. Split by time AND by user, depending on the prediction target.

### [soc-002] Network features
**Summary:** Beyond user-level features, compute graph features: PageRank, clustering coefficient, community membership (Louvain, Leiden), k-core. Use `networkx`, `graph-tool`, or `cugraph` for scale.

### [soc-003] Cold-start handling
**Summary:** New users have no history. Use content-based signals (bio, profile pic embedding, first 3 posts) plus look-alike modeling against established users.

### [soc-004] Cascade prediction
**Summary:** Predicting virality is hard - early signals (first-hour reactions, breadth of first sharers) dominate later content features. Use Hawkes processes for temporal modeling.

### [soc-005] Toxicity / moderation features
**Summary:** Perspective API scores, slur lexicons, embedding-based similarity to known violations. Always pair ML with rule-based safety nets and human review queues.

## Pitfalls

- Survivor bias: deleted accounts and removed posts are missing from training data.
- Echo chambers in labels: reviewer agreement is low on borderline content; use multi-rater labels and aggregate with Dawid-Skene.
- Privacy: user_id, IP, device fingerprint must be hashed; comply with GDPR / DSA / DSA Art 27.
- Adversarial drift: spammers and bad actors adapt - models age in days, not months.

## Recommended metrics

- **Engagement prediction**: NDCG, hit-rate@k, RIG (relative information gain) over baseline CTR.
- **Moderation**: PR-AUC at high-precision operating point, false-positive rate by demographic.
- **Network growth**: link-prediction AUC, cohort retention curves.

## Key sources

- Facebook AI / Meta engineering blog (recommendation systems)
- Twitter (X) recommendation algorithm open-source
- "Networks, Crowds, and Markets" (Easley & Kleinberg)
- "Mining of Massive Datasets" (Leskovec, Rajaraman, Ullman)
