# Phase 3A-Bis Script Lineage Report

## Execution Chain

| Order | Script | Role | Writes Parquet? |
|-------|--------|------|-----------------|
| 1 | `build_phase1c_aggregations.py` | Builds fact_sales_monthly.parquet + fact_sales_weekly.parquet from raw CSVs. Ass... | YES |
| 2 | `build_phase2a_features.py` | First feature engineering pass. Creates *_features.parquet and *_future_q2_rows.... | YES |
| 3 | `build_phase2a_patch.py` | Panelizes historical data, enriches with lags/shares, creates multi-horizon futu... | YES |
| 4 | `build_phase2a_patch2.py` | Builds canonical feature_registry_track1.json and track1_model_feature_sets.json... | YES |
| 5 | `align_track1_features.py` | Aligns train (from model_panel) and future (from future_q2_rows) into *_aligned.... | YES |
| 6 | `align_track1_features_patch4.py` | Syncs feature sets with registry (drops disallowed). Reads aligned parquets.... | NO |
| 7 | `patch_5_features.py` | Adds horizon_month/horizon_week=1 to train, adds days_in_segment/is_partial_week... | YES |
| 8 | `patch_6_features.py` | Removes horizon from model feature sets, updates registry. Reads aligned parquet... | NO |


## Final Writer Analysis

Which script produces the FINAL version of each parquet file (last writer wins):

| Output File | Final Writer (Order) | Script |
|-------------|---------------------|--------|
| `data/features/track1_monthly_features.parquet` | 2 | `build_phase2a_features.py` |
| `data/features/track1_monthly_future_aligned.parquet` | 5 | `align_track1_features.py` |
| `data/features/track1_monthly_future_q2_rows.parquet` | 3 | `build_phase2a_patch.py` |
| `data/features/track1_monthly_model_panel.parquet` | 3 | `build_phase2a_patch.py` |
| `data/features/track1_monthly_train_aligned.parquet` | 7 | `patch_5_features.py` |
| `data/features/track1_weekly_features.parquet` | 2 | `build_phase2a_features.py` |
| `data/features/track1_weekly_future_aligned.parquet` | 5 | `align_track1_features.py` |
| `data/features/track1_weekly_future_q2_rows.parquet` | 3 | `build_phase2a_patch.py` |
| `data/features/track1_weekly_model_panel.parquet` | 3 | `build_phase2a_patch.py` |
| `data/features/track1_weekly_train_aligned.parquet` | 7 | `patch_5_features.py` |
| `data/interim/fact_sales_monthly.parquet` | 1 | `build_phase1c_aggregations.py` |
| `data/interim/fact_sales_weekly.parquet` | 1 | `build_phase1c_aggregations.py` |
| `data/metadata/feature_registry_track1.json` | 4 | `build_phase2a_patch2.py` |
| `data/metadata/track1_model_feature_sets.json` | 4 | `build_phase2a_patch2.py` |


## Dangerous Pattern Findings

| Order | Script | Line | Severity | Finding | Detail |
|-------|--------|------|----------|---------|--------|
| 3 | `build_phase2a_patch.py` | N/A | **ERROR** | FILE NOT FOUND | `Expected at C:\Users\HOANG TUNG\TPT_Data-Explorers-2026\src\models\forecasting\p` |
| 4 | `build_phase2a_patch2.py` | N/A | **ERROR** | FILE NOT FOUND | `Expected at C:\Users\HOANG TUNG\TPT_Data-Explorers-2026\src\models\forecasting\p` |
| 6 | `align_track1_features_patch4.py` | N/A | **ERROR** | FILE NOT FOUND | `Expected at C:\Users\HOANG TUNG\TPT_Data-Explorers-2026\src\models\forecasting\p` |
| 7 | `patch_5_features.py` | N/A | **ERROR** | FILE NOT FOUND | `Expected at C:\Users\HOANG TUNG\TPT_Data-Explorers-2026\src\models\forecasting\p` |
| 8 | `patch_6_features.py` | N/A | **ERROR** | FILE NOT FOUND | `Expected at C:\Users\HOANG TUNG\TPT_Data-Explorers-2026\src\models\forecasting\p` |


## Critical Analysis: Overwrite Chain


### Key Finding

`build_phase2a_features.py` (Order 2) uses **safe merge-based lag** (`safe_lag` via temporal self-merge).
However, `build_phase2a_patch.py` (Order 3) runs AFTER it and **OVERWRITES**:
- `track1_monthly_model_panel.parquet`
- `track1_weekly_model_panel.parquet`
- `track1_monthly_future_q2_rows.parquet`
- `track1_weekly_future_q2_rows.parquet`

`build_phase2a_patch.py` uses `groupby().shift()` with a **block_id mask**:
```python
shifted_val = df.groupby(group_col)[val_col].shift(lag_n)
shifted_block = df.groupby(group_col)[block_col].shift(lag_n)
mask = current_block == shifted_block
return shifted_val.where(mask, np.nan)
```

**Is this safe?** The block mask ensures that if `shift(1)` crosses from block A to block B,
the result is NaN. However, this approach ONLY works correctly if:
1. Data is sorted by product_code + time
2. block_id is correctly assigned (A for Q1/2025, B for Q1/2026)
3. There are no rows between block A and B

Since we never impute gap rows, shift(1) at the start of block B would look at the last row
of block A for the same product_code. The block mask would detect this (A != B) and return NaN.
**This is functionally correct but relies on block_id rather than calendar distance.**

Additionally, `build_phase2a_patch.py` uses `rank('dense')` for weekly `period_idx`:
```python
w_hist['period_idx'] = w_hist['week_start_date'].rank(method='dense').astype(int)
```
This collapses the calendar gap into consecutive integers, which means `shift(4)` for
`qty_lag_4w` would look 4 rows back, which could be incorrect if combined with the
block mask approach. However, since the block mask checks block_id equality, and all
weekly data within a block is contiguous, the rolling mean via safe_lag(shift-based)
should still produce correct results within each block.

### Verdict
The block-mask approach in `build_phase2a_patch.py` is **functionally safe against
cross-gap leakage** because it explicitly checks `block_id` equality. However, it is
**architecturally inferior** to the merge-based approach in `build_phase2a_features.py`
because it cannot detect intra-block distance errors.

The data audit in Section 2-3 below will EMPIRICALLY verify whether any cross-gap
leakage actually occurred in the final aligned parquet files.
