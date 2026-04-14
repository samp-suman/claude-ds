---
area: marketing
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area marketing
status: seed
schema_version: 1.0
---

# Marketing — Domain Knowledge

## Core techniques

### [mkt-001] Uplift modeling, not response modeling
**Summary:** A response model predicts "will this user convert?". An uplift model predicts "will the campaign CAUSE conversion?". Use `causalml`, `econml`, or T-learner / X-learner / DR-learner over treatment-control logs.
**When to use:** Any campaign targeting where you have a holdout group.

### [mkt-002] Attribution beyond last-click
**Summary:** Last-click overweights bottom-of-funnel channels. Use Markov-chain attribution, Shapley-value attribution, or media-mix models (PyMC-Marketing, Robyn) for budget allocation.

### [mkt-003] CLV / LTV models
**Summary:** BG/NBD + Gamma-Gamma for non-contractual; survival + ARPU for subscriptions. Don't aggregate at customer level then predict "future revenue" - it's a censored survival problem.

### [mkt-004] Cohort analysis as a feature
**Summary:** Acquisition cohort, source channel, first-product, time-to-second-purchase are stronger predictors than current-state features. Always include them.

### [mkt-005] Holdout discipline
**Summary:** Always reserve an untargeted holdout (5-10%) on every campaign so you can measure incremental lift. Without it, you cannot distinguish a good model from a good audience.

## Pitfalls

- Selection bias: training only on past clickers ignores why others didn't.
- Leakage from post-treatment variables (e.g., "did user open the email" used as a feature for "will user convert").
- Multi-touch attribution requires deduplicated user IDs across devices - hard in cookie-less world.
- iOS 14.5+ (ATT) and cookie deprecation broke many funnel models; expect signal loss.

## Recommended metrics

- Uplift: Qini coefficient, AUUC, top-k uplift.
- Attribution: incremental revenue per channel, ROAS, MROI.
- Forecasting: lift over baseline, statistical significance via permutation tests.

## Key sources

- "Causal Inference for the Brave and True" (Matheus Facure)
- PyMC-Marketing docs and case studies
- Wayfair, Booking, Airbnb engineering blogs on experimentation
- "Trustworthy Online Controlled Experiments" (Kohavi, Tang, Xu)
