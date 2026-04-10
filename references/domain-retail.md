# Domain Reference: Retail

## Key Performance Indicators (KPIs)
- Revenue per customer / Average Order Value (AOV)
- Basket size (items per transaction)
- Inventory turnover rate
- Gross margin / Contribution margin
- Sell-through rate
- Stockout rate
- Customer retention rate
- Same-store sales growth

## Critical Retail Features

| Feature | Typical Range | Significance |
|---------|-------------|--------------|
| Price elasticity | -0.5 to -3.0 | How demand changes with price |
| Basket size | 1–20+ items | Average items per transaction |
| AOV | Varies by category | Average order value |
| Inventory days | 30–120 days | Days of inventory on hand |
| Return rate | 5–30% | By category: apparel 25-30%, electronics 10-15% |
| Promotion lift | 1.2x–3x | Sales uplift during promotion |
| Cross-sell rate | 5–20% | Rate of complementary product purchase |

## Domain-Specific Feature Engineering
- **Price features**: Current price, regular price, discount %, price rank within category
- **Basket analysis**: Association rules (support, confidence, lift), frequently bought together
- **Seasonality**: Week of year, holiday flags, seasonal index, weather correlation
- **Inventory signals**: Days of supply, stockout flag, reorder point proximity
- **Demand patterns**: Rolling 7/14/30-day sales, trend, velocity
- **Category hierarchy**: Department → category → subcategory → item aggregation levels
- **Promotion features**: On-promotion flag, promo type, cannibalization rate
- **Customer segments**: High-value, deal-seeker, seasonal-only, one-time buyer
- **Time features**: Day of week, hour of day, payday proximity
- **Competitive pricing**: Price position vs competitors (if available)

## Common Pitfalls
1. **Promotional leakage**: Using promotion flag to predict sales without controlling for it
2. **Seasonality confusion**: Model picks up seasonal patterns as feature importance (December ≠ "high demand forever")
3. **New product cold start**: Models can't predict demand for products with no history
4. **Cannibalization**: Promoting item A reduces sales of substitute item B — model must account for this
5. **Return rate varies by channel**: Online returns 25-30% vs in-store 10% — segment before modeling
6. **Stockout bias**: Zero sales ≠ zero demand. Need stockout indicators
7. **Price optimization traps**: Optimizing price without demand constraints leads to unrealistic recommendations

## Preferred Metrics
- **Demand forecasting**: MAPE, WMAPE (weighted), RMSE, bias (systematic over/under-prediction)
- **Product recommendation**: Precision@K, Recall@K, NDCG, hit rate
- **Price optimization**: Revenue lift, margin impact, elasticity estimation accuracy
- **Customer segmentation**: Silhouette score, revenue concentration, segment stability

## Analysis Types
- **Market basket analysis**: Apriori, FP-Growth for association rules
- **Demand forecasting**: Time series (ARIMA, Prophet, LSTM) or ML with lag features
- **Price elasticity**: Log-log regression, demand curves
- **Assortment optimization**: Category management, product clustering
- **Inventory optimization**: Economic Order Quantity, safety stock calculation

## Red Flags
- Demand model doesn't handle zero-demand days (stockouts vs true zero demand)
- Price elasticity model ignores cross-elasticity effects
- Seasonal model trained on < 2 years of data (can't distinguish annual patterns)
- Customer segmentation uses single-period data (misses lifecycle)
- SKU-level model without category hierarchy features
