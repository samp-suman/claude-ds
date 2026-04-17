# Domain Reference: Logistics / Supply Chain

## KPIs

| KPI | Description | Target |
|-----|-------------|--------|
| MAPE | Mean Absolute Percentage Error (demand forecast) | <10% excellent, <20% acceptable |
| WMAPE | Weighted MAPE (volume-weighted, better for skewed demand) | <15% excellent |
| Bias | Systematic over/under-forecast (positive = overforecast) | Near 0 |
| Fill Rate | % of demand fulfilled from available stock | >95% |
| In-Stock Rate | % of time SKU is available when ordered | >98% |
| Stockout Rate | % of periods with zero stock | <2% |
| Inventory Turnover | COGS / Average Inventory Value | Industry-dependent (grocery >20, industrial ~5) |
| Days of Supply (DoS) | Inventory / Daily Demand | 7–30 days typical |
| On-Time Delivery (OTD) | % deliveries within promised window | >95% |
| Perfect Order Rate | Orders complete, on-time, undamaged | >95% |
| Order Cycle Time | Order placement → delivery | Category-dependent |
| OTIF | On-Time In-Full delivery rate | >90% |

## Feature Engineering Patterns

### Demand Forecasting Features
| Feature | Formula | Why |
|---------|---------|-----|
| Lag demand | `demand[t-7]`, `demand[t-14]`, `demand[t-28]` | Autoregressive component |
| Rolling average | `rolling_mean(demand, 7d/14d/28d)` | Smoothed baseline |
| Rolling std | `rolling_std(demand, 14d)` | Demand variability signal |
| Demand CV | `std / mean` per SKU | Intermittency classification |
| YoY growth | `demand[t] / demand[t-365]` | Trend adjustment |
| Day of week | `date.weekday()` | Weekly seasonality |
| Week of year | `date.isocalendar().week` | Annual seasonality |
| Is holiday | `date in holiday_calendar` | External event |
| Days to holiday | `min(days_until_next_holiday, 30)` | Pre-holiday stock-up |
| Promotion flag | Binary from promotion calendar | Promotional lift |
| Promotion discount | `(original_price - promo_price) / original_price` | Elasticity signal |
| Price change | `price[t] / price[t-1]` | Price-demand relationship |

### Inventory Optimization Features
| Feature | Formula | Why |
|---------|---------|-----|
| Lead time | Supplier → warehouse days | Reorder point calculation |
| Lead time variability | `std(lead_time)` | Safety stock buffer |
| Reorder point | `μ_demand × lead_time + Z × σ_demand × √lead_time` | When to reorder |
| Safety stock | `Z × σ_demand × √lead_time` (Z=1.65 for 95%) | Buffer for uncertainty |
| EOQ | `√(2 × demand × order_cost / holding_cost)` | Optimal order quantity |
| ABC classification | A: top 80% revenue, B: next 15%, C: bottom 5% | Differentiated management |
| XYZ classification | X: stable, Y: seasonal, Z: erratic | Forecasting approach |

### Delivery Prediction Features
| Feature | Why |
|---------|-----|
| Distance (haversine) | Primary delivery time driver |
| Carrier ID | Carrier performance varies significantly |
| Weight/volume | Handling time at depot |
| Time of day (pickup) | Traffic patterns |
| Day of week | Weekend slowdowns |
| Zone type | Urban vs rural last-mile differences |
| Weather severity | Encoded external event |
| Historical carrier performance (route) | Rolling avg actual delivery time for carrier+route |

## Demand Pattern Classification

| Pattern | CV (σ/μ) | % Zeros | Recommended Model |
|---------|----------|---------|-------------------|
| Smooth | CV < 0.5 | < 10% | ARIMA, ETS, Prophet, LightGBM |
| Erratic | CV > 0.5 | < 10% | LightGBM, LSTM, XGBoost |
| Intermittent | CV < 0.5 | > 10% | Croston, ADIDA, zero-inflated |
| Lumpy | CV > 0.5 | > 10% | TSB, IMAPA, Poisson regression |

## Common Pitfalls

| Pitfall | Why it matters | Fix |
|---------|---------------|-----|
| Stockout periods in training | Model learns zero demand when product is unavailable | Flag and exclude stockout periods |
| Random CV on time-series | Leaks future demand patterns into training | Time-based split always |
| Single-step vs multi-step forecasting | Single-step MAE ≠ forecast error over replenishment horizon | Evaluate at full forecast horizon |
| Ignoring promotions | Promotions cause 2–5x demand spikes that appear as noise | Promotions as explicit features |
| Aggregation level mismatch | SKU-level accuracy different from category/warehouse level | Evaluate at the level decisions are made |
| Symmetric loss on asymmetric cost | Stockout cost >> overstock cost for most categories | Asymmetric loss function (understock penalty) |
| New SKU / cold start | No history for new products | Cross-SKU features, attribute-based models |
| Cannibalization | Promotions on one SKU reduce sales of substitutes | Cluster substitutes, add cross-elasticity features |

## Preferred Metrics by Task

| Task | Primary Metric | Secondary |
|------|----------------|-----------|
| Demand forecasting | WMAPE, Bias | MAPE, RMSE |
| Inventory optimization | Fill Rate, DoS | Inventory turnover cost |
| Delivery time prediction | MAE (days), P90 error | RMSE |
| Route optimization | Total distance/time | vs. heuristic baseline |
| Stockout prediction | F1 (recall-focused) | PR-AUC |

## Modeling Approaches

| Problem | Recommended Models |
|---------|--------------------|
| Demand forecasting (smooth) | LightGBM, Prophet, ETS, ARIMA |
| Demand forecasting (intermittent) | Croston, ADIDA, zero-inflated Poisson |
| Multi-step horizon | Recursive, DIRECT, MIMO strategies |
| Hierarchical reconciliation | MinT (Minimum Trace), OLS, Bottom-Up |
| Delivery time prediction | LightGBM, XGBoost (tabular), gradient boosting |
| Route optimization | Nearest neighbor heuristic → OR-Tools → metaheuristics |
| Inventory optimization | Newsvendor model, Q-R policy, simulation |

## Red Flags

- Random train/test split on time-series demand data
- Zero-demand rows included without stockout flag
- No lag features in demand model
- Evaluating at daily level when decisions are made weekly
- Using RMSE as primary metric when cost is asymmetric
- Ignoring external events (holidays, promotions)
- Building SKU-level model without any category-level hierarchy features
- No bias (directional error) reporting — bias causes systematic over/under-stocking
