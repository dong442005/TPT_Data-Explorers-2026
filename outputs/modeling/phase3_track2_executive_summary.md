# Track 2 Executive Summary: Color/Variant Forecast

## 1. Top Q2 2026 Forecast by Color
Based on the highly predictive Track 1 outputs, demand for Q2 is heavily concentrated in neutral and core colors.

**Top 5 Colors (XGBoost ML Upside vs Group-Share Base):**
1. **Đen**: 15,693 units *(Base: 5,885)*
2. **Kem**: 11,889 units *(Base: 4,459)*
3. **Ghi**: 11,111 units *(Base: 4,167)*
4. **Hồng**: 9,049 units *(Base: 3,394)*
5. **Xanh**: 8,587 units *(Base: 3,220)*

**Production Recommendation:**
- Prioritize raw material sourcing and production for these core colors.
- **Planning Guardrail**: Use the `Group-Share Base` and `Group-Share Aggressive` quantities as the safe planning range. The `XGBoost ML Upside` should be treated as a strong momentum signal, but not an absolute production commitment to avoid overstocking if the market cools.

---

## 2. Inventory Risk Alert (Slow-Moving SKUs)
We flagged 265 active SKUs based on their Q1 2026 performance to mitigate dead stock risks.

**SKU Risk Distribution:**
- **`healthy` (153 SKUs)**: Normal activity.
- **`red_no_demand` (51 SKUs)**: Zero sales across all of Q1 2026.
- **`amber_slow_moving` (37 SKUs)**: Very low sales (<= 10 units or bottom 10% of their group).
- **`new_or_uncertain` (18 SKUs)**: Newly introduced in Mar26; insufficient data to penalize.
- **`declining_activity` (6 SKUs)**: Dropped by > 50% YoY.

**Recommended Actions for High-Risk Categories:**
- **`red_no_demand`**: Phase out or stop production immediately unless required for strategic display. Do not build stock.
- **`amber_slow_moving`**: Deprioritize. Liquidate existing excess inventory and do not run large batches.
- **`declining_activity`**: Review pricing, display, or marketing before committing to further production.
- **`new_or_uncertain`**: Pilot in small batches; monitor closely over the next 30 days.

---
*Note: This Track 2 analysis is derived directly from the Track 1 finalized forecasts (maintaining 100% reconciliation). It is an aggregation artifact for operational planning, not a separately trained model.*
