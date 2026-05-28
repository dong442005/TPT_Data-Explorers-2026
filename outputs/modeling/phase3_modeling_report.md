# Phase 3 Modeling Report: Predictive Models & Business Benchmarks (Track 1)

## 1. Objective and Strategic Framing

**Objective**: Establish a robust forecasting foundation for Q2 2026. Given the extreme data sparsity (9-month gap between Apr 2025 and Dec 2025), our strategy involves balancing predictive power with business scenario planning.

- **Primary Predictive Model**: `XGBoost_monthly_extended_features` (Machine Learning). Selected for presentation due to its superior error metrics and its ability to capture the momentum of the recent demand shock.
- **Business Benchmark / Planning Guardrail**: `Group-Share Proportional`. Retained to enforce top-down scenario constraints (Conservative/Base/Aggressive) and reconcile forecasts against financial blueprints.

**Validation Setup**: 
- We hold out **March 2026** as the validation set. 
- While March 2026 experienced an abnormal demand spike, the ML model interprets this not just as an anomaly, but as a potential **new momentum/trend** going into Q2.
- **Metrics**: WMAPE (primary), SMAPE, MAE, RMSE, Mean_Error, Bias_Ratio (sum(pred - actual) / sum(actual)).

---

## 2. Model Selection & Risk Explanation

### Primary Predictive Model (Upside Signal)
**XGBoost monthly extended** is selected as the primary predictive model for presentation. 
- **Validation Win**: It achieved the lowest WMAPE (0.514) on the Mar26 stress test, significantly outperforming heuristic baselines.
- **Bias Correction**: While statistical baselines severely under-forecasted the Mar26 spike (Bias_Ratio ~ -51%), XGBoost adapted to the momentum, achieving a Bias_Ratio of just +10.4%.
- **Official ML Artifact**: `phase3c_ml_forecast_q2_2026.csv`

### Business Scenario Benchmark (Guardrail)
**Group-Share Proportional** is retained as a business scenario benchmark and reconciliation guardrail.
- It acts as a safety net because the ML validation is based on a single stress month.
- It provides explainable, blueprint-reconciled forecasts across Conservative, Base, and Aggressive scenarios.

### Risk Explanation
> [!WARNING]
> **Momentum-Driven Forecasting vs. Planning Safety**
> Because the XGBoost model treats the Mar26 spike as momentum, its Q2 forecast is extremely bullish (~2.66x the Base Scenario). XGBoost Q2 forecast should be interpreted as an upside demand signal driven by March momentum, not as an unconditional production commitment.
> 
> **Recommendation for Planning**: Because Q2 ground truth is unavailable and validation relies on one stress month, operational planning should compare the ML upside forecast against Group-Share Base/Aggressive before final inventory and production decisions.

---

## 3. Comparative Summary

Validation metrics and Q2 scenario projections are reported separately because Mar26 validation tests short-term predictive accuracy, while Q2 scenarios represent planning assumptions.

### Table A: Mar26 Validation Metrics
| Metric | `jan_feb_avg` | `group_share_validation` | `XGBoost_monthly_extended` |
|:---|:---:|:---:|:---:|
| **WMAPE** | 0.573 | 0.575 | **0.514** |
| **SMAPE** | 0.916 | 0.923 | 0.991 |
| **MAE** | 55.46 | 55.62 | **49.67** |
| **RMSE** | 111.24 | 111.29 | **88.35** |
| **Mean_Error** | -49.16 | -49.34 | **+10.02** |
| **Bias_Ratio** | -51.0% | -51.2% | **+10.4%** |

### Table B: Q2 Projection Comparison
| Model / Scenario | Q2 Total Quantity | Q2 Total Revenue | Ratio vs Group-Share Base | Interpretation |
|:---|:---:|:---:|:---:|:---:|
| **Group-Share Base** | 37,596 | 60.91 B | 1.00x | Anchor planning baseline |
| **Group-Share Aggressive** | 42,953 | 69.59 B | 1.14x | Aggressive planning threshold |
| **XGBoost_monthly_extended** | 100,227 | 161.09 B | 2.66x | Upside demand signal (momentum) |

## 4. Conclusion

**XGBoost monthly extended** is selected as the primary predictive model for presentation, while **Group-Share Proportional** is retained as a business scenario benchmark and reconciliation guardrail. 

This dual-track reporting structure ensures we do not ignore the massive momentum signal detected by the ML model in March, while simultaneously providing supply chain and finance teams with a secure, blueprint-aligned operational floor.
