"""
Phase 1C Verification Script
Checks if fact_sales_monthly.parquet and fact_sales_weekly.parquet
already contain all Phase 1C changes.
"""
import pandas as pd
import numpy as np
import os
import sys

INTERIM = "data/interim"
RAW = "data/raw"

results = []

def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, status, detail))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

def main():
    # ---- Load files ----
    monthly_path = os.path.join(INTERIM, "fact_sales_monthly.parquet")
    weekly_path = os.path.join(INTERIM, "fact_sales_weekly.parquet")
    raw_path = os.path.join(RAW, "fact_sales.csv")

    if not os.path.exists(monthly_path):
        print(f"FATAL: {monthly_path} NOT FOUND. You need to run build_phase1c_aggregations.py first.")
        sys.exit(1)
    if not os.path.exists(weekly_path):
        print(f"FATAL: {weekly_path} NOT FOUND. You need to run build_phase1c_aggregations.py first.")
        sys.exit(1)

    monthly = pd.read_parquet(monthly_path)
    weekly = pd.read_parquet(weekly_path)
    raw = pd.read_csv(raw_path, dtype={"product_code": str})

    raw_qty = raw["quantity"].sum()
    raw_rev = raw["line_total"].sum()

    print(f"Monthly parquet: {len(monthly)} rows, cols: {sorted(monthly.columns.tolist())}")
    print(f"Weekly parquet:  {len(weekly)} rows, cols: {sorted(weekly.columns.tolist())}")
    print(f"Raw fact_sales:  {len(raw)} rows, qty={raw_qty:,.0f}, rev={raw_rev:,.0f}")
    print()

    # ================================================================
    # 1. Column existence checks
    # ================================================================
    print("=" * 60)
    print("1. COLUMN EXISTENCE CHECKS")
    print("=" * 60)

    for col in ["base_color", "group_code_clean", "group_name_clean",
                "line_id_clean", "line_name_clean"]:
        check(f"monthly has '{col}'", col in monthly.columns)
        check(f"weekly has '{col}'", col in weekly.columns)

    for col in ["province_name_clean", "region_clean"]:
        check(f"monthly has '{col}'", col in monthly.columns)
        check(f"weekly has '{col}'", col in weekly.columns)

    print()

    # ================================================================
    # 2. Quantity / Revenue reconciliation
    # ================================================================
    print("=" * 60)
    print("2. QUANTITY / REVENUE RECONCILIATION")
    print("=" * 60)

    m_qty = monthly["total_quantity"].sum()
    m_rev = monthly["total_revenue"].sum()
    w_qty = weekly["total_quantity"].sum()
    w_rev = weekly["total_revenue"].sum()

    check("monthly qty == raw qty",
          abs(m_qty - raw_qty) < 1,
          f"monthly={m_qty:,.0f} vs raw={raw_qty:,.0f}")
    check("monthly rev == raw rev",
          abs(m_rev - raw_rev) < 1,
          f"monthly={m_rev:,.0f} vs raw={raw_rev:,.0f}")
    check("weekly qty == raw qty",
          abs(w_qty - raw_qty) < 1,
          f"weekly={w_qty:,.0f} vs raw={raw_qty:,.0f}")
    check("weekly rev == raw rev",
          abs(w_rev - raw_rev) < 1,
          f"weekly={w_rev:,.0f} vs raw={raw_rev:,.0f}")

    print()

    # ================================================================
    # 3. Weekly -> Monthly reconciliation by period_month
    # ================================================================
    print("=" * 60)
    print("3. WEEKLY -> MONTHLY RECONCILIATION BY PERIOD_MONTH")
    print("=" * 60)

    if "period_month" in monthly.columns and "period_month" in weekly.columns:
        w_pm = weekly.groupby("period_month")["total_quantity"].sum().reset_index()
        m_pm = monthly.groupby("period_month")["total_quantity"].sum().reset_index()
        merged = w_pm.merge(m_pm, on="period_month", suffixes=("_w", "_m"))
        merged["diff"] = abs(merged["total_quantity_w"] - merged["total_quantity_m"])
        max_diff = merged["diff"].max()
        check("weekly sum by period_month == monthly",
              max_diff < 1,
              f"max diff = {max_diff}")
        for _, r in merged.iterrows():
            pm = r["period_month"]
            print(f"    period_month {pm}: weekly={r['total_quantity_w']:,.0f}  monthly={r['total_quantity_m']:,.0f}  diff={r['diff']:,.0f}")
    else:
        check("period_month exists", False, "column missing in monthly or weekly")

    print()

    # ================================================================
    # 4. UNKNOWN hierarchy handling
    # ================================================================
    print("=" * 60)
    print("4. UNKNOWN HIERARCHY HANDLING")
    print("=" * 60)

    if "group_code_clean" in monthly.columns:
        unknown_m = monthly[monthly["group_code_clean"] == "UNKNOWN"]
        unknown_skus = unknown_m["product_code"].nunique()
        unknown_rev = unknown_m["total_revenue"].sum()
        unknown_pct = unknown_rev / m_rev * 100 if m_rev else 0

        check("UNKNOWN SKU count == 55",
              unknown_skus == 55,
              f"found {unknown_skus}")
        check("UNKNOWN revenue share ~ 12.9%",
              abs(unknown_pct - 12.9) < 1.0,
              f"actual = {unknown_pct:.2f}%")

        # Ensure no rows were dropped for UNKNOWN
        check("group_code_clean has no NaN (all mapped or UNKNOWN)",
              monthly["group_code_clean"].isna().sum() == 0,
              f"NaN count = {monthly['group_code_clean'].isna().sum()}")
    else:
        check("group_code_clean exists for UNKNOWN check", False)

    print()

    # ================================================================
    # 5. base_color populated
    # ================================================================
    print("=" * 60)
    print("5. BASE_COLOR CHECK")
    print("=" * 60)

    if "base_color" in monthly.columns:
        n_base_colors = monthly["base_color"].nunique()
        na_count = monthly["base_color"].isna().sum()
        check("base_color has values",
              n_base_colors > 0,
              f"{n_base_colors} unique base_colors, {na_count} NaN")
    else:
        check("base_color column exists", False)

    if "base_color" in weekly.columns:
        n_base_colors_w = weekly["base_color"].nunique()
        na_count_w = weekly["base_color"].isna().sum()
        check("weekly base_color has values",
              n_base_colors_w > 0,
              f"{n_base_colors_w} unique base_colors, {na_count_w} NaN")
    else:
        check("weekly base_color column exists", False)

    print()

    # ================================================================
    # 6. Province clean check
    # ================================================================
    print("=" * 60)
    print("6. PROVINCE CLEAN CHECK")
    print("=" * 60)

    if "province_name_clean" in monthly.columns:
        prov_na = monthly["province_name_clean"].isna().sum()
        n_provs = monthly["province_name_clean"].nunique()
        check("province_name_clean populated",
              n_provs > 0,
              f"{n_provs} unique provinces, {prov_na} NaN rows")
    if "region_clean" in monthly.columns:
        reg_na = monthly["region_clean"].isna().sum()
        n_regs = monthly["region_clean"].nunique()
        check("region_clean populated",
              n_regs > 0,
              f"{n_regs} unique regions, {reg_na} NaN rows")

    # ================================================================
    # SUMMARY
    # ================================================================
    print()
    print("=" * 60)
    total = len(results)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"SUMMARY: {passed}/{total} PASSED, {failed} FAILED")
    if failed == 0:
        print("All checks PASSED! Parquet files are ready for Phase 2.")
    else:
        print("Some checks FAILED. You may need to re-run build_phase1c_aggregations.py.")
    print("=" * 60)

if __name__ == "__main__":
    main()
