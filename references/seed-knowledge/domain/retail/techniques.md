---
area: retail
category: domain
track: tabular
seeded_at: 2026-04-14
seed_source: claude-training-cutoff-2025-05
refresh_command: /dataforge-learn --area retail
status: seed
schema_version: 1.0
---

# Retail / E-commerce — Domain Knowledge

## Core techniques

### [ret-001] Hierarchical forecasting
**Summary:** Sales forecasts roll up store -> region -> chain and SKU -> category -> department. Train at the lowest granularity and reconcile with `hts` / MinT reconciliation, or train per-level and ensemble.
**When to use:** Any multi-store / multi-SKU demand forecast.

### [ret-002] Intermittent demand
**Summary:** Slow-moving SKUs have many zero-sales days. Standard regression overfits the zeros. Use Croston, SBA, or Tweedie loss in XGBoost (`objective='reg:tweedie'`).

### [ret-003] Price elasticity features
**Summary:** Compute `price_relative = price / category_avg_price`, `discount_pct = (list - actual) / list`, `competitor_price_diff`. These dominate demand models.

### [ret-004] Calendar features
**Summary:** Holidays (with country-specific moving dates - Easter, Diwali, Chinese New Year), payday weeks, end-of-month, school holidays, Black Friday / Cyber Monday windows. Use `holidays` PyPI package + custom calendars.

### [ret-005] Customer lifetime value
**Summary:** BG/NBD + Gamma-Gamma (lifetimes package) for non-contractual settings. For subscription, survival models on churn + ARPU.

## Pitfalls

- Promotional effects: a sales spike during a 50%-off week is not "demand" - it's an offer effect. Build a counterfactual baseline.
- Stockouts mask true demand. If `units_sold == on_hand`, the true demand was higher. Treat as right-censored.
- Returns lag the sale by days/weeks - net revenue features need a delay.
- Cannibalization: a new SKU steals from existing ones. Account for it in lift studies.

## Recommended metrics

- **Forecasting**: WAPE / MAPE per SKU, MASE for cross-series comparison, pinball loss for quantile forecasts (inventory targets need P90, not P50).
- **Recommendation**: NDCG@k, MAP@k, hit-rate, coverage.
- **Pricing**: incremental revenue uplift vs holdout.

## Key sources

- M5 Forecasting Competition winning solutions (Kaggle)
- Instacart Market Basket Analysis writeups
- Walmart store sales forecasting notebooks
- Wayfair / Shopify / Stitch Fix engineering blogs
