import pandas as pd
import numpy as np
import os
import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from src.models.forecasting.shared.config.paths import RAW_DATA_DIR, INTERIM_DATA_DIR, METADATA_DIR

# ============================================================
# CONSTANTS & CONFIG
# ============================================================
RAW_DIR = RAW_DATA_DIR
INTERIM_DIR = INTERIM_DATA_DIR
METADATA_DIR = METADATA_DIR
AUDIT_DIR = "outputs/audit"

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

def assign_block(row):
    """
    Block A: Q1/2025 (months 1,2,3)
    Block B: Q1/2026 (months 1,2,3)
    Gap: Apr-Dec 2025
    """
    fy = row['fiscal_year']
    fm = row['fiscal_month']
    if fy == 2025 and fm in [1,2,3]:
        return 'A'
    elif fy == 2026 and fm in [1,2,3]:
        return 'B'
    else:
        return 'GAP'

def assign_period_month(row):
    """
    period_month = absolute calendar index
    1 = Jan25, 2 = Feb25, 3 = Mar25
    13 = Jan26, 14 = Feb26, 15 = Mar26
    """
    fy = row['fiscal_year']
    fm = row['fiscal_month']
    if fy == 2025 and fm == 1: return 1
    elif fy == 2025 and fm == 2: return 2
    elif fy == 2025 and fm == 3: return 3
    elif fy == 2026 and fm == 1: return 13
    elif fy == 2026 and fm == 2: return 14
    elif fy == 2026 and fm == 3: return 15
    else: return np.nan

def clean_id(pid):
    try:
        if pd.isna(pid):
            return pid
        return str(int(float(pid)))
    except:
        return str(pid)

def main():
    ensure_dir(INTERIM_DIR)
    ensure_dir(AUDIT_DIR)
    
    print("Loading raw data...")
    # Read fact_sales
    dtypes = {
        'product_code': str,
        'customer_code': str,
        'so_number': str,
        'invoice_number': str,
        'message_id': str,
        'line_id_fk': str,
        'province_id': str
    }
    df_raw = pd.read_csv(os.path.join(RAW_DIR, 'fact_sales.csv'), dtype=dtypes)
    df_raw['order_date'] = pd.to_datetime(df_raw['order_date'])
    
    total_qty_raw = df_raw['quantity'].sum()
    total_rev_raw = df_raw['line_total'].sum()
    
    # Read metadata
    print("Loading metadata...")
    product_meta = pd.read_parquet(os.path.join(METADATA_DIR, 'product_metadata.parquet'))
    province_clean = pd.read_csv(os.path.join(RAW_DIR, 'province_clean.csv'), dtype={'province_id': str})
    
    # Pre-process IDs for merge
    df_raw['clean_province_id_fk'] = df_raw['province_id'].apply(clean_id)
    province_clean['clean_province_id'] = province_clean['province_id'].apply(clean_id)
    
    print("Merging metadata...")
    # Province Merge
    df_raw = df_raw.merge(
        province_clean[['clean_province_id', 'province_name_clean', 'region_clean']], 
        left_on='clean_province_id_fk', 
        right_on='clean_province_id', 
        how='left'
    )
    
    # Product Merge
    if 'base_color' in df_raw.columns:
        df_raw = df_raw.drop(columns=['base_color'])
        
    meta_cols = ['product_code', 'base_color', 'group_code_clean', 'group_name_clean', 'line_id_clean', 'line_name_clean']
    df_raw = df_raw.merge(product_meta[meta_cols], on='product_code', how='left')
    
    # Verify no data loss
    if df_raw['quantity'].sum() != total_qty_raw or df_raw['line_total'].sum() != total_rev_raw:
        raise ValueError("DATA LOSS detected after merging metadata!")
    
    if len(df_raw) != 25754:
        raise ValueError("Row count changed after merging metadata!")
        
    print("Data validation successful. No data loss.")
    
    # ============================================================
    # MONTHLY AGGREGATION
    # ============================================================
    print("\nBuilding monthly aggregation...")
    
    # Median prices
    median_prices_m = df_raw.groupby(
        ['product_code', 'fiscal_year', 'fiscal_month']
    )['unit_price'].median().reset_index().rename(columns={'unit_price': 'median_unit_price'})
    
    monthly = df_raw.groupby(
        ['product_code', 'product_name', 'base_color', 'group_code_clean', 'group_name_clean',
         'line_id_clean', 'line_name_clean', 'fiscal_year', 'fiscal_month'],
        dropna=False
    ).agg(
        total_quantity=('quantity', 'sum'),
        total_revenue=('line_total', 'sum'),
        n_orders=('so_number', 'nunique'),
        n_transactions=('fact_id', 'count'),
        n_dealers=('customer_code', 'nunique'),
        n_provinces=('province_name_clean', 'nunique'),
        n_regions=('region_clean', 'nunique')
    ).reset_index()
    
    monthly = monthly.merge(median_prices_m, on=['product_code', 'fiscal_year', 'fiscal_month'], how='left')
    
    # Additional logic
    monthly['block_id'] = monthly.apply(assign_block, axis=1)
    monthly['period_month'] = monthly.apply(assign_period_month, axis=1)
    monthly['implied_price'] = monthly['total_revenue'] / monthly['total_quantity']
    
    # Check totals
    if abs(monthly['total_quantity'].sum() - total_qty_raw) > 1:
        raise ValueError(f"Monthly quantity mismatch: {monthly['total_quantity'].sum()} vs {total_qty_raw}")
    if abs(monthly['total_revenue'].sum() - total_rev_raw) > 1:
        raise ValueError(f"Monthly revenue mismatch: {monthly['total_revenue'].sum()} vs {total_rev_raw}")
        
    monthly.to_parquet(os.path.join(INTERIM_DIR, 'fact_sales_monthly.parquet'), index=False)
    
    # Output Summary
    monthly_summary = monthly.groupby(['fiscal_year', 'fiscal_month']).agg(
        n_skus=('product_code', 'nunique'),
        sum_qty=('total_quantity', 'sum'),
        sum_rev=('total_revenue', 'sum'),
    ).reset_index()
    monthly_summary.to_csv(os.path.join(AUDIT_DIR, 'fact_sales_monthly_summary.csv'), index=False)
    print(f"Saved fact_sales_monthly.parquet ({len(monthly)} rows)")
    
    # ============================================================
    # WEEKLY AGGREGATION
    # ============================================================
    print("\nBuilding weekly aggregation...")
    df_raw['iso_year'] = df_raw['order_date'].dt.isocalendar().year.astype(int)
    df_raw['iso_week'] = df_raw['order_date'].dt.isocalendar().week.astype(int)
    
    df_raw['week_start_date'] = df_raw['order_date'] - pd.to_timedelta(df_raw['order_date'].dt.weekday, unit='D')
    df_raw['week_end_date'] = df_raw['week_start_date'] + pd.Timedelta(days=6)
    df_raw['year_week'] = df_raw['iso_year'].astype(str) + '-W' + df_raw['iso_week'].astype(str).str.zfill(2)
    
    median_prices_w = df_raw.groupby(
        ['product_code', 'year_week', 'fiscal_month']
    )['unit_price'].median().reset_index().rename(columns={'unit_price': 'median_unit_price'})
    
    weekly = df_raw.groupby(
        ['product_code', 'product_name', 'base_color', 'group_code_clean', 'group_name_clean',
         'line_id_clean', 'line_name_clean', 'iso_year', 'iso_week', 'year_week', 
         'week_start_date', 'week_end_date', 'fiscal_year', 'fiscal_month'],
        dropna=False
    ).agg(
        total_quantity=('quantity', 'sum'),
        total_revenue=('line_total', 'sum'),
        n_orders=('so_number', 'nunique'),
        n_transactions=('fact_id', 'count'),
        n_dealers=('customer_code', 'nunique'),
        n_provinces=('province_name_clean', 'nunique'),
        n_regions=('region_clean', 'nunique')
    ).reset_index()
    
    weekly = weekly.merge(median_prices_w, on=['product_code', 'year_week', 'fiscal_month'], how='left')
    
    weekly['block_id'] = weekly.apply(assign_block, axis=1)
    weekly['period_month'] = weekly.apply(assign_period_month, axis=1)
    weekly['implied_price'] = weekly['total_revenue'] / weekly['total_quantity']
    
    # Compute period_week
    week_order = weekly[['iso_year', 'iso_week']].drop_duplicates().sort_values(['iso_year', 'iso_week']).reset_index(drop=True)
    # Absolute week index: weeks since start of 2025
    week_order['period_week'] = (week_order['iso_year'] - 2025) * 52 + week_order['iso_week']
    weekly = weekly.merge(week_order, on=['iso_year', 'iso_week'], how='left')
    
    if abs(weekly['total_quantity'].sum() - total_qty_raw) > 1:
        raise ValueError(f"Weekly quantity mismatch: {weekly['total_quantity'].sum()} vs {total_qty_raw}")
    if abs(weekly['total_revenue'].sum() - total_rev_raw) > 1:
        raise ValueError(f"Weekly revenue mismatch: {weekly['total_revenue'].sum()} vs {total_rev_raw}")
        
    weekly.to_parquet(os.path.join(INTERIM_DIR, 'fact_sales_weekly.parquet'), index=False)
    
    weekly_summary = weekly.groupby(['fiscal_year', 'fiscal_month', 'year_week']).agg(
        n_skus=('product_code', 'nunique'),
        sum_qty=('total_quantity', 'sum'),
        sum_rev=('total_revenue', 'sum'),
    ).reset_index()
    weekly_summary.to_csv(os.path.join(AUDIT_DIR, 'fact_sales_weekly_summary.csv'), index=False)
    print(f"Saved fact_sales_weekly.parquet ({len(weekly)} rows)")
    
    # Weekly to Monthly reconciliation by period_month
    print("\nVerifying Weekly-to-Monthly Reconciliation by period_month...")
    w_sum = weekly.groupby('period_month')['total_quantity'].sum().reset_index()
    m_sum = monthly.groupby('period_month')['total_quantity'].sum().reset_index()
    check = w_sum.merge(m_sum, on='period_month', suffixes=('_weekly', '_monthly'))
    check['diff'] = abs(check['total_quantity_weekly'] - check['total_quantity_monthly'])
    if check['diff'].max() > 1:
        print("❌ FAILED: Weekly sum by period_month does NOT match Monthly sum!")
        print(check[check['diff'] > 1])
    else:
        print("✅ PASS: Weekly aggregate matches Monthly aggregate exactly by period_month.")
        
    print("\nAll Phase 1C aggregations rebuilt and verified successfully.")

if __name__ == '__main__':
    main()
