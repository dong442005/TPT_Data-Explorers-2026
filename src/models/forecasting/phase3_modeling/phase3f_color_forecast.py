import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.forecasting.shared.config.paths import FEATURES_DIR, IMPLEMENT_DIR, METADATA_DIR

from src.models.forecasting.shared.config.paths import MODELING_OUTPUTS_DIR
OUTPUT_DIR = MODELING_OUTPUTS_DIR
REPORT_DIR = OUTPUT_DIR
os.makedirs(REPORT_DIR, exist_ok=True)

def run_phase3f():
    print("=== Phase 3F: Track 2 Color/Variant Forecast ===")
    
    # 1. Load Data
    ml_fcst = pd.read_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_forecast_q2_2026.csv"))
    gs_fcst = pd.read_csv(os.path.join(OUTPUT_DIR, "phase3_group_share_forecast_q2_2026.csv"))
    gs_scen = pd.read_csv(os.path.join(OUTPUT_DIR, "phase3_scenario_summary_q2_2026.csv"))
    meta = pd.read_parquet(os.path.join(METADATA_DIR, "product_metadata.parquet"))
    m_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_train_aligned.parquet"))
    
    # Filter ML forecast to XGBoost_monthly_extended_features
    xgb_fcst = ml_fcst[ml_fcst['model_name'] == 'XGBoost_monthly_extended_features'].copy()
    
    # 2. Enrich with Metadata
    meta_sub = meta[['product_code', 'product_name', 'group_code_clean', 'line_id_clean', 'base_color', 'color']].drop_duplicates('product_code')
    
    def enrich_forecast(df):
        df = df.copy()
        if 'color' not in df.columns:
            df = df.merge(meta_sub[['product_code', 'color']], on='product_code', how='left')
        
        # Fill missing fields from meta if any
        for col in ['product_name', 'group_code_clean', 'line_id_clean', 'base_color', 'color']:
            if col not in df.columns:
                df = df.merge(meta_sub[['product_code', col]], on='product_code', how='left')
            else:
                mapping = meta_sub.set_index('product_code')[col]
                df[col] = df[col].fillna(df['product_code'].map(mapping))
                
        df['base_color'] = df['base_color'].fillna('UNKNOWN')
        df['color'] = df['color'].fillna('UNKNOWN')
        return df

    xgb_fcst = enrich_forecast(xgb_fcst)
    gs_fcst = enrich_forecast(gs_fcst)
    
    # Get total Q2 for each forecast
    xgb_q2 = xgb_fcst.groupby(['product_code', 'base_color', 'color'])[['predicted_quantity', 'estimated_revenue']].sum().reset_index()
    xgb_q2['model_scenario'] = 'XGBoost_ML_Upside'
    
    gs_q2 = gs_fcst.groupby(['product_code', 'base_color', 'color'])[['predicted_quantity', 'estimated_revenue']].sum().reset_index()
    
    # GS Base Scenario
    gs_base_ratio = gs_scen.loc[gs_scen['Scenario'] == 'Base', 'Total_Q2_Qty'].values[0] / gs_fcst['predicted_quantity'].sum()
    gs_q2_base = gs_q2.copy()
    gs_q2_base['predicted_quantity'] = gs_q2_base['predicted_quantity'] * gs_base_ratio
    gs_q2_base['estimated_revenue'] = gs_q2_base['estimated_revenue'] * gs_base_ratio
    gs_q2_base['model_scenario'] = 'Group_Share_Base'
    
    # GS Aggressive Scenario
    gs_agg_ratio = gs_scen.loc[gs_scen['Scenario'] == 'Aggressive', 'Total_Q2_Qty'].values[0] / gs_fcst['predicted_quantity'].sum()
    gs_q2_agg = gs_q2.copy()
    gs_q2_agg['predicted_quantity'] = gs_q2_agg['predicted_quantity'] * gs_agg_ratio
    gs_q2_agg['estimated_revenue'] = gs_q2_agg['estimated_revenue'] * gs_agg_ratio
    gs_q2_agg['model_scenario'] = 'Group_Share_Aggressive'
    
    combined_sku = pd.concat([xgb_q2, gs_q2_base, gs_q2_agg])
    
    # Reconciliation Check
    xgb_expected = xgb_fcst['predicted_quantity'].sum()
    gs_base_expected = gs_scen.loc[gs_scen['Scenario'] == 'Base', 'Total_Q2_Qty'].values[0]
    gs_agg_expected = gs_scen.loc[gs_scen['Scenario'] == 'Aggressive', 'Total_Q2_Qty'].values[0]
    
    xgb_actual = combined_sku[combined_sku['model_scenario'] == 'XGBoost_ML_Upside']['predicted_quantity'].sum()
    gs_base_actual = combined_sku[combined_sku['model_scenario'] == 'Group_Share_Base']['predicted_quantity'].sum()
    gs_agg_actual = combined_sku[combined_sku['model_scenario'] == 'Group_Share_Aggressive']['predicted_quantity'].sum()
    
    tol = 1.0 # 1 unit tolerance
    if abs(xgb_expected - xgb_actual) > tol:
        raise ValueError(f"Reconciliation Failed for XGBoost: Expected {xgb_expected}, Got {xgb_actual}")
    if abs(gs_base_expected - gs_base_actual) > tol:
        raise ValueError(f"Reconciliation Failed for GS Base: Expected {gs_base_expected}, Got {gs_base_actual}")
    if abs(gs_agg_expected - gs_agg_actual) > tol:
        raise ValueError(f"Reconciliation Failed for GS Aggressive: Expected {gs_agg_expected}, Got {gs_agg_actual}")
        
    print("Reconciliation checks passed.")

    # 3. Aggregate by Color
    color_fcst = combined_sku.groupby(['model_scenario', 'base_color', 'color'])[['predicted_quantity', 'estimated_revenue']].sum().reset_index()
    color_fcst.to_csv(os.path.join(REPORT_DIR, "phase3_color_forecast_q2_2026.csv"), index=False)
    
    # Pivot summary
    summary_qty = color_fcst.pivot_table(index=['base_color', 'color'], columns='model_scenario', values='predicted_quantity', fill_value=0)
    summary_qty.columns = [f"{c}_Qty" for c in summary_qty.columns]
    summary_rev = color_fcst.pivot_table(index=['base_color', 'color'], columns='model_scenario', values='estimated_revenue', fill_value=0)
    summary_rev.columns = [f"{c}_Rev" for c in summary_rev.columns]
    color_summary = pd.concat([summary_qty, summary_rev], axis=1).reset_index()
    color_summary.to_csv(os.path.join(REPORT_DIR, "phase3_color_summary_q2_2026.csv"), index=False)
    
    # 4. Slow-moving SKU/Color Flags
    print("Calculating Slow-moving SKU/Color Flags...")
    # Extract Q1_2025 and Q1_2026
    # Q1_2025 = period_month 1,2,3 (Jan,Feb,Mar 2025)
    # Q1_2026 = period_month 13,14,15 (Jan,Feb,Mar 2026)
    q1_25 = m_train[m_train['period_month'].isin([1, 2, 3])].groupby('product_code')['total_quantity'].sum().reset_index(name='q1_2025_qty')
    q1_26 = m_train[m_train['period_month'].isin([13, 14, 15])]
    
    q1_26_sum = q1_26.groupby('product_code')['total_quantity'].sum().reset_index(name='q1_2026_qty')
    jan26 = q1_26[q1_26['period_month']==13].groupby('product_code')['total_quantity'].sum().reset_index(name='jan26_qty')
    feb26 = q1_26[q1_26['period_month']==14].groupby('product_code')['total_quantity'].sum().reset_index(name='feb26_qty')
    mar26 = q1_26[q1_26['period_month']==15].groupby('product_code')['total_quantity'].sum().reset_index(name='mar26_qty')
    
    sku_flags = meta_sub[['product_code', 'product_name', 'group_code_clean', 'line_id_clean', 'base_color', 'color']].copy()
    sku_flags = sku_flags.merge(q1_25, on='product_code', how='left').fillna({'q1_2025_qty': 0})
    sku_flags = sku_flags.merge(q1_26_sum, on='product_code', how='left').fillna({'q1_2026_qty': 0})
    sku_flags = sku_flags.merge(jan26, on='product_code', how='left').fillna({'jan26_qty': 0})
    sku_flags = sku_flags.merge(feb26, on='product_code', how='left').fillna({'feb26_qty': 0})
    sku_flags = sku_flags.merge(mar26, on='product_code', how='left').fillna({'mar26_qty': 0})
    
    sku_flags['q1_yoy_change_pct'] = np.where(
        sku_flags['q1_2025_qty'] > 0, 
        (sku_flags['q1_2026_qty'] - sku_flags['q1_2025_qty']) / sku_flags['q1_2025_qty'],
        np.nan
    )
    
    # Calculate group P10
    group_p10 = sku_flags[sku_flags['q1_2026_qty'] > 0].groupby('group_code_clean')['q1_2026_qty'].quantile(0.1).to_dict()
    
    flags = []
    reasons = []
    actions = []
    
    for idx, row in sku_flags.iterrows():
        g = row['group_code_clean']
        q1_25_val = row['q1_2025_qty']
        q1_26_val = row['q1_2026_qty']
        yoy = row['q1_yoy_change_pct']
        jan = row['jan26_qty']
        feb = row['feb26_qty']
        mar = row['mar26_qty']
        
        # historical presence (if total quantity across all time is 0 before Mar26, it's new)
        # simplistic check: if q1_25 == 0 and jan == 0 and feb == 0 and mar > 0 -> new
        is_new = (q1_25_val == 0) and (jan == 0) and (feb == 0)
        
        if is_new:
            flags.append('new_or_uncertain')
            reasons.append('SKU appeared very recently (Mar26 or Q1_2026) with no Q1_25 history.')
            actions.append('Monitor demand closely. Do not classify as slow-moving yet.')
        elif q1_26_val == 0:
            flags.append('red_no_demand')
            reasons.append('Q1_2026 total_quantity = 0.')
            actions.append('Phase out or stop production unless required for strategic reasons.')
        else:
            p10_threshold = group_p10.get(g, 10)
            threshold = max(10, p10_threshold)
            
            if q1_26_val <= threshold:
                flags.append('amber_slow_moving')
                reasons.append(f'Q1_2026 qty ({q1_26_val}) is <= group P10/10 threshold ({threshold}).')
                actions.append('Deprioritize in production. Liquidate excess inventory.')
            elif q1_25_val >= 10 and not pd.isna(yoy) and yoy <= -0.5:
                flags.append('declining_activity')
                reasons.append(f'Q1_2026 qty dropped by {abs(yoy*100):.1f}% vs Q1_2025.')
                actions.append('Review marketing/pricing. Reduce production forecast.')
            else:
                flags.append('healthy')
                reasons.append('Normal activity.')
                actions.append('Follow Q2 forecast.')
                
    sku_flags['slow_moving_flag'] = flags
    sku_flags['slow_moving_reason'] = reasons
    sku_flags['recommended_action'] = actions
    
    sku_flags.to_csv(os.path.join(REPORT_DIR, "phase3_slow_moving_sku_color_flags.csv"), index=False)
    
    print("Saved Phase 3F outputs.")

if __name__ == "__main__":
    run_phase3f()
