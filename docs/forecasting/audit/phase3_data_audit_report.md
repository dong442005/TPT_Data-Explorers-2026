# Phase 3A Data Audit Report

## 1. Files Loaded
- 4 aligned parquet files (m_train, m_future, w_train, w_future)
- track1_model_feature_sets.json
- feature_registry_track1.json
- raw_fact_sales.csv: Loaded
- raw_product_price.csv: Loaded

## 2. Data Periods & Gap Validation
- Found Train Periods (period_month): [1, 2, 3, 13, 14, 15]
- ✅ **PASS**: Periods are exactly Jan25-Mar25 and Jan26-Mar26.
- ✅ **PASS**: Gap Apr25-Dec25 is correctly preserved (not imputed).

## 3. Schema and Feature Set Checks
### monthly_minimal: PASS
- Feature count: 9
### monthly_extended: PASS
- Feature count: 21
### weekly_minimal: PASS
- Feature count: 11
### weekly_extended: PASS
- Feature count: 15

## 4. Block-Aware Lag Validation
- Jan26 `qty_lag_1` missing rate: 100.0%
- ✅ **PASS**: Lag does not jump over the 9-month gap.

## 5. Basic Statistics
- `m_train` rows: 925, SKUs: 265
- `m_future` rows: 795, SKUs: 265
- ✅ **PASS**: Target column `total_quantity` exists in train.

## 6. Pricing Data Validation
- `product_price.csv` has 1016 rows. Columns: ['price_id', 'product_code', 'unit_price', 'effective_from', 'effective_to', 'created_at']
- ✅ **PASS**: product_price has required effective date columns.
- `fact_sales.csv`: Max diff between `line_total` and `qty * unit_price`: 189.00
- ✅ **PASS**: line_total is approx quantity * unit_price.
