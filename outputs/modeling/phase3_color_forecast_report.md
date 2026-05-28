# Phase 3F Track 2: Color/Variant Forecast Report

## 1. Objective and Methodology
This report transitions the high-level group forecast from Track 1 into actionable SKU/Color-level variant planning for Q2 2026. 

**Important Note:** Track 2 is strictly an **aggregation and derivation** of the finalized Track 1 outputs. No new machine learning models were trained. The total quantities and revenues map perfectly to Track 1 totals without any data leakage.

### Forecast Inputs (from Track 1)
- **Primary ML Upside Forecast**: `XGBoost_monthly_extended_features` (~100K Q2 units).
- **Business Benchmarks**: `Group-Share Base` (~37K units) and `Group-Share Aggressive` (~42K units).

---

## 2. Top Color Forecast (Q2 2026)
Based on the Primary ML Upside forecast, the demand is heavily concentrated in core neutral colors, capturing the momentum from the March 2026 sales spike.

### Top 5 Colors by Quantity
| Base Color | Variant Color | XGBoost ML Upside (Qty) | Group-Share Base (Qty) | Group-Share Aggressive (Qty) |
|:---|:---|:---:|:---:|:---:|
| **Đen (Black)** | Đen | 15,693 | 5,885 | 6,722 |
| **Kem (Cream)** | Kem | 11,889 | 4,459 | 5,094 |
| **Ghi (Grey)** | Ghi | 11,111 | 4,167 | 4,760 |
| **Hồng (Pink)** | Hồng | 9,049 | 3,394 | 3,876 |
| **Xanh (Blue)** | Xanh | 8,587 | 3,220 | 3,678 |

*Observation: If production must be strictly controlled, the `Group-Share Base (Qty)` serves as the minimum safety threshold, while the `XGBoost ML Upside` provides the theoretical ceiling if the Mar26 momentum sustains throughout Q2.*

---

## 3. Slow-Moving SKU & Color Flags
To mitigate inventory risk—especially given the bullish ML forecast—we analyzed historical Q1 2026 sales to flag SKUs that have stalled or are actively declining.

### Flagging Distribution (Total 265 SKUs)
- **`healthy` (153 SKUs)**: Normal activity, follow Q2 forecast.
- **`red_no_demand` (51 SKUs)**: 0 sales in Q1 2026. **Action:** Phase out or stop production immediately unless retained for strategic display.
- **`amber_slow_moving` (37 SKUs)**: Sales are > 0 but fall within the bottom 10% of their respective product groups (or <= 10 units total). **Action:** Deprioritize in production. Liquidate existing excess inventory.
- **`declining_activity` (6 SKUs)**: Volume dropped by > 50% YoY (Q1 2026 vs Q1 2025). **Action:** Review marketing/pricing; reduce production forecast despite historical highs.
- **`new_or_uncertain` (18 SKUs)**: Appeared very recently (March 2026) with no prior history. **Action:** Monitor demand closely before committing to large production runs.

> [!WARNING]
> **Production Guardrail**
> The 94 SKUs flagged as `red_no_demand`, `amber_slow_moving`, and `declining_activity` represent significant inventory risk. Even if the ML model projects a slight uptick for these SKUs due to seasonal lags, we strongly recommend manually overriding their forecasts down to zero or matching the `Group-Share Base` minimums to avoid dead stock.

---

## 4. Output Artifacts
All color-level data has been exported for operations:
- **`phase3_color_forecast_q2_2026.csv`**: Detailed Q2 projection per Color/SKU.
- **`phase3_color_summary_q2_2026.csv`**: Pivot table comparing ML Upside vs. Group-Share scenarios.
- **`phase3_slow_moving_sku_color_flags.csv`**: The comprehensive flagging list for the 265 active SKUs.
