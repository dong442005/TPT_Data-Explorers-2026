import os
import sys
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.forecasting.shared.config.paths import FEATURES_DIR, IMPLEMENT_DIR, METADATA_DIR, RAW_DATA_DIR

from src.models.forecasting.shared.config.paths import MODELING_OUTPUTS_DIR
OUTPUT_DIR = MODELING_OUTPUTS_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

def wmape(y_true, y_pred):
    return np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) if np.sum(np.abs(y_true)) > 0 else np.nan

def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    return np.mean(np.where(denom == 0, 0, np.abs(y_true - y_pred) / denom))

def eval_metrics(y_true, y_pred):
    mae = np.abs(y_true - y_pred).mean()
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    bias = np.mean(y_pred - y_true)
    wm = wmape(y_true, y_pred)
    sm = smape(y_true, y_pred)
    return {
        'MAE': mae,
        'RMSE': rmse,
        'WMAPE': wm,
        'SMAPE': sm,
        'Bias': bias
    }

def build_asp_hierarchy(skus, group_mapping, cutoff_date, m_train, raw_price_path):
    """
    Returns a dataframe with columns:
    product_code, asp_used, asp_source, asp_cutoff_date
    """
    res = []
    
    # Load raw price
    if os.path.exists(raw_price_path):
        price_df = pd.read_csv(raw_price_path)
        price_df['product_code'] = price_df['product_code'].astype(str)
        price_df['effective_from'] = pd.to_datetime(price_df['effective_from'])
        # filter before cutoff
        price_df = price_df[price_df['effective_from'] <= pd.to_datetime(cutoff_date)]
        # sort to get latest
        price_df = price_df.sort_values('effective_from').groupby('product_code').tail(1)
        latest_effective = dict(zip(price_df['product_code'], price_df['unit_price']))
    else:
        price_df = pd.DataFrame()
        latest_effective = {}
        
    # Latest transaction price from m_train before cutoff
    if cutoff_date == '2026-02-28':
        hist = m_train[m_train['period_month'] <= 14]
    else:
        hist = m_train[m_train['period_month'] <= 15]
        
    # Get last non-null implied_price per SKU
    hist_prices = hist.dropna(subset=['implied_price']).sort_values('period_month').groupby('product_code').tail(1)
    latest_tx = dict(zip(hist_prices['product_code'], hist_prices['implied_price']))
    
    # Group-level latest effective ASP
    group_eff_prices = {}
    if not price_df.empty:
        price_df_mapped = price_df.merge(group_mapping, on='product_code', how='left')
        group_eff_prices = price_df_mapped.groupby('group_code_clean')['unit_price'].mean().to_dict()
        
    # Group-level latest transaction ASP
    # sum(revenue)/sum(qty) in the latest month overall (which is max period_month in hist)
    max_pm = hist['period_month'].max()
    hist_latest = hist[hist['period_month'] == max_pm]
    group_tx_prices = {}
    for g, d in hist_latest.groupby('group_code_clean'):
        if d['total_quantity'].sum() > 0:
            group_tx_prices[g] = d['total_revenue'].sum() / d['total_quantity'].sum()
            
    # Overall latest ASP
    overall_tx = 0
    if hist_latest['total_quantity'].sum() > 0:
        overall_tx = hist_latest['total_revenue'].sum() / hist_latest['total_quantity'].sum()
        
    # Fallback cascade
    for sku in skus:
        g = group_mapping[group_mapping['product_code'] == sku]['group_code_clean']
        g = g.iloc[0] if len(g) > 0 else 'UNKNOWN'
        
        if sku in latest_effective:
            res.append({'product_code': sku, 'asp_used': latest_effective[sku], 'asp_source': 'a. SKU latest effective price', 'asp_cutoff_date': cutoff_date})
        elif sku in latest_tx:
            res.append({'product_code': sku, 'asp_used': latest_tx[sku], 'asp_source': 'b. SKU latest transaction unit_price', 'asp_cutoff_date': cutoff_date})
        elif g in group_eff_prices:
            res.append({'product_code': sku, 'asp_used': group_eff_prices[g], 'asp_source': 'c. group-level latest effective ASP', 'asp_cutoff_date': cutoff_date})
        elif g in group_tx_prices:
            res.append({'product_code': sku, 'asp_used': group_tx_prices[g], 'asp_source': 'd. group-level latest transaction ASP', 'asp_cutoff_date': cutoff_date})
        else:
            res.append({'product_code': sku, 'asp_used': overall_tx, 'asp_source': 'e. overall latest ASP', 'asp_cutoff_date': cutoff_date})
            
    return pd.DataFrame(res)


def run_phase3b():
    print("=== Phase 3B: Core Baselines & Group-Share Primary ===")
    
    # 1. Load data
    m_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_train_aligned.parquet"))
    meta = pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet"))
    raw_price_path = os.path.join(RAW_DATA_DIR, "product_price.csv")
    
    group_map = meta[['product_code', 'group_code_clean']].drop_duplicates()
    
    # Classify High vs Low volume based on Jan-Feb 2026
    hist_q1_early = m_train[m_train['period_month'].isin([13, 14])]
    sku_vols = hist_q1_early.groupby('product_code')['total_quantity'].sum().reset_index()
    vol_p75 = sku_vols['total_quantity'].quantile(0.75)
    sku_vols['volume_segment'] = np.where(sku_vols['total_quantity'] >= vol_p75, 'High Volume', 'Low Volume')
    vol_map = sku_vols[['product_code', 'volume_segment']]
    
    # ============================================================
    # PART 1: Baseline Comparison on Mar26 (Stress Test)
    # ============================================================
    print("1. Running Baseline Comparison (Val = Mar26)")
    val_df = m_train[m_train['period_month'] == 15].copy()
    val_df = val_df.merge(vol_map, on='product_code', how='left')
    val_df['volume_segment'] = val_df['volume_segment'].fillna('Low Volume')
    
    # Baselines
    val_df['pred_naive_last'] = val_df['qty_lag_1'].fillna(0)
    val_df['pred_jan_feb_avg'] = val_df[['qty_lag_1', 'qty_lag_2']].mean(axis=1).fillna(0)
    
    # Group-share proportional validation version (use Jan-Feb to predict Mar26)
    # Step 1: Total predicted for Mar26 = Jan-Feb Avg Total
    jan_feb_total = hist_q1_early.groupby('period_month')['total_quantity'].sum().mean()
    mar_total_pred = jan_feb_total
    
    # Step 2 & 3: SKU share from Jan-Feb
    sku_jf_qty = hist_q1_early.groupby('product_code')['total_quantity'].sum().reset_index(name='jf_qty')
    total_jf = sku_jf_qty['jf_qty'].sum()
    sku_jf_qty['sku_share'] = sku_jf_qty['jf_qty'] / total_jf if total_jf > 0 else 0
    
    val_df = val_df.merge(sku_jf_qty[['product_code', 'sku_share']], on='product_code', how='left')
    val_df['sku_share'] = val_df['sku_share'].fillna(0)
    val_df['pred_group_share_proportional'] = mar_total_pred * val_df['sku_share']
    
    models = ['pred_naive_last', 'pred_jan_feb_avg', 'pred_group_share_proportional']
    
    metrics_all = []
    
    # OVERALL metrics
    for m in models:
        res = eval_metrics(val_df['total_quantity'], val_df[m])
        res['Model'] = m.replace('pred_', '')
        res['Segment'] = 'Overall'
        metrics_all.append(res)
        
    # By Group
    for g in val_df['group_code_clean'].unique():
        gdf = val_df[val_df['group_code_clean'] == g]
        for m in models:
            res = eval_metrics(gdf['total_quantity'], gdf[m])
            res['Model'] = m.replace('pred_', '')
            res['Segment'] = f"Group: {g}"
            metrics_all.append(res)
            
    # By Volume
    for v in val_df['volume_segment'].unique():
        vdf = val_df[val_df['volume_segment'] == v]
        for m in models:
            res = eval_metrics(vdf['total_quantity'], vdf[m])
            res['Model'] = m.replace('pred_', '')
            res['Segment'] = f"Volume: {v}"
            metrics_all.append(res)
            
    df_metrics = pd.DataFrame(metrics_all)
    df_metrics = df_metrics[['Model', 'Segment', 'MAE', 'RMSE', 'WMAPE', 'SMAPE', 'Bias']]
    
    # Split into 3 files
    df_overall = df_metrics[df_metrics['Segment'] == 'Overall'].copy()
    df_group = df_metrics[df_metrics['Segment'].str.startswith('Group:')].copy()
    
    df_overall.to_csv(os.path.join(OUTPUT_DIR, "phase3_metrics_overall.csv"), index=False)
    df_group.to_csv(os.path.join(OUTPUT_DIR, "phase3_metrics_by_group.csv"), index=False)
    df_metrics.to_csv(os.path.join(OUTPUT_DIR, "phase3_baseline_comparison.csv"), index=False)
    
    print("   Metrics generated.")
    
    # ============================================================
    # PART 2: Group-Share Proportional Forecast for Q2 2026
    # ============================================================
    print("\n2. Generating Group-Share Primary Forecast (Q2 2026)")
    
    # Q1 Actuals for Shares (Jan, Feb, Mar)
    q1_26 = m_train[m_train['period_month'].isin([13, 14, 15])]
    sku_q1_qty = q1_26.groupby('product_code')['total_quantity'].sum().reset_index(name='sku_q1_qty')
    
    # Total qty per Group in Q1
    sku_q1_qty = sku_q1_qty.merge(group_map, on='product_code', how='left')
    group_q1_qty = sku_q1_qty.groupby('group_code_clean')['sku_q1_qty'].sum().reset_index(name='group_q1_qty')
    total_q1_qty = group_q1_qty['group_q1_qty'].sum()
    
    # Shares
    group_q1_qty['group_share'] = group_q1_qty['group_q1_qty'] / total_q1_qty
    sku_q1_qty = sku_q1_qty.merge(group_q1_qty[['group_code_clean', 'group_share', 'group_q1_qty']], on='group_code_clean', how='left')
    sku_q1_qty['sku_share_in_group'] = sku_q1_qty['sku_q1_qty'] / sku_q1_qty['group_q1_qty'].replace(0, np.nan)
    sku_q1_qty['sku_share_in_group'] = sku_q1_qty['sku_share_in_group'].fillna(0)
    
    # Get ASP hierarchy with cutoff = Mar26 (2026-03-31)
    asp_df = build_asp_hierarchy(meta['product_code'].unique(), group_map, '2026-03-31', m_train, raw_price_path)
    sku_q1_qty = sku_q1_qty.merge(asp_df, on='product_code', how='right').fillna(0)
    
    # Scenarios for Total Q2 Qty (Blueprint constants)
    scenarios = {
        'Conservative': 31956,
        'Base': 37596,
        'Aggressive': 42953
    }
    
    forecast_rows = []
    summary_rows = []
    now_ts = datetime.datetime.now().isoformat()
    
    for scenario_name, total_q2 in scenarios.items():
        # Step 2: Group Q2
        group_forecast = group_q1_qty.copy()
        group_forecast['group_q2_qty'] = total_q2 * group_forecast['group_share']
        
        # Step 3: SKU Q2
        sku_forecast = sku_q1_qty.copy()
        sku_forecast = sku_forecast.merge(group_forecast[['group_code_clean', 'group_q2_qty']], on='group_code_clean', how='left')
        sku_forecast['sku_q2_qty'] = sku_forecast['group_q2_qty'] * sku_forecast['sku_share_in_group']
        
        # Step 4: SKU Month (divide by 3)
        sku_forecast['sku_month_qty'] = sku_forecast['sku_q2_qty'] / 3
        sku_forecast['sku_month_qty'] = sku_forecast['sku_month_qty'].fillna(0)
        
        # Merge metadata
        sku_forecast = sku_forecast.merge(meta[['product_code', 'product_name', 'line_id_clean', 'base_color']], on='product_code', how='left')
        
        # Add to output
        for _, row in sku_forecast.iterrows():
            for m in [4, 5, 6]:
                forecast_rows.append({
                    'product_code': row['product_code'],
                    'product_name': row.get('product_name', ''),
                    'group_code_clean': row.get('group_code_clean', 'UNKNOWN'),
                    'line_id_clean': row.get('line_id_clean', ''),
                    'base_color': row.get('base_color', ''),
                    'fiscal_year': 2026,
                    'fiscal_month': m,
                    'scenario': scenario_name,
                    'scenario_formula': 'Blueprint scenario constant',
                    'predicted_quantity': row['sku_month_qty'],
                    'asp_used': row['asp_used'],
                    'asp_source': row['asp_source'],
                    'asp_cutoff_date': row['asp_cutoff_date'],
                    'estimated_revenue': row['sku_month_qty'] * row['asp_used'],
                    'method_type': 'core_baseline',
                    'model_name': 'group_share_proportional',
                    'run_timestamp': now_ts
                })
                
        # Summary
        summary_rows.append({
            'Scenario': scenario_name,
            'Total_Q2_Qty': sku_forecast['sku_q2_qty'].sum(),
            'Total_Q2_Revenue': (sku_forecast['sku_q2_qty'] * sku_forecast['asp_used']).sum(),
            'Monthly_Avg_Qty': sku_forecast['sku_q2_qty'].sum() / 3,
            'Monthly_Avg_Revenue': (sku_forecast['sku_q2_qty'] * sku_forecast['asp_used']).sum() / 3,
            'Source': 'Blueprint scenario constant'
        })
        
    df_forecast = pd.DataFrame(forecast_rows)
    df_summary = pd.DataFrame(summary_rows)
    
    fcst_path = os.path.join(OUTPUT_DIR, "phase3_group_share_forecast_q2_2026.csv")
    summ_path = os.path.join(OUTPUT_DIR, "phase3_scenario_summary_q2_2026.csv")
    
    df_forecast.to_csv(fcst_path, index=False)
    df_summary.to_csv(summ_path, index=False)
    
    print(f"   Saved {fcst_path} ({len(df_forecast)} rows)")
    print(f"   Saved {summ_path}")
    print("\nScenario Summary:")
    print(df_summary)

if __name__ == "__main__":
    run_phase3b()
