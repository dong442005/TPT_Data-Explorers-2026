import os
import json
import pandas as pd
import numpy as np

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Make sure to run this from the project root
from src.models.forecasting.shared.config.paths import RAW_DATA_DIR, CONFIG_DIR, FEATURES_DIR, IMPLEMENT_DIR

from src.models.forecasting.shared.config.paths import AUDIT_OUTPUTS_DIR
OUTPUT_DIR = AUDIT_OUTPUTS_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_phase3a_audit():
    report = ["# Phase 3A Data Audit Report\n"]
    
    # 1. Load Files
    print("Loading data...")
    m_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_train_aligned.parquet"))
    m_future = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_future_aligned.parquet"))
    w_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_train_aligned.parquet"))
    w_future = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_future_aligned.parquet"))
    
    with open(os.path.join(CONFIG_DIR, "track1_model_feature_sets.json"), "r") as f:
        feature_sets = json.load(f)
        
    with open(os.path.join(CONFIG_DIR, "feature_registry_track1.json"), "r") as f:
        registry = json.load(f)
        
    raw_fact = None
    raw_price = None
    raw_fact_path = os.path.join(RAW_DATA_DIR, "fact_sales.csv")
    raw_price_path = os.path.join(RAW_DATA_DIR, "product_price.csv")
    
    if os.path.exists(raw_fact_path):
        raw_fact = pd.read_csv(raw_fact_path)
    if os.path.exists(raw_price_path):
        raw_price = pd.read_csv(raw_price_path)
        
    report.append("## 1. Files Loaded")
    report.append("- 4 aligned parquet files (m_train, m_future, w_train, w_future)")
    report.append("- track1_model_feature_sets.json")
    report.append("- feature_registry_track1.json")
    report.append(f"- raw_fact_sales.csv: {'Loaded' if raw_fact is not None else 'Missing'}")
    report.append(f"- raw_product_price.csv: {'Loaded' if raw_price is not None else 'Missing'}\n")
    
    # 2. Data Periods Found & Gap Validation
    train_periods = sorted(m_train['period_month'].unique())
    expected_periods = [1.0, 2.0, 3.0, 13.0, 14.0, 15.0]
    has_gap = all(p not in train_periods for p in range(4, 13))
    
    report.append("## 2. Data Periods & Gap Validation")
    report.append(f"- Found Train Periods (period_month): {train_periods}")
    if train_periods == expected_periods and has_gap:
        report.append("- ✅ **PASS**: Periods are exactly Jan25-Mar25 and Jan26-Mar26.")
        report.append("- ✅ **PASS**: Gap Apr25-Dec25 is correctly preserved (not imputed).")
    else:
        report.append("- ❌ **FAIL**: Periods do not match expectation or gap was filled.")
    report.append("")
    
    # 3. Schema & Feature Sets
    report.append("## 3. Schema and Feature Set Checks")
    disallowed_features = {x["feature_name"] for x in registry if not x["allowed_for_model"]}
    
    def check_schema(set_name, f_list, df_tr, df_fut):
        tr_cols = set(df_tr.columns)
        fut_cols = set(df_fut.columns)
        
        miss_tr = [f for f in f_list if f not in tr_cols]
        miss_fut = [f for f in f_list if f not in fut_cols]
        disallow = [f for f in f_list if f in disallowed_features]
        leaks = [f for f in f_list if f in ['total_quantity', 'total_revenue', 'is_zero_sales_row', 'n_orders']]
        
        status = "PASS" if not miss_tr and not miss_fut and not disallow and not leaks else "FAIL"
        report.append(f"### {set_name}: {status}")
        report.append(f"- Feature count: {len(f_list)}")
        if miss_tr: report.append(f"  - ❌ Missing in train: {miss_tr}")
        if miss_fut: report.append(f"  - ❌ Missing in future: {miss_fut}")
        if disallow: report.append(f"  - ❌ Disallowed found: {disallow}")
        if leaks: report.append(f"  - ❌ Leakage found: {leaks}")
        
    check_schema("monthly_minimal", feature_sets["monthly_minimal_features"], m_train, m_future)
    check_schema("monthly_extended", feature_sets["monthly_extended_features"], m_train, m_future)
    check_schema("weekly_minimal", feature_sets["weekly_minimal_features"], w_train, w_future)
    check_schema("weekly_extended", feature_sets["weekly_extended_features"], w_train, w_future)
    report.append("")
    
    # 4. Check Block-Aware Lag (No jumping gap)
    report.append("## 4. Block-Aware Lag Validation")
    # For Jan26 (period 13), lag1 should be NaN because lag1 would be Dec25 which doesn't exist
    jan26_data = m_train[m_train['period_month'] == 13.0]
    if 'qty_lag_1' in jan26_data.columns:
        lag1_jan26_missing = jan26_data['qty_lag_1'].isna().mean()
        report.append(f"- Jan26 `qty_lag_1` missing rate: {lag1_jan26_missing*100:.1f}%")
        if lag1_jan26_missing > 0.99:
            report.append("- ✅ **PASS**: Lag does not jump over the 9-month gap.")
        else:
            report.append("- ❌ **FAIL**: Lag appears to jump the gap (missing rate too low).")
    report.append("")
    
    # 5. Missing Rates, Row Counts, Target Column
    report.append("## 5. Basic Statistics")
    report.append(f"- `m_train` rows: {len(m_train)}, SKUs: {m_train['product_code'].nunique()}")
    report.append(f"- `m_future` rows: {len(m_future)}, SKUs: {m_future['product_code'].nunique()}")
    if 'total_quantity' in m_train.columns:
        report.append("- ✅ **PASS**: Target column `total_quantity` exists in train.")
    else:
        report.append("- ❌ **FAIL**: Target column `total_quantity` missing from train.")
    report.append("")
    
    # 6. Pricing Data Validation
    report.append("## 6. Pricing Data Validation")
    if raw_price is not None:
        report.append(f"- `product_price.csv` has {len(raw_price)} rows. Columns: {list(raw_price.columns)}")
        if all(c in raw_price.columns for c in ['product_code', 'unit_price', 'effective_from', 'effective_to']):
            report.append("- ✅ **PASS**: product_price has required effective date columns.")
        else:
            report.append("- ⚠️ **WARNING**: product_price might be missing some effective date columns.")
    else:
        report.append("- ⚠️ **WARNING**: `product_price.csv` not found.")
        
    if raw_fact is not None:
        if 'unit_price' in raw_fact.columns and 'quantity' in raw_fact.columns and 'line_total' in raw_fact.columns:
            computed = raw_fact['quantity'] * raw_fact['unit_price']
            diff = (raw_fact['line_total'] - computed).abs()
            max_diff = diff.max()
            report.append(f"- `fact_sales.csv`: Max diff between `line_total` and `qty * unit_price`: {max_diff:.2f}")
            if max_diff < 1000:
                report.append("- ✅ **PASS**: line_total is approx quantity * unit_price.")
            else:
                report.append("- ❌ **FAIL**: Large discrepancy between line_total and qty * unit_price.")
    report.append("")
    
    # Write report
    report_path = os.path.join(OUTPUT_DIR, "phase3_data_audit_report.md")
    with open(report_path, "w", encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"Phase 3A Data Audit complete. Report saved to {report_path}")

if __name__ == "__main__":
    run_phase3a_audit()
