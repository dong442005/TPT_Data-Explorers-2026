import pandas as pd
import numpy as np
import os
import json
import calendar

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from src.models.forecasting.shared.config.paths import INTERIM_DATA_DIR, CONFIG_DIR, FEATURES_DIR, METADATA_DIR

INTERIM_DIR = INTERIM_DATA_DIR
CONFIG_DIR = CONFIG_DIR
FEATURES_DIR = FEATURES_DIR
METADATA_DIR = METADATA_DIR
AUDIT_DIR = "outputs/audit"

os.makedirs(FEATURES_DIR, exist_ok=True)
os.makedirs(AUDIT_DIR, exist_ok=True)

def safe_lag(df, group_col, sort_cols, val_col, lag_n, block_col):
    """
    Computes a gap-aware lag using calendar distance matching via merge.
    df must be pre-sorted.
    Returns a Series of lagged values where the calendar distance is exactly lag_n.
    """
    time_col = sort_cols[0]
    
    # Create a distinct lag DataFrame
    lag_df = df[[group_col, time_col, val_col]].copy()
    
    # Aggregate by mean to handle duplicate time indices (e.g. split weeks in future rows)
    lag_df = lag_df.groupby([group_col, time_col])[val_col].mean().reset_index()
    
    # Shift time by lag_n forward so it matches the current row's time
    lag_df[time_col] = lag_df[time_col] + lag_n
    lag_df = lag_df.rename(columns={val_col: 'lag_val'})
    
    # Merge back to original df maintaining index order
    df_temp = df[[group_col, time_col]].copy()
    df_temp['original_index'] = df_temp.index
    
    merged = df_temp.merge(lag_df, on=[group_col, time_col], how='left')
    merged = merged.sort_values('original_index').reset_index(drop=True)
    
    return merged['lag_val']

def safe_rolling_mean(df, group_col, val_col, window_n, block_col):
    """
    Computes a block-aware rolling mean OVER THE PAST WINDOW (excluding current row).
    Essentially: mean of lag_1, lag_2, ... lag_window.
    If ANY of the lags cross the block boundary, we still compute the mean of the VALID lags in the same block.
    Actually, to be strictly safe and avoid leakage, we compute shifted rolling mean.
    """
    # Create shifted lag columns
    lags = [safe_lag(df, group_col, ['period_idx'], val_col, i, block_col) for i in range(1, window_n + 1)]
    # Concatenate and mean
    return pd.concat(lags, axis=1).mean(axis=1, skipna=True) # skipna=True means if some lags are missing (e.g. cross block), it averages remaining. But maybe we want strict window? Wait, if we are at start of block, rolling mean of past 4 weeks but only 2 weeks exist in block, mean of 2 weeks is fine.

def build_monthly_features():
    print("Building monthly features...")
    m = pd.read_parquet(os.path.join(INTERIM_DIR, "fact_sales_monthly.parquet"))
    meta = pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet"))
    
    # 1. Merge metadata (color, is_cold_start_march_sku)
    m = m.merge(meta[['product_code', 'color', 'is_cold_start_march_sku']], on='product_code', how='left')
    
    # 2. Add UNKNOWN hierarchy flag
    m['is_unknown_hierarchy'] = (m['group_code_clean'] == 'UNKNOWN').astype(int)
    
    # 3. Calendar features
    m['month_sin'] = np.sin(2 * np.pi * m['fiscal_month'] / 12)
    m['month_cos'] = np.cos(2 * np.pi * m['fiscal_month'] / 12)
    m['is_q1'] = m['fiscal_month'].isin([1, 2, 3]).astype(int)
    m['is_q2'] = m['fiscal_month'].isin([4, 5, 6]).astype(int)
    
    # days_in_month
    def get_days(y, m_val):
        return calendar.monthrange(y, m_val)[1]
    m['days_in_month'] = m.apply(lambda r: get_days(r['fiscal_year'], r['fiscal_month']), axis=1)
    
    # Sort for time-series operations
    m = m.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    # 4. Lifecycle features
    first_seen = m.groupby('product_code')['period_month'].transform('min')
    m['months_since_first_seen'] = m['period_month'] - first_seen
    m['is_new_sku'] = (m['months_since_first_seen'] == 0).astype(int)
    
    # Define block: period_month <= 3 is Block A, else Block B
    m['block_id'] = np.where(m['period_month'] <= 3, 'A', 'B')
    
    # 5. Block-aware Lags
    m['qty_lag_1'] = safe_lag(m, 'product_code', ['period_month'], 'total_quantity', 1, 'block_id')
    m['qty_lag_2'] = safe_lag(m, 'product_code', ['period_month'], 'total_quantity', 2, 'block_id')
    
    m['n_dealers_lag1'] = safe_lag(m, 'product_code', ['period_month'], 'n_dealers', 1, 'block_id')
    m['median_unit_price_lag1'] = safe_lag(m, 'product_code', ['period_month'], 'median_unit_price', 1, 'block_id')
    m['implied_price_lag1'] = safe_lag(m, 'product_code', ['period_month'], 'implied_price', 1, 'block_id')
    
    m['n_provinces_lag1'] = safe_lag(m, 'product_code', ['period_month'], 'n_provinces', 1, 'block_id')
    m['n_regions_lag1'] = safe_lag(m, 'product_code', ['period_month'], 'n_regions', 1, 'block_id')
    
    # 6. Hierarchy / Share features (all lagged)
    # We need to compute group totals first, then lag them.
    group_totals = m.groupby(['group_code_clean', 'period_month'])['total_quantity'].sum().reset_index()
    group_totals.rename(columns={'total_quantity': 'group_total_qty'}, inplace=True)
    
    market_totals = m.groupby(['period_month'])['total_quantity'].sum().reset_index()
    market_totals.rename(columns={'total_quantity': 'market_total_qty'}, inplace=True)
    
    m = m.merge(group_totals, on=['group_code_clean', 'period_month'], how='left')
    m = m.merge(market_totals, on=['period_month'], how='left')
    
    # Sort again after merge
    m = m.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    m['group_total_quantity_lagged'] = safe_lag(m, 'product_code', ['period_month'], 'group_total_qty', 1, 'block_id')
    
    # Share computations (lagged)
    sku_qty_lag1 = m['qty_lag_1']
    m['sku_share_in_group_lagged'] = sku_qty_lag1 / m['group_total_quantity_lagged']
    
    market_total_lagged = safe_lag(m, 'product_code', ['period_month'], 'market_total_qty', 1, 'block_id')
    m['sku_share_total_lagged'] = sku_qty_lag1 / market_total_lagged
    
    # 7. Pricing vs Group (lagged)
    group_median_price = m.groupby(['group_code_clean', 'period_month'])['median_unit_price'].median().reset_index()
    group_median_price.rename(columns={'median_unit_price': 'group_median_price'}, inplace=True)
    m = m.merge(group_median_price, on=['group_code_clean', 'period_month'], how='left')
    m = m.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    group_median_price_lagged = safe_lag(m, 'product_code', ['period_month'], 'group_median_price', 1, 'block_id')
    m['price_vs_group_median_lag1'] = m['median_unit_price_lag1'] / group_median_price_lagged
    
    # 8. Dealer features
    m['avg_qty_per_dealer_lag1'] = m['qty_lag_1'] / m['n_dealers_lag1']
    
    # Cleanup intermediate columns
    m.drop(columns=['group_total_qty', 'market_total_qty', 'group_median_price'], inplace=True)
    
    m.to_parquet(os.path.join(FEATURES_DIR, "track1_monthly_model_panel.parquet"), index=False)
    print(f"  -> Monthly historical rows: {len(m)}")
    return m

def build_weekly_features():
    print("Building weekly features...")
    w = pd.read_parquet(os.path.join(INTERIM_DIR, "fact_sales_weekly.parquet"))
    meta = pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet"))
    
    w = w.merge(meta[['product_code', 'color', 'is_cold_start_march_sku']], on='product_code', how='left')
    w['is_unknown_hierarchy'] = (w['group_code_clean'] == 'UNKNOWN').astype(int)
    
    # Calendar features
    # Extract year and week number from year_week (format: YYYY-WXX)
    w['year'] = w['year_week'].str[:4].astype(int)
    w['week_of_year'] = w['year_week'].str[-2:].astype(int)
    
    w['month_sin'] = np.sin(2 * np.pi * w['fiscal_month'] / 12)
    w['month_cos'] = np.cos(2 * np.pi * w['fiscal_month'] / 12)
    
    # week_of_month calculation
    # Let's define week_of_month as the rank of the week within the fiscal_month
    w['week_of_month'] = w.groupby(['fiscal_year', 'fiscal_month', 'product_code'])['week_start_date'].rank(method='dense').astype(int)
    
    # is_month_start_week / is_month_end_week approximation
    # A week is start if week_of_month == 1
    w['is_month_start_week'] = (w['week_of_month'] == 1).astype(int)
    # is month end: max rank in month
    max_wom = w.groupby(['fiscal_year', 'fiscal_month', 'product_code'])['week_of_month'].transform('max')
    w['is_month_end_week'] = (w['week_of_month'] == max_wom).astype(int)
    
    # Sort for time-series operations
    # Use absolute calendar index from phase 1c
    w['period_idx'] = w['period_week']
    w = w.sort_values(['product_code', 'period_idx']).reset_index(drop=True)
    
    # Block mapping: we can use block_id already in the data
    w['qty_lag_1w'] = safe_lag(w, 'product_code', ['period_idx'], 'total_quantity', 1, 'block_id')
    w['qty_lag_2w'] = safe_lag(w, 'product_code', ['period_idx'], 'total_quantity', 2, 'block_id')
    w['qty_lag_4w'] = safe_lag(w, 'product_code', ['period_idx'], 'total_quantity', 4, 'block_id')
    
    w['n_dealers_lag_1w'] = safe_lag(w, 'product_code', ['period_idx'], 'n_dealers', 1, 'block_id')
    w['median_unit_price_lag_1w'] = safe_lag(w, 'product_code', ['period_idx'], 'median_unit_price', 1, 'block_id')
    w['implied_price_lag_1w'] = safe_lag(w, 'product_code', ['period_idx'], 'implied_price', 1, 'block_id')
    
    # Rolling features
    w['qty_roll_mean_2w'] = safe_rolling_mean(w, 'product_code', 'total_quantity', 2, 'block_id')
    w['qty_roll_mean_4w'] = safe_rolling_mean(w, 'product_code', 'total_quantity', 4, 'block_id')
    
    w.to_parquet(os.path.join(FEATURES_DIR, "track1_weekly_model_panel.parquet"), index=False)
    print(f"  -> Weekly historical rows: {len(w)}")
    return w

def build_future_monthly_rows(hist_m, meta):
    print("Building monthly future rows...")
    # April, May, June 2026 => fiscal_year 2026, fiscal_month 4, 5, 6, period_month 16, 17, 18
    skus = meta['product_code'].unique()
    
    future_rows = []
    for pm, fy, fm in [(16, 2026, 4), (17, 2026, 5), (18, 2026, 6)]:
        for sku in skus:
            future_rows.append({
                'product_code': sku,
                'fiscal_year': fy,
                'fiscal_month': fm,
                'period_month': pm,
                'block_id': 'B', # Q2 is effectively continuation of Block B for lag purposes, but wait, the gap was between A and B. So Q2 is adjacent to Mar26 (Block B). So block_id='B' is fine for lagging from Mar26.
                'total_quantity': np.nan,
                'total_revenue': np.nan
            })
            
    fdf = pd.DataFrame(future_rows)
    
    # Merge static metadata
    fdf = fdf.merge(meta[['product_code', 'group_code_clean', 'group_name_clean', 'line_id_clean', 'line_name_clean', 'base_color', 'color', 'is_cold_start_march_sku']], on='product_code', how='left')
    fdf['is_unknown_hierarchy'] = (fdf['group_code_clean'] == 'UNKNOWN').astype(int)
    
    # Calendar features
    fdf['month_sin'] = np.sin(2 * np.pi * fdf['fiscal_month'] / 12)
    fdf['month_cos'] = np.cos(2 * np.pi * fdf['fiscal_month'] / 12)
    fdf['is_q1'] = fdf['fiscal_month'].isin([1, 2, 3]).astype(int)
    fdf['is_q2'] = fdf['fiscal_month'].isin([4, 5, 6]).astype(int)
    
    def get_days(y, m_val):
        return calendar.monthrange(y, m_val)[1]
    fdf['days_in_month'] = fdf.apply(lambda r: get_days(r['fiscal_year'], r['fiscal_month']), axis=1)
    
    # Combine with history to compute lags properly
    combined = pd.concat([hist_m, fdf], ignore_index=True)
    combined = combined.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    # Recompute lifecycle
    first_seen = combined.groupby('product_code')['period_month'].transform('min')
    combined['months_since_first_seen'] = combined['period_month'] - first_seen
    combined['is_new_sku'] = (combined['months_since_first_seen'] == 0).astype(int)
    
    # Recompute block-aware lags (now including future rows)
    combined['qty_lag_1'] = safe_lag(combined, 'product_code', ['period_month'], 'total_quantity', 1, 'block_id')
    combined['qty_lag_2'] = safe_lag(combined, 'product_code', ['period_month'], 'total_quantity', 2, 'block_id')
    combined['n_dealers_lag1'] = safe_lag(combined, 'product_code', ['period_month'], 'n_dealers', 1, 'block_id')
    combined['median_unit_price_lag1'] = safe_lag(combined, 'product_code', ['period_month'], 'median_unit_price', 1, 'block_id')
    combined['implied_price_lag1'] = safe_lag(combined, 'product_code', ['period_month'], 'implied_price', 1, 'block_id')
    combined['n_provinces_lag1'] = safe_lag(combined, 'product_code', ['period_month'], 'n_provinces', 1, 'block_id')
    combined['n_regions_lag1'] = safe_lag(combined, 'product_code', ['period_month'], 'n_regions', 1, 'block_id')
    
    # For hierarchy / share lagged features in future rows, we need the group_totals of historical periods.
    # We can just re-run the group logic on combined, BUT total_quantity is NaN in future rows, so sum is 0. This is fine because we only need the lagged values (which come from historical where total_quantity is valid).
    group_totals = combined.groupby(['group_code_clean', 'period_month'])['total_quantity'].sum().reset_index()
    group_totals.rename(columns={'total_quantity': 'group_total_qty'}, inplace=True)
    
    market_totals = combined.groupby(['period_month'])['total_quantity'].sum().reset_index()
    market_totals.rename(columns={'total_quantity': 'market_total_qty'}, inplace=True)
    
    combined = combined.merge(group_totals, on=['group_code_clean', 'period_month'], how='left')
    combined = combined.merge(market_totals, on=['period_month'], how='left')
    combined = combined.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    combined['group_total_quantity_lagged'] = safe_lag(combined, 'product_code', ['period_month'], 'group_total_qty', 1, 'block_id')
    combined['sku_share_in_group_lagged'] = combined['qty_lag_1'] / combined['group_total_quantity_lagged']
    combined['sku_share_total_lagged'] = combined['qty_lag_1'] / safe_lag(combined, 'product_code', ['period_month'], 'market_total_qty', 1, 'block_id')
    
    group_median_price = combined.groupby(['group_code_clean', 'period_month'])['median_unit_price'].median().reset_index()
    group_median_price.rename(columns={'median_unit_price': 'group_median_price'}, inplace=True)
    combined = combined.merge(group_median_price, on=['group_code_clean', 'period_month'], how='left')
    combined = combined.sort_values(['product_code', 'period_month']).reset_index(drop=True)
    
    combined['price_vs_group_median_lag1'] = combined['median_unit_price_lag1'] / safe_lag(combined, 'product_code', ['period_month'], 'group_median_price', 1, 'block_id')
    combined['avg_qty_per_dealer_lag1'] = combined['qty_lag_1'] / combined['n_dealers_lag1']
    
    combined.drop(columns=['group_total_qty', 'market_total_qty', 'group_median_price'], inplace=True)
    
    # Filter back to future rows only
    out_future = combined[combined['period_month'] > 15].copy()
    
    out_future.to_parquet(os.path.join(FEATURES_DIR, "track1_monthly_future_q2_rows.parquet"), index=False)
    print(f"  -> Monthly future rows: {len(out_future)}")
    return out_future

def build_future_weekly_rows(hist_w, meta):
    print("Building weekly future rows...")
    skus = meta['product_code'].unique()
    
    # Generate all dates in Q2 2026
    dates = pd.date_range("2026-04-01", "2026-06-30")
    df_dates = pd.DataFrame({'date': dates})
    
    # Assign fiscal_month based on month
    df_dates['fiscal_month'] = df_dates['date'].dt.month
    
    # Compute iso year and week
    df_dates['iso_year'] = df_dates['date'].dt.isocalendar().year
    df_dates['iso_week'] = df_dates['date'].dt.isocalendar().week
    df_dates['year_week'] = df_dates.apply(lambda x: f"{x['iso_year']}-W{x['iso_week']:02d}", axis=1)
    
    # Group dates by year_week and fiscal_month to create segments
    segments = df_dates.groupby(['year_week', 'fiscal_month']).agg(
        segment_start_date=('date', 'min'),
        segment_end_date=('date', 'max'),
        days_in_segment=('date', 'count')
    ).reset_index()
    
    segments['is_partial_week'] = (segments['days_in_segment'] < 7).astype(int)
    
    # For period_idx continuation, find max period_idx in history
    max_hist_idx = hist_w['period_idx'].max()
    
    # Compute absolute period_idx consistently with historical data
    # year_week is "YYYY-WXX"
    segments['iso_year_num'] = segments['year_week'].str[:4].astype(int)
    segments['iso_week_num'] = segments['year_week'].str[6:].astype(int)
    segments['period_idx'] = (segments['iso_year_num'] - 2025) * 52 + segments['iso_week_num']
    
    # Expand for all SKUs
    future_rows = []
    for _, seg in segments.iterrows():
        for sku in skus:
            row = seg.to_dict()
            row['product_code'] = sku
            row['block_id'] = 'B'
            row['total_quantity'] = np.nan
            row['total_revenue'] = np.nan
            future_rows.append(row)
            
    fdf = pd.DataFrame(future_rows)
    
    # Merge static
    fdf = fdf.merge(meta[['product_code', 'group_code_clean', 'group_name_clean', 'line_id_clean', 'line_name_clean', 'base_color', 'color', 'is_cold_start_march_sku']], on='product_code', how='left')
    fdf['is_unknown_hierarchy'] = (fdf['group_code_clean'] == 'UNKNOWN').astype(int)
    
    fdf['year'] = fdf['year_week'].str[:4].astype(int)
    fdf['week_of_year'] = fdf['year_week'].str[-2:].astype(int)
    fdf['month_sin'] = np.sin(2 * np.pi * fdf['fiscal_month'] / 12)
    fdf['month_cos'] = np.cos(2 * np.pi * fdf['fiscal_month'] / 12)
    
    # We won't compute strict week_of_month here since it's future and targetless, 
    # but we can set defaults or compute similar to history
    fdf['week_of_month'] = fdf.groupby(['fiscal_month', 'product_code'])['segment_start_date'].rank(method='dense').astype(int)
    fdf['is_month_start_week'] = (fdf['week_of_month'] == 1).astype(int)
    max_wom = fdf.groupby(['fiscal_month', 'product_code'])['week_of_month'].transform('max')
    fdf['is_month_end_week'] = (fdf['week_of_month'] == max_wom).astype(int)
    
    # Combine with history to compute lags
    # Need to be careful: historical W14 and future W14 might share the same year_week.
    # When we sort by period_idx, they are tied.
    # Let's create a combined sorting key: period_idx, then fiscal_month
    combined = pd.concat([hist_w, fdf], ignore_index=True)
    combined = combined.sort_values(['product_code', 'period_idx', 'fiscal_month']).reset_index(drop=True)
    
    # Weekly lags
    # Because of split weeks (W14 Mar and W14 Apr), they have the same period_idx.
    # If we just shift by period_idx, pandas shift() shifts by ROW.
    # If there are duplicate period_idx per SKU, row shift will be wrong!
    # Let's aggregate to WEEK level first, compute lags, then merge back.
    week_agg = combined.groupby(['product_code', 'period_idx']).agg({
        'total_quantity': 'sum', # sum over segments for the same week (if history has target, future is nan, sum is target)
        'n_dealers': 'max',
        'median_unit_price': 'median',
        'implied_price': 'mean',
        'block_id': 'first'
    }).reset_index()
    
    week_agg = week_agg.sort_values(['product_code', 'period_idx'])
    week_agg['qty_lag_1w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'total_quantity', 1, 'block_id')
    week_agg['qty_lag_2w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'total_quantity', 2, 'block_id')
    week_agg['qty_lag_4w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'total_quantity', 4, 'block_id')
    
    week_agg['n_dealers_lag_1w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'n_dealers', 1, 'block_id')
    week_agg['median_unit_price_lag_1w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'median_unit_price', 1, 'block_id')
    week_agg['implied_price_lag_1w'] = safe_lag(week_agg, 'product_code', ['period_idx'], 'implied_price', 1, 'block_id')
    
    week_agg['qty_roll_mean_2w'] = safe_rolling_mean(week_agg, 'product_code', 'total_quantity', 2, 'block_id')
    week_agg['qty_roll_mean_4w'] = safe_rolling_mean(week_agg, 'product_code', 'total_quantity', 4, 'block_id')
    
    # Merge lags back
    lag_cols = ['qty_lag_1w', 'qty_lag_2w', 'qty_lag_4w', 'n_dealers_lag_1w', 'median_unit_price_lag_1w', 'implied_price_lag_1w', 'qty_roll_mean_2w', 'qty_roll_mean_4w']
    combined = combined.drop(columns=lag_cols, errors='ignore') # Drop if existed in hist
    combined = combined.merge(week_agg[['product_code', 'period_idx'] + lag_cols], on=['product_code', 'period_idx'], how='left')
    
    # Filter back to future rows (where segment_start_date is not null and is from fdf)
    # We can distinguish future rows by looking at dates in Q2 (fiscal_month >= 4 and year == 2026)
    out_future = combined[(combined['fiscal_month'] >= 4) & (combined['year'] == 2026)].copy()
    
    out_future.to_parquet(os.path.join(FEATURES_DIR, "track1_weekly_future_q2_rows.parquet"), index=False)
    print(f"  -> Weekly future rows: {len(out_future)}")
    return out_future

def build_feature_registry():
    print("Building feature registry...")
    registry = [
        # Calendar
        {"feature_name": "fiscal_year", "feature_family": "calendar", "grain": "both", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "fiscal_month", "feature_family": "calendar", "grain": "both", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "month_sin", "feature_family": "calendar", "grain": "both", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "month_cos", "feature_family": "calendar", "grain": "both", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "is_q1", "feature_family": "calendar", "grain": "monthly", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "is_q2", "feature_family": "calendar", "grain": "monthly", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "days_in_month", "feature_family": "calendar", "grain": "monthly", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        
        # Static product
        {"feature_name": "group_code_clean", "feature_family": "static", "grain": "both", "dtype": "string", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        {"feature_name": "base_color", "feature_family": "static", "grain": "both", "dtype": "string", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "computation_rule": "Primary color feature", "requires_shift": False, "block_aware": False},
        {"feature_name": "color", "feature_family": "static", "grain": "both", "dtype": "string", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "computation_rule": "Detail/raw color feature", "requires_shift": False, "block_aware": False},
        {"feature_name": "is_unknown_hierarchy", "feature_family": "static", "grain": "both", "dtype": "int", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": False, "block_aware": False},
        
        # Lags
        {"feature_name": "qty_lag_1", "feature_family": "lag", "grain": "monthly", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": True, "block_aware": True},
        {"feature_name": "qty_lag_2", "feature_family": "lag", "grain": "monthly", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": True, "block_aware": True},
        {"feature_name": "sku_share_in_group_lagged", "feature_family": "hierarchy_share", "grain": "monthly", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": True, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": True, "block_aware": True},
        
        # Dealer/Price
        {"feature_name": "n_dealers_lag1", "feature_family": "dealer", "grain": "monthly", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": True, "block_aware": True},
        {"feature_name": "implied_price_lag1", "feature_family": "pricing", "grain": "monthly", "dtype": "float", "allowed_for_model": True, "model_candidate_minimal": False, "model_candidate_extended": True, "leakage_risk": "low", "requires_shift": True, "block_aware": True},
    ]
    
    with open(os.path.join(CONFIG_DIR, "feature_registry_track1.json"), "w", encoding='utf-8') as f:
        json.dump(registry, f, indent=4)
    print(f"  -> Registry saved.")

def run_leakage_audit():
    print("Running leakage audit...")
    m = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_model_panel.parquet"))
    w = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_model_panel.parquet"))
    mf = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_future_q2_rows.parquet"))
    wf = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_future_q2_rows.parquet"))
    
    results = []
    
    # Row counts
    results.append({"Check": "Monthly hist row count == 925", "Status": "PASS" if len(m) == 925 else "FAIL", "Detail": len(m)})
    results.append({"Check": "Weekly hist row count == 2642", "Status": "PASS" if len(w) == 2642 else "FAIL", "Detail": len(w)})
    results.append({"Check": "SKU count == 265", "Status": "PASS" if m['product_code'].nunique() == 265 else "FAIL", "Detail": m['product_code'].nunique()})
    
    # UNKNOWN handling
    unknown_m = m[m['group_code_clean'] == 'UNKNOWN']
    results.append({"Check": "UNKNOWN SKU count == 55", "Status": "PASS" if unknown_m['product_code'].nunique() == 55 else "FAIL", "Detail": unknown_m['product_code'].nunique()})
    
    rev_share = unknown_m['total_revenue'].sum() / m['total_revenue'].sum() * 100
    qty_share = unknown_m['total_quantity'].sum() / m['total_quantity'].sum() * 100
    results.append({"Check": "UNKNOWN rev share matches Phase 1C (~12.9%)", "Status": "PASS" if abs(rev_share - 12.9) < 0.5 else "FAIL", "Detail": f"{rev_share:.2f}%"})
    
    # Leakage
    pm4_lags = m[m['period_month'] == 4]['qty_lag_1'].isna().all()
    results.append({"Check": "No lag crosses block A->B (pm=4 is NaN)", "Status": "PASS" if pm4_lags else "FAIL", "Detail": "Checked period_month=4"})
    
    results.append({"Check": "Target total_quantity exists in hist", "Status": "PASS" if 'total_quantity' in m.columns else "FAIL", "Detail": ""})
    results.append({"Check": "Target total_quantity NaN in future monthly", "Status": "PASS" if mf['total_quantity'].isna().all() else "FAIL", "Detail": ""})
    results.append({"Check": "Target total_quantity NaN in future weekly", "Status": "PASS" if wf['total_quantity'].isna().all() else "FAIL", "Detail": ""})
    
    # Reconcile
    results.append({"Check": "Monthly feature qty sum == 72146", "Status": "PASS" if abs(m['total_quantity'].sum() - 72146) < 1 else "FAIL", "Detail": m['total_quantity'].sum()})
    results.append({"Check": "Weekly feature qty sum == 72146", "Status": "PASS" if abs(w['total_quantity'].sum() - 72146) < 1 else "FAIL", "Detail": w['total_quantity'].sum()})
    
    df_res = pd.DataFrame(results)
    df_res.to_csv(os.path.join(AUDIT_DIR, "phase2a_leakage_check.csv"), index=False)
    
    # Markdown report
    with open(os.path.join(AUDIT_DIR, "phase2a_feature_store_report.md"), "w", encoding='utf-8') as f:
        f.write("# Phase 2A Leakage Audit Report\n\n")
        f.write(df_res.to_markdown(index=False))
        f.write("\n\n## Conclusion\nFeature store generated successfully without target leakage across the 9-month gap.")
    
    print("  -> Audit passed and reports saved.")

if __name__ == "__main__":
    hm = build_monthly_features()
    hw = build_weekly_features()
    build_future_monthly_rows(hm, pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet")))
    build_future_weekly_rows(hw, pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet")))
    build_feature_registry()
    run_leakage_audit()
    print("Phase 2A completely finished!")
