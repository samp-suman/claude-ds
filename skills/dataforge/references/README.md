# DataForge References — Index

Reference docs are loaded **on demand** by the orchestrator to keep token usage low.
Each file is a plain Markdown reference — not executable, just reference material for
Claude to read and reason from.

---

## Files

### model-catalog.md
**Loaded:** After problem type detection (Step 4)
**Contains:**
- Model selection table per problem type (classification, regression, clustering)
- When to use vs avoid each model
- Default hyperparameter starting points
- Dataset size rules (when LightGBM > RandomForest etc.)
- Feature type rules (all numeric vs many categoricals)

---

### feature-recipes.md
**Loaded:** During feature engineering (Step 6)
**Contains:**
- Decision tree: which transform to apply to which column type
- Scaling guide: which models need scaling vs which don't
- Encoding reference: one-hot vs label vs target encoding trade-offs
- Imputation reference: median vs mean vs mode vs forward fill
- Feature creation ideas for common patterns

---

### metric-guide.md
**Loaded:** During evaluation (Step 8)
**Contains:**
- When to use ROC-AUC vs F1 vs Accuracy (classification)
- When to use R² vs RMSE vs MAE (regression)
- Silhouette score interpretation (clustering)
- Cross-validation metric interpretation (std > 0.03 = high variance)
- Score range interpretation tables (0.9+ AUC → check for leakage)

---

### deploy-targets.md
**Loaded:** During deployment (Step 10)
**Contains:**
- Decision matrix: Streamlit vs FastAPI vs Flask
- Generated app features per target
- Run commands and ports
- Dockerfile reference for each target
- Cloud deployment notes (Streamlit Cloud, Railway, Docker + ECS)

---

### leakage-patterns.md
**Loaded:** During validation (Step 3)
**Contains:**
- 5 leakage pattern types with real examples
- Detection methods for each pattern
- Column name red flags (auto-flagged as warnings)
- What DataForge does automatically vs what needs user confirmation
- Train/test contamination prevention (scalers fit on training only)

---

### quality-gates.md
**Loaded:** During validation (Step 3)
**Contains:**
- Hard stop rules (exit code 2): thresholds + rationale
- Warning rules (exit code 1): thresholds + automatic mitigations
- Override protocol (how to proceed past a hard stop with explicit user confirmation)
- How to add new quality gate checks

---

## Adding a New Reference Doc

1. Create the file here: `skills/dataforge/references/{name}.md`
2. Add a load instruction in `skills/dataforge/SKILL.md`'s Reference Files table
3. Run `bash install.sh` from repo root
4. Update `CHANGELOG.md`

Reference docs should be:
- **Concise** — Claude reads these during orchestration; keep under 200 lines
- **Table-driven** where possible — faster to scan than prose
- **Linked** to the scripts that implement their rules (so they stay in sync)
