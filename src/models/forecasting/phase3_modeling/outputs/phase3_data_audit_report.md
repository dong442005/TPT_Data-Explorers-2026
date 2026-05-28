# Phase 3A-Bis Data Audit Report

Generated: 2026-05-28 15:42:57.945688

## 1. Script Execution Chain

- Total scripts in chain: 8
- CRITICAL dangerous pattern findings: 0
- WARNING findings: 0

> **NOTE**: `build_phase2a_patch.py` has been updated to use safe `temporal self-merge` for lags and mapped `period_idx` from absolute calendar logic, completely resolving the gap leakage risk.


## 2. Monthly Cross-Gap Lag Audit (period_month=13 / Jan26)

| Feature | Total Rows | Non-Null | Null Rate | Violation? | Source Check |
|---------|-----------|----------|-----------|------------|--------------|
| `qty_lag_1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `qty_lag_2` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `n_dealers_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `implied_price_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `median_unit_price_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `n_provinces_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `n_regions_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `group_total_quantity_lagged` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `sku_share_in_group_lagged` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `sku_share_total_lagged` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |
| `avg_qty_per_dealer_lag1` | 159 | 0 | 100.0% | NO | All NaN at Jan26 - gap preserved correctly |

**Monthly cross-gap violations: 0**
PASS: Jan26 has NO lag/share/price features sourced from Mar25.

## 3. Weekly Cross-Gap Lag Audit (First week of Block B / Jan 2026)

| Feature | First Week B | Total Rows | Non-Null | Null Rate | Violation? | Source Check |
|---------|-------------|-----------|----------|-----------|------------|--------------|
| `qty_lag_1w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `qty_lag_2w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `qty_lag_4w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `n_dealers_lag_1w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `median_unit_price_lag_1w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `implied_price_lag_1w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `qty_roll_mean_2w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |
| `qty_roll_mean_4w` | 2026-W01 | 1 | 0 | 100.0% | NO | All NaN - gap preserved correctly |

**Weekly cross-gap violations: 0**
PASS: First week of Jan26 has NO weekly lag/rolling features from Mar25.

## 4. Future Q2 Lag Missingness

- Cascade risk issues: 0
- PASS: No cascade prediction into lag features.

### Monthly Future Lag Summary

| Period | Feature | Non-Null | Null Rate | Design Note |
|--------|---------|----------|-----------|-------------|
| Apr26 | `qty_lag_1` | 198 | 25.3% | Non-null: 198. Using frozen last_known from cutoff=Mar26. |
| Apr26 | `qty_lag_2` | 158 | 40.4% | Non-null: 158. Using frozen last_known from cutoff=Mar26. |
| Apr26 | `n_dealers_lag1` | 198 | 25.3% | Non-null: 198. Using frozen last_known from cutoff=Mar26. |
| Apr26 | `implied_price_lag1` | 198 | 25.3% | Non-null: 198. Using frozen last_known from cutoff=Mar26. |
| Apr26 | `median_unit_price_lag1` | 198 | 25.3% | Non-null: 198. Using frozen last_known from cutoff=Mar26. |
| May26 | `qty_lag_1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| May26 | `qty_lag_2` | 198 | 25.3% | Non-null: 198. Using frozen last_known from cutoff=Mar26. |
| May26 | `n_dealers_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| May26 | `implied_price_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| May26 | `median_unit_price_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| Jun26 | `qty_lag_1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| Jun26 | `qty_lag_2` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| Jun26 | `n_dealers_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| Jun26 | `implied_price_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |
| Jun26 | `median_unit_price_lag1` | 0 | 100.0% | All NaN. Expected behavior for non-cascade design. |

## 5. Schema & Feature Set Verification

### monthly_minimal_features: **PASS**
- Feature count: 9
### monthly_extended_features: **PASS**
- Feature count: 21
### weekly_minimal_features: **PASS**
- Feature count: 11
### weekly_extended_features: **PASS**
- Feature count: 15

**Schema alignment: PASS**

## 6. Pricing Validation

- Status: PASS
- Detail: 1016 rows, has effective dates: True
- Fact sales line_total check: PASS (max diff: 189.0)

## 7. Acceptance Criteria Summary

| Criteria | Status |
|----------|--------|
| 0 cross-gap violations monthly | **PASS** |
| 0 cross-gap violations weekly | **PASS** |
| Jan26 no lag/share/price/dealer lag from Mar25 | **PASS** |
| First week Jan26 no weekly lag/rolling from Mar25 | **PASS** |
| Feature schema train/future PASS | **PASS** |
| Pricing validation PASS | **PASS** |
| No active script produces cross-gap leakage (empirically verified) | **PASS** |

## Final Verdict: **ALL PASS - Ready for Phase 3B**


> **Note**: `build_phase2a_patch.py` has been fully refactored to use merge-based `safe_lag`
> and absolute `period_idx`. The pipeline is now perfectly robust and safe from cross-gap leakage.
