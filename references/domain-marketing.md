# Domain Reference: Marketing

## Key Performance Indicators (KPIs)
- Customer Lifetime Value (CLV/LTV)
- Churn rate / retention rate
- Conversion rate (CVR)
- Click-through rate (CTR)
- Return on Ad Spend (ROAS)
- Cost per Acquisition (CPA)
- Net Promoter Score (NPS)
- Customer Acquisition Cost (CAC)

## Critical Marketing Features

| Feature | Typical Range | Significance |
|---------|-------------|--------------|
| Recency (R) | 1–365+ days | Days since last purchase/interaction |
| Frequency (F) | 1–100+ | Number of transactions in period |
| Monetary (M) | Varies | Total spend in period |
| Tenure | 0–N months | Time since first interaction |
| Email open rate | 15–25% avg | Below 10% = disengaged segment |
| CTR | 1–5% avg | Above 5% = high engagement |
| Bounce rate | 26–70% | Above 70% = content/targeting issue |
| Session duration | 2–3 min avg | Below 30s = likely bounce |

## Domain-Specific Feature Engineering
- **RFM scores**: Recency, Frequency, Monetary — quintile binning (1-5 per dimension)
- **CLV calculation**: `avg_order_value × purchase_frequency × customer_lifespan`
- **Engagement score**: Weighted composite of opens, clicks, visits, purchases
- **Churn risk windows**: 30/60/90 day inactivity flags
- **Cohort features**: Acquisition channel, signup month, first purchase category
- **Campaign response history**: Open/click/convert rates per customer
- **Channel preference**: Primary channel by interaction frequency
- **Lifecycle stage**: New, active, at-risk, dormant, churned
- **Seasonality features**: Holiday proximity, day-of-week, month-of-year
- **Attribution features**: First-touch, last-touch, multi-touch attribution weights

## Common Pitfalls
1. **Churn definition ambiguity**: Define churn precisely (e.g., "no purchase in 90 days") — different definitions produce different models
2. **Survivorship bias in CLV**: Only modeling active customers overestimates CLV
3. **Selection bias in A/B tests**: Non-random assignment, novelty effects, sample ratio mismatch
4. **Aggregation period matters**: Monthly vs weekly vs daily aggregation changes patterns
5. **Channel attribution**: Last-click attribution undervalues awareness channels
6. **Lookalike leakage**: Using response variable features (e.g., "has_converted") in the prediction features
7. **Seasonal confounding**: Model trained in Q4 (holiday) may fail in Q1

## Preferred Metrics
- **Churn prediction**: F1, precision-recall AUC (churners are minority class)
- **CLV prediction**: RMSE, MAE, MAPE (regression task)
- **Campaign response**: Lift, cumulative gains chart, top-decile lift
- **Segmentation**: Silhouette score, within-cluster variance, business interpretability

## Analysis Types
- **RFM segmentation**: Classic customer segmentation framework
- **Cohort analysis**: Retention curves by acquisition cohort
- **A/B test analysis**: Proper hypothesis testing with power analysis
- **Funnel analysis**: Drop-off rates between stages
- **Attribution modeling**: Multi-touch attribution, Markov chains

## Red Flags
- Churn model includes post-churn features (e.g., "days since last email open" where open=0 means churned)
- CLV model trained on < 6 months of data (insufficient lifecycle observation)
- A/B test concluded without sufficient sample size (p-hacking)
- Campaign model doesn't account for control/holdout group
- RFM built on single transaction window without lifecycle context
