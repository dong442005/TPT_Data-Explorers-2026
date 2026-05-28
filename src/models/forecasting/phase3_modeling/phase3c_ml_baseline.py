import os
import sys
import pandas as pd
import numpy as np
import json
import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.forecasting.shared.config.paths import FEATURES_DIR, IMPLEMENT_DIR, CONFIG_DIR, RAW_DATA_DIR

from src.models.forecasting.shared.config.paths import MODELING_OUTPUTS_DIR
OUTPUT_DIR = MODELING_OUTPUTS_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Try importing models
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from catboost import CatBoostRegressor
    HAS_CAT = True
except ImportError:
    HAS_CAT = False
    
from sklearn.preprocessing import OneHotEncoder

def wmape(y_true, y_pred):
    return np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) if np.sum(np.abs(y_true)) > 0 else np.nan

def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    return np.mean(np.where(denom == 0, 0, np.abs(y_true - y_pred) / denom))

def eval_metrics(y_true, y_pred):
    mae = np.abs(y_true - y_pred).mean()
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    mean_error = np.mean(y_pred - y_true)
    bias_ratio = np.sum(y_pred - y_true) / np.sum(y_true) if np.sum(y_true) > 0 else np.nan
    wm = wmape(y_true, y_pred)
    sm = smape(y_true, y_pred)
    return {
        'MAE': mae,
        'RMSE': rmse,
        'WMAPE': wm,
        'SMAPE': sm,
        'Mean_Error': mean_error,
        'Bias_Ratio': bias_ratio
    }

def run_phase3c():
    np.random.seed(42)
    print("=== Phase 3C: Enhanced ML Baseline ===")
    
    # 1. Load Data
    m_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_train_aligned.parquet"))
    m_future = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_monthly_future_aligned.parquet"))
    w_train = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_train_aligned.parquet"))
    w_future = pd.read_parquet(os.path.join(FEATURES_DIR, "track1_weekly_future_aligned.parquet"))
    meta = pd.read_parquet(os.path.join(CONFIG_DIR, "product_metadata.parquet"))
    
    with open(os.path.join(CONFIG_DIR, "track1_model_feature_sets.json"), "r") as f:
        feature_sets = json.load(f)
        
    # High/Low Volume definitions (based on Jan-Feb 2026 as in 3B)
    hist_q1_early = m_train[m_train['period_month'].isin([13, 14])]
    sku_vols = hist_q1_early.groupby('product_code')['total_quantity'].sum().reset_index()
    vol_p75 = sku_vols['total_quantity'].quantile(0.75)
    sku_vols['volume_segment'] = np.where(sku_vols['total_quantity'] >= vol_p75, 'High Volume', 'Low Volume')
    vol_map = sku_vols[['product_code', 'volume_segment']]
    
    # Validation splits
    # Monthly
    m_X_train_full = m_train[m_train['period_month'] <= 14].copy()
    m_y_train_full = m_X_train_full['total_quantity']
    m_X_val = m_train[m_train['period_month'] == 15].copy()
    m_y_val = m_X_val['total_quantity']
    
    # Weekly (Mar26 weeks are those where fiscal_month == 3 and fiscal_year == 2026)
    w_X_train_full = w_train[(w_train['fiscal_year'] < 2026) | ((w_train['fiscal_year'] == 2026) & (w_train['fiscal_month'] <= 2))].copy()
    w_y_train_full = w_X_train_full['total_quantity']
    w_X_val = w_train[(w_train['fiscal_year'] == 2026) & (w_train['fiscal_month'] == 3)].copy()
    w_y_val = w_X_val['total_quantity']
    
    metrics_all = []
    q2_forecast_rows = []
    feature_importances = []
    now_ts = datetime.datetime.now().isoformat()
    
    # Helper to get ASP for Q2 inference
    # Note: Using the exact same ASP used in Phase 3B. We can join it later or load it from Phase 3B output.
    asp_info = pd.read_csv(os.path.join(OUTPUT_DIR, "phase3_group_share_forecast_q2_2026.csv"))
    # We just need asp_used, asp_source, asp_cutoff_date per product_code
    asp_map = asp_info[['product_code', 'asp_used', 'asp_source', 'asp_cutoff_date']].drop_duplicates().set_index('product_code').to_dict('index')

    configs = [
        ('monthly', 'monthly_minimal_features', feature_sets['monthly_minimal_features']),
        ('monthly', 'monthly_extended_features', feature_sets['monthly_extended_features']),
        ('weekly', 'weekly_minimal_features', feature_sets['weekly_minimal_features']),
        ('weekly', 'weekly_extended_features', feature_sets['weekly_extended_features']),
    ]
    
    for grain, config_name, features in configs:
        print(f"\nTraining {config_name} ({len(features)} features)")
        
        # Assert features exist
        if grain == 'monthly':
            df_train = m_X_train_full
            y_train = m_y_train_full
            df_val = m_X_val
            y_val = m_y_val
            df_future = m_future
            
            # Identify categoricals dynamically
            cat_features = [f for f in features if df_train[f].dtype == 'object' or f.endswith('_clean') or f in ['base_color', 'color']]
        else:
            df_train = w_X_train_full
            y_train = w_y_train_full
            df_val = w_X_val
            y_val = w_y_val
            df_future = w_future
            
            cat_features = [f for f in features if df_train[f].dtype == 'object' or f.endswith('_clean') or f in ['base_color', 'color']]

        # Assert all features exist
        missing = [f for f in features if f not in df_train.columns]
        if missing:
            print(f"  WARNING: Missing features in train: {missing}. Skipping config.")
            continue
            
        X_tr = df_train[features].copy()
        X_va = df_val[features].copy()
        X_fu = df_future[features].copy() if not df_future.empty else pd.DataFrame()
        
        # Preprocessing for LGBM & CatBoost (cast to string/category)
        for c in cat_features:
            X_tr[c] = X_tr[c].fillna('UNKNOWN').astype(str)
            X_va[c] = X_va[c].fillna('UNKNOWN').astype(str)
            if not X_fu.empty:
                X_fu[c] = X_fu[c].fillna('UNKNOWN').astype(str)
                
        # --- LightGBM ---
        if HAS_LGB:
            print("  -> LightGBM")
            X_tr_lgb = X_tr.copy()
            X_va_lgb = X_va.copy()
            X_fu_lgb = X_fu.copy() if not X_fu.empty else pd.DataFrame()
            
            for c in cat_features:
                X_tr_lgb[c] = X_tr_lgb[c].astype('category')
                X_va_lgb[c] = X_va_lgb[c].astype('category')
                if not X_fu_lgb.empty:
                    X_fu_lgb[c] = X_fu_lgb[c].astype('category')
                    
            model_lgb = lgb.LGBMRegressor(
                num_leaves=15,
                max_depth=4,
                min_child_samples=50,
                n_estimators=200,
                reg_alpha=1.0,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=1,
                deterministic=True
            )
            model_lgb.fit(X_tr_lgb, y_train, categorical_feature=cat_features)
            
            preds_val = np.maximum(0, model_lgb.predict(X_va_lgb))
            
            # Metrics
            if 'volume_segment' not in df_val.columns:
                df_val['volume_segment'] = df_val['product_code'].map(vol_map.set_index('product_code')['volume_segment']).fillna('Low Volume')
            
            def add_metrics(y_t, y_p, seg):
                res = eval_metrics(y_t, y_p)
                res['Model'] = f"LightGBM_{config_name}"
                res['Segment'] = seg
                res['Grain'] = grain
                metrics_all.append(res)
                
            add_metrics(y_val, preds_val, 'Overall')
            for g in df_val['group_code_clean'].unique():
                idx = df_val['group_code_clean'] == g
                add_metrics(y_val[idx], preds_val[idx], f"Group: {g}")
            for v in df_val['volume_segment'].unique():
                idx = df_val['volume_segment'] == v
                add_metrics(y_val[idx], preds_val[idx], f"Volume: {v}")
                
            # Q2 Inference
            if grain == 'monthly' and not X_fu_lgb.empty:
                preds_q2 = np.maximum(0, model_lgb.predict(X_fu_lgb))
                for i, row in df_future.iterrows():
                    sku = row['product_code']
                    q = preds_q2[i]
                    a_info = asp_map.get(sku, {'asp_used': 0, 'asp_source': 'Unknown', 'asp_cutoff_date': 'Unknown'})
                    q2_forecast_rows.append({
                        'product_code': sku,
                        'product_name': meta[meta['product_code']==sku]['product_name'].iloc[0] if len(meta[meta['product_code']==sku])>0 else '',
                        'group_code_clean': row.get('group_code_clean', 'UNKNOWN'),
                        'line_id_clean': row.get('line_id_clean', ''),
                        'base_color': row.get('base_color', ''),
                        'fiscal_year': row['fiscal_year'],
                        'fiscal_month': row['fiscal_month'],
                        'predicted_quantity': q,
                        'asp_used': a_info['asp_used'],
                        'asp_source': a_info['asp_source'],
                        'asp_cutoff_date': a_info['asp_cutoff_date'],
                        'estimated_revenue': q * a_info['asp_used'],
                        'method_type': 'enhanced_ml_baseline',
                        'model_name': f"LightGBM_{config_name}",
                        'run_timestamp': now_ts
                    })
                    
            # Feature Importance
            for f, imp in zip(features, model_lgb.feature_importances_):
                feature_importances.append({
                    'Model': f"LightGBM_{config_name}",
                    'Feature': f,
                    'Importance': imp
                })

        # --- XGBoost ---
        if HAS_XGB:
            print("  -> XGBoost")
            # Need OHE for cat features
            X_tr_xgb = X_tr.drop(columns=cat_features).copy()
            X_va_xgb = X_va.drop(columns=cat_features).copy()
            X_fu_xgb = X_fu.drop(columns=cat_features).copy() if not X_fu.empty else pd.DataFrame()
            
            if cat_features:
                ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
                ohe.fit(X_tr[cat_features])
                
                cat_tr = pd.DataFrame(ohe.transform(X_tr[cat_features]), columns=ohe.get_feature_names_out(), index=X_tr.index)
                cat_va = pd.DataFrame(ohe.transform(X_va[cat_features]), columns=ohe.get_feature_names_out(), index=X_va.index)
                X_tr_xgb = pd.concat([X_tr_xgb, cat_tr], axis=1)
                X_va_xgb = pd.concat([X_va_xgb, cat_va], axis=1)
                
                if not X_fu_xgb.empty:
                    cat_fu = pd.DataFrame(ohe.transform(X_fu[cat_features]), columns=ohe.get_feature_names_out(), index=X_fu.index)
                    X_fu_xgb = pd.concat([X_fu_xgb, cat_fu], axis=1)
                    
            model_xgb = xgb.XGBRegressor(
                max_depth=3,
                n_estimators=200,
                learning_rate=0.05,
                colsample_bytree=0.8,
                reg_alpha=1.0,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=1
            )
            # Fix issue with boolean features in XGB
            for col in X_tr_xgb.columns:
                if X_tr_xgb[col].dtype == bool:
                    X_tr_xgb[col] = X_tr_xgb[col].astype(int)
                    X_va_xgb[col] = X_va_xgb[col].astype(int)
                    if not X_fu_xgb.empty:
                        X_fu_xgb[col] = X_fu_xgb[col].astype(int)
                        
            model_xgb.fit(X_tr_xgb, y_train)
            preds_val = np.maximum(0, model_xgb.predict(X_va_xgb))
            
            # Metrics
            if 'volume_segment' not in df_val.columns:
                df_val['volume_segment'] = df_val['product_code'].map(vol_map.set_index('product_code')['volume_segment']).fillna('Low Volume')
                
            def add_metrics_xgb(y_t, y_p, seg):
                res = eval_metrics(y_t, y_p)
                res['Model'] = f"XGBoost_{config_name}"
                res['Segment'] = seg
                res['Grain'] = grain
                metrics_all.append(res)
                
            add_metrics_xgb(y_val, preds_val, 'Overall')
            for g in df_val['group_code_clean'].unique():
                idx = df_val['group_code_clean'] == g
                add_metrics_xgb(y_val[idx], preds_val[idx], f"Group: {g}")
            for v in df_val['volume_segment'].unique():
                idx = df_val['volume_segment'] == v
                add_metrics_xgb(y_val[idx], preds_val[idx], f"Volume: {v}")
                
            if grain == 'monthly' and not X_fu_xgb.empty:
                preds_q2 = np.maximum(0, model_xgb.predict(X_fu_xgb))
                for i, row in df_future.iterrows():
                    sku = row['product_code']
                    q = preds_q2[i]
                    a_info = asp_map.get(sku, {'asp_used': 0, 'asp_source': 'Unknown', 'asp_cutoff_date': 'Unknown'})
                    q2_forecast_rows.append({
                        'product_code': sku,
                        'product_name': meta[meta['product_code']==sku]['product_name'].iloc[0] if len(meta[meta['product_code']==sku])>0 else '',
                        'group_code_clean': row.get('group_code_clean', 'UNKNOWN'),
                        'line_id_clean': row.get('line_id_clean', ''),
                        'base_color': row.get('base_color', ''),
                        'fiscal_year': row['fiscal_year'],
                        'fiscal_month': row['fiscal_month'],
                        'predicted_quantity': q,
                        'asp_used': a_info['asp_used'],
                        'asp_source': a_info['asp_source'],
                        'asp_cutoff_date': a_info['asp_cutoff_date'],
                        'estimated_revenue': q * a_info['asp_used'],
                        'method_type': 'enhanced_ml_baseline',
                        'model_name': f"XGBoost_{config_name}",
                        'run_timestamp': now_ts
                    })
                    
            for f, imp in zip(features, model_xgb.feature_importances_):
                feature_importances.append({
                    'Model': f"XGBoost_{config_name}",
                    'Feature': f,
                    'Importance': imp
                })
                    
        # --- CatBoost ---
        if HAS_CAT:
            print("  -> CatBoost")
            model_cat = CatBoostRegressor(
                depth=4,
                learning_rate=0.05,
                l2_leaf_reg=3.0,
                verbose=False,
                random_seed=42,
                thread_count=1
            )
            # CatBoost can handle categoricals directly if we pass cat_features
            # Ensure categoricals are string
            model_cat.fit(X_tr, y_train, cat_features=cat_features)
            preds_val = np.maximum(0, model_cat.predict(X_va))
            
            if 'volume_segment' not in df_val.columns:
                df_val['volume_segment'] = df_val['product_code'].map(vol_map.set_index('product_code')['volume_segment']).fillna('Low Volume')
                
            def add_metrics_cat(y_t, y_p, seg):
                res = eval_metrics(y_t, y_p)
                res['Model'] = f"CatBoost_{config_name}"
                res['Segment'] = seg
                res['Grain'] = grain
                metrics_all.append(res)
                
            add_metrics_cat(y_val, preds_val, 'Overall')
            for g in df_val['group_code_clean'].unique():
                idx = df_val['group_code_clean'] == g
                add_metrics_cat(y_val[idx], preds_val[idx], f"Group: {g}")
            for v in df_val['volume_segment'].unique():
                idx = df_val['volume_segment'] == v
                add_metrics_cat(y_val[idx], preds_val[idx], f"Volume: {v}")
                
            if grain == 'monthly' and not X_fu.empty:
                preds_q2 = np.maximum(0, model_cat.predict(X_fu))
                for i, row in df_future.iterrows():
                    sku = row['product_code']
                    q = preds_q2[i]
                    a_info = asp_map.get(sku, {'asp_used': 0, 'asp_source': 'Unknown', 'asp_cutoff_date': 'Unknown'})
                    q2_forecast_rows.append({
                        'product_code': sku,
                        'product_name': meta[meta['product_code']==sku]['product_name'].iloc[0] if len(meta[meta['product_code']==sku])>0 else '',
                        'group_code_clean': row.get('group_code_clean', 'UNKNOWN'),
                        'line_id_clean': row.get('line_id_clean', ''),
                        'base_color': row.get('base_color', ''),
                        'fiscal_year': row['fiscal_year'],
                        'fiscal_month': row['fiscal_month'],
                        'predicted_quantity': q,
                        'asp_used': a_info['asp_used'],
                        'asp_source': a_info['asp_source'],
                        'asp_cutoff_date': a_info['asp_cutoff_date'],
                        'estimated_revenue': q * a_info['asp_used'],
                        'method_type': 'enhanced_ml_baseline',
                        'model_name': f"CatBoost_{config_name}",
                        'run_timestamp': now_ts
                    })
                    
            for f, imp in zip(features, model_cat.get_feature_importance()):
                feature_importances.append({
                    'Model': f"CatBoost_{config_name}",
                    'Feature': f,
                    'Importance': imp
                })

    # Save metrics
    df_metrics = pd.DataFrame(metrics_all)
    df_overall = df_metrics[df_metrics['Segment'] == 'Overall']
    df_group = df_metrics[df_metrics['Segment'].str.startswith('Group:')]
    
    df_overall.to_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_metrics_overall.csv"), index=False)
    df_group.to_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_metrics_by_group.csv"), index=False)
    df_metrics.to_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_model_comparison.csv"), index=False)
    
    df_fcst = pd.DataFrame(q2_forecast_rows)
    df_fcst.to_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_forecast_q2_2026.csv"), index=False)
    
    df_imp = pd.DataFrame(feature_importances)
    df_imp.to_csv(os.path.join(OUTPUT_DIR, "phase3c_ml_feature_importance.csv"), index=False)
    
    print("\nPhase 3C ML runs completed.")
    print(f"Overall Metrics preview:\n{df_overall.head(10)}")

if __name__ == "__main__":
    run_phase3c()
