# Phase 2A Feature Alignment Report

## Mappings Applied

### Monthly Mappings
- `last_known_qty_1` -> `qty_lag_1`
- `last_known_qty_2` -> `qty_lag_2`
- `last_known_n_dealers_1` -> `n_dealers_lag1`
- `last_known_price_1` -> `implied_price_lag1`

### Weekly Mappings
- `last_known_qty_1w` -> `qty_lag_1w`
- `last_known_qty_2w` -> `qty_lag_2w`
- `last_known_qty_4w` -> `qty_lag_4w`
- `last_known_n_dealers_1w` -> `n_dealers_lag_1w`
- `last_known_median_unit_price_1w` -> `median_unit_price_lag_1w`

## Validation & Dropping Features

### monthly_minimal_features

Final feature count for monthly_minimal_features: **9** (was 9)
### monthly_extended_features

Final feature count for monthly_extended_features: **21** (was 21)
### weekly_minimal_features

Final feature count for weekly_minimal_features: **11** (was 11)
### weekly_extended_features

Final feature count for weekly_extended_features: **15** (was 15)

## Direct Multi-Horizon Verification

- Monthly future retains `horizon_month`: False
- Weekly future retains `horizon_week`: False
- Confirmed: No cascade lagging in future rows. Values frozen at last_known cutoff.

## Conclusion

- Schema match is 100% verified for all features left in the sets.
- No blockers before Phase 3 Modeling.