# Domain Reference: Finance

## Key Performance Indicators (KPIs)
- ROC-AUC (fraud, credit risk)
- Gini coefficient (= 2 * AUC - 1)
- KS statistic (Kolmogorov-Smirnov) — separation between good/bad
- Precision-Recall AUC (fraud detection with extreme imbalance)
- Sharpe ratio, Sortino ratio (portfolio/trading)
- Expected loss = PD × LGD × EAD

## Critical Financial Features

| Feature | Typical Range | Significance |
|---------|-------------|--------------|
| FICO/Credit Score | 300–850 | < 580 = poor, 580-669 = fair, 670-739 = good, ≥ 740 = excellent |
| DTI (Debt-to-Income) | 0–100% | > 43% typically disqualifies for QM loans |
| LTV (Loan-to-Value) | 0–120%+ | > 80% = requires PMI, > 100% = underwater |
| APR | 0–36%+ | Regulatory caps vary by state/country |
| Transaction velocity | Varies | Sudden spikes = fraud signal |
| Amount deviation | Varies | Transactions > 3σ from user mean = suspicious |

## Domain-Specific Feature Engineering
- **Velocity features**: Transaction count/amount per hour/day/week — key fraud signal
- **Recency features**: Days since last transaction, last missed payment, account opening
- **Behavioral deviation**: Current transaction amount vs rolling mean/std for the user
- **Time-of-day features**: After-hours transactions, weekend patterns
- **Geographic features**: Distance between consecutive transactions, unusual locations
- **Aggregation windows**: 1h, 24h, 7d, 30d rolling aggregates per customer
- **PD/LGD/EAD components**: For credit risk, model each separately
- **Payment ratios**: Minimum payment vs full payment vs balance ratios
- **Utilization rate**: Credit used / credit limit — non-linear impact (bins matter)
- **Vintage analysis**: Age of account, months on book

## Common Pitfalls
1. **Temporal leakage**: Using future transaction data to predict fraud. Split by time, not random
2. **Extreme imbalance**: Fraud is typically 0.1-0.5%. Never use accuracy. Use precision-recall
3. **Regulatory features**: Some features (race, zip code as proxy for race) may violate fair lending laws
4. **Survivorship bias**: Only modeling customers who were approved ignores reject population
5. **Non-stationarity**: Financial data distributions shift over time (concept drift). Models need monitoring
6. **Dollar-weighted metrics**: A model that catches $1M fraud but misses $100K fraud needs dollar-weighted evaluation
7. **Synthetic minorities**: SMOTE on financial data can create impossible transactions

## Preferred Metrics
- **Fraud detection**: Precision-Recall AUC, F1 at specific threshold, dollar-weighted recall
- **Credit scoring**: Gini, KS statistic, ROC-AUC
- **Default prediction**: Brier score (calibration matters for PD)
- **Trading/portfolio**: Sharpe ratio, max drawdown, win rate

## Regulatory Considerations
- Fair lending: Model must not discriminate on protected classes (directly or via proxy)
- Explainability: Many jurisdictions require reason codes for credit decisions (SHAP helps)
- Basel/IFRS: PD, LGD, EAD models have specific regulatory validation requirements
- GDPR: Right to explanation for automated decisions

## Red Flags
- Random train/test split on time-series financial data (must use temporal split)
- Accuracy reported for fraud detection (imbalance makes it meaningless)
- Customer ID or account number used as feature
- No consideration of dollar amounts in evaluation (all fraud treated equally)
- Protected class features included without fairness analysis
