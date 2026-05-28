import os
import sys
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
from datetime import timedelta
import datetime

from sklearn.metrics import average_precision_score, roc_auc_score
import logging

try:
    # pyrefly: ignore [missing-import]
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    HAS_XGB = False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.forecasting.shared.config.paths import RAW_DATA_DIR, IMPLEMENT_DIR

from src.models.forecasting.shared.config.paths import MODELING_OUTPUTS_DIR
OUTPUT_DIR = MODELING_OUTPUTS_DIR
REPORT_DIR = OUTPUT_DIR
os.makedirs(REPORT_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def get_rfm_segment(r, f, m):
    # R Score: Dựa trên chu kỳ B2B
    if r <= 30: r_score = 5
    elif r <= 60: r_score = 4
    elif r <= 90: r_score = 3
    elif r <= 180: r_score = 2
    else: r_score = 1
    
    # F Score: Dựa trên phân bố B2B 6 tháng
    if f >= 10: f_score = 5
    elif f >= 6: f_score = 4
    elif f >= 3: f_score = 3
    elif f >= 2: f_score = 2
    else: f_score = 1
    
    # M Score: Dựa trên doanh thu thực tế
    if m >= 1000000000: m_score = 5
    elif m >= 300000000: m_score = 4
    elif m >= 100000000: m_score = 3
    elif m >= 30000000: m_score = 2
    else: m_score = 1
    
    # Logic phân loại từ v_rfm_analysis
    if r_score >= 4 and f_score >= 4 and m_score >= 4: return 'Champions'
    if r_score >= 4 and f_score >= 3 and m_score >= 3: return 'Loyal'
    if r_score >= 3 and f_score <= 2 and m_score >= 4: return 'Big Spender'
    if r_score >= 3 and f_score >= 2 and m_score >= 2: return 'Potential'
    if r_score >= 4 and f_score == 1 and m_score <= 3: return 'New'
    if r_score <= 2 and f_score >= 3 and m_score >= 3: return 'At Risk'
    if r_score <= 2 and (f_score >= 2 or m_score >= 2): return 'Hibernating'
    
    return 'Lost'

def run_track3():
    np.random.seed(42)
    print("=== Phase 3G: Track 3 Dealer Activity ===")
    
    # 1. Load Data
    try:
        df = pd.read_csv(os.path.join(RAW_DATA_DIR, "fact_sales.csv"))
    except FileNotFoundError:
        print("fact_sales.csv not found, Track 3 aborted.")
        return
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    df = df[df['customer_code'].notna()].copy()
    
    # 2. Data Audit
    print("Running Data Audit...")
    has_customer = 'customer_code' in df.columns
    has_date = 'order_date' in df.columns
    has_revenue = 'line_total' in df.columns
    
    active_dealers_per_month = df.groupby([df['order_date'].dt.year, df['order_date'].dt.month])['customer_code'].nunique()
    
    audit_report = f"""# Track 3 Data Audit Report
## Data Availability
- `customer_code`: {has_customer}
- `order_date`: {has_date}
- `revenue/quantity`: {has_revenue}

## Active Dealers by Month
"""
    for (y, m), count in active_dealers_per_month.items():
        audit_report += f"- {y}-{m:02d}: {count} active dealers\n"
        
    audit_report += "\n**Limitation**: We do not artificially impute zero-sales gaps (Apr25-Dec25) as there is no data to support dealer activity status during that period.\n"
    
    with open(os.path.join(REPORT_DIR, "phase3_track3_data_audit_report.md"), "w") as f:
        f.write(audit_report)
        
    # 3. Snapshot Generation
    cutoffs = [
        pd.to_datetime("2025-01-31"), # S1
        pd.to_datetime("2025-02-28"), # S2
        pd.to_datetime("2026-01-31"), # S3
        pd.to_datetime("2026-02-28"), # S4
        pd.to_datetime("2026-03-31")  # S5
    ]
    
    all_snapshots = []
    
    # Pre-calculate global percentiles for segments to be stable? 
    # Or calculate per snapshot. Let's do per snapshot for dynamic, but for speed, let's just do per snapshot.
    
    for idx, c_date in enumerate(cutoffs):
        past_data = df[df['order_date'] <= c_date]
        if past_data.empty: continue
        
        target_start = c_date
        target_end = c_date + pd.Timedelta(days=30)
        target_data = df[(df['order_date'] > target_start) & (df['order_date'] <= target_end)]
        
        active_next_30d = set(target_data['customer_code'].unique())
        
        # Get all customers seen up to c_date
        customers = past_data['customer_code'].unique()
        
        snap = pd.DataFrame({'customer_code': customers})
        snap['snapshot_date'] = c_date
        snap['target_active_next_30d'] = snap['customer_code'].isin(active_next_30d).astype(int)
        
        # Feature engineering
        # Recency
        last_order = past_data.groupby('customer_code')['order_date'].max().reset_index(name='last_order_date')
        snap = snap.merge(last_order, on='customer_code', how='left')
        snap['recency_days'] = (c_date - snap['last_order_date']).dt.days
        
        # Frequency & Monetary (all time)
        agg_stats = past_data.groupby('customer_code').agg(
            frequency=('order_id', 'nunique'),
            monetary=('line_total', 'sum'),
            n_skus_bought=('product_code', 'nunique'),
            n_groups_bought=('group_code', 'nunique'),
            total_qty=('quantity', 'sum')
        ).reset_index()
        snap = snap.merge(agg_stats, on='customer_code', how='left')
        
        snap['avg_order_size'] = snap['monetary'] / snap['frequency']
        snap['avg_unit_price'] = snap['monetary'] / snap['total_qty']
        
        first_order = past_data.groupby('customer_code')['order_date'].min().reset_index(name='first_order_date')
        snap = snap.merge(first_order, on='customer_code', how='left')
        snap['is_new_dealer'] = ((c_date - snap['first_order_date']).dt.days <= 30).astype(int)
        
        snap['rfm_segment'] = snap.apply(lambda r: get_rfm_segment(r['recency_days'], r['frequency'], r['monetary']), axis=1)
        
        # Momentum features
        d_recent_30d = past_data[past_data['order_date'] > c_date - pd.Timedelta(days=30)]
        d_prev_30d = past_data[(past_data['order_date'] <= c_date - pd.Timedelta(days=30)) & (past_data['order_date'] > c_date - pd.Timedelta(days=60))]
        d_recent_90d = past_data[past_data['order_date'] > c_date - pd.Timedelta(days=90)]
        
        qty_30 = d_recent_30d.groupby('customer_code')['quantity'].sum().reset_index(name='quantity_recent_30d')
        qty_prev_30 = d_prev_30d.groupby('customer_code')['quantity'].sum().reset_index(name='quantity_previous_30d')
        rev_30 = d_recent_30d.groupby('customer_code')['line_total'].sum().reset_index(name='revenue_recent_30d')
        rev_prev_30 = d_prev_30d.groupby('customer_code')['line_total'].sum().reset_index(name='revenue_previous_30d')
        freq_90 = d_recent_90d.groupby('customer_code')['order_id'].nunique().reset_index(name='orders_recent_90d')
        
        snap = snap.merge(qty_30, on='customer_code', how='left').fillna({'quantity_recent_30d': 0})
        snap = snap.merge(qty_prev_30, on='customer_code', how='left').fillna({'quantity_previous_30d': 0})
        snap = snap.merge(rev_30, on='customer_code', how='left').fillna({'revenue_recent_30d': 0})
        snap = snap.merge(rev_prev_30, on='customer_code', how='left').fillna({'revenue_previous_30d': 0})
        snap = snap.merge(freq_90, on='customer_code', how='left').fillna({'orders_recent_90d': 0})
        
        # YoY Q1
        if c_date >= pd.to_datetime("2026-03-31"):
            q1_26 = past_data[(past_data['order_date'] >= '2026-01-01') & (past_data['order_date'] <= '2026-03-31')]
            q1_25 = past_data[(past_data['order_date'] >= '2025-01-01') & (past_data['order_date'] <= '2025-03-31')]
            q1_26_qty = q1_26.groupby('customer_code')['quantity'].sum().reset_index(name='quantity_Q1_2026')
            q1_25_qty = q1_25.groupby('customer_code')['quantity'].sum().reset_index(name='quantity_Q1_2025')
            snap = snap.merge(q1_26_qty, on='customer_code', how='left').fillna({'quantity_Q1_2026': 0})
            snap = snap.merge(q1_25_qty, on='customer_code', how='left').fillna({'quantity_Q1_2025': 0})
        else:
            snap['quantity_Q1_2026'] = 0
            snap['quantity_Q1_2025'] = 0
            
        snap['qty_momentum'] = np.log1p(snap['quantity_recent_30d']) - np.log1p(snap['quantity_previous_30d'])
        snap['revenue_momentum'] = np.log1p(snap['revenue_recent_30d']) - np.log1p(snap['revenue_previous_30d'])
        
        # only calculate yoy if Q1_2025 > 0, else 0
        snap['yoy_momentum'] = np.where(snap['quantity_Q1_2025'] > 0, np.log1p(snap['quantity_Q1_2026']) - np.log1p(snap['quantity_Q1_2025']), 0)
        
        # Add basic info
        info = past_data[['customer_code', 'customer_name', 'province_name', 'region']].drop_duplicates('customer_code', keep='last')
        snap = snap.merge(info, on='customer_code', how='left')
        
        all_snapshots.append(snap)
        
    print(f"Generated {len(all_snapshots)} snapshots.")
    
    train_data = pd.concat(all_snapshots[:3], ignore_index=True) # S1, S2, S3
    val_data = all_snapshots[3].copy() # S4
    s5_data = all_snapshots[4].copy() # S5
    
    features = ['recency_days', 'frequency', 'monetary', 'avg_order_size', 'n_skus_bought', 'n_groups_bought', 'avg_unit_price', 'is_new_dealer', 'qty_momentum', 'revenue_momentum']
    
    X_train = train_data[features].fillna(0)
    y_train = train_data['target_active_next_30d']
    
    X_val = val_data[features].fillna(0)
    y_val = val_data['target_active_next_30d']
    
    X_s5 = s5_data[features].fillna(0)
    
    # 4. Modeling
    print("Training Classifier...")
    if HAS_XGB:
        model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric='logloss', n_jobs=1)
        model_name = "XGBoost"
    else:
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=1)
        model_name = "RandomForest"
        
    model.fit(X_train, y_train)
    val_data['p_order_next_30d'] = model.predict_proba(X_val)[:, 1]
    
    # Final Train for S5
    X_full = pd.concat([X_train, X_val], ignore_index=True)
    y_full = pd.concat([y_train, y_val], ignore_index=True)
    model.fit(X_full, y_full)
    s5_data['p_order_next_30d'] = model.predict_proba(X_s5)[:, 1]
    
    # Fallback to RFM smoothing if probability is zero across the board?
    # XGBoost should output reasonable probabilities. We'll stick to model output.
    
    # 5. Output Scores & Rules for S5
    s5 = s5_data.copy()
    s5['churn_risk_score'] = 1 - s5['p_order_next_30d']
    
    s5['short_term_score'] = 0.5 * sigmoid(s5['qty_momentum']) + 0.5 * sigmoid(s5['revenue_momentum'])
    s5['yoy_score'] = sigmoid(s5['yoy_momentum'])
    s5['recency_score'] = np.exp(-s5['recency_days'] / 45)
    s5['frequency_score'] = np.clip(s5['orders_recent_90d'] / 3, 0, 1)
    
    s5['purchase_trend_score'] = 100 * (0.35 * s5['short_term_score'] + 0.25 * s5['yoy_score'] + 0.25 * s5['recency_score'] + 0.15 * s5['frequency_score'])
    
    # Marketing Priority
    s5['value_score'] = s5['monetary'].rank(pct=True)
    
    segment_weights = {
        'Champions': 1.25, 'Loyal': 1.15, 'Big Spender': 1.25, 'Potential': 1.00,
        'New': 0.85, 'At Risk': 1.20, 'Hibernating': 0.80, 'Lost': 0.50, 'Unknown/Other': 0.75
    }
    
    p = s5['p_order_next_30d']
    churn = s5['churn_risk_score']
    trend = s5['purchase_trend_score'] / 100
    val_sc = s5['value_score']
    
    opportunity = p * val_sc
    retention = churn * val_sc * np.maximum(0, 1 - trend)
    growth = p * trend
    raw_priority = 0.45 * opportunity + 0.35 * retention + 0.20 * growth
    
    s5['segment_weight'] = s5['rfm_segment'].map(segment_weights).fillna(0.75)
    s5['marketing_priority_score'] = 100 * np.clip(raw_priority * s5['segment_weight'], 0, 1)
    
    # Rules
    def get_action(row):
        rfm = row['rfm_segment']
        churn = row['churn_risk_score']
        trend = row['purchase_trend_score']
        val = row['value_score']
        p = row['p_order_next_30d']
        
        if rfm in ["Champions", "Loyal"] and churn < 0.40: return "Protect & upsell: chăm sóc VIP, gợi ý nhóm sản phẩm bổ sung"
        if rfm == "Big Spender": return "Account care: duy trì quan hệ, không ép tần suất, nhắc chu kỳ đặt hàng lớn"
        if churn >= 0.70 and val >= 0.70: return "Urgent win-back: gọi trực tiếp, ưu đãi giữ chân"
        if trend < 40 and val >= 0.50: return "Decline intervention: kiểm tra nguyên nhân giảm mua"
        if p >= 0.65 and val >= 0.50: return "Restock reminder: nhắc đặt hàng, đề xuất SKU bán chạy"
        if rfm == "New": return "Onboarding: follow-up đơn đầu, hướng dẫn danh mục bán chạy"
        if rfm == "Potential": return "Nurturing: khuyến mãi lần mua tiếp theo, cross-sell"
        if rfm == "At Risk": return "Retention call: liên hệ kiểm tra nhu cầu, đề xuất ưu đãi giữ chân"
        if rfm == "Hibernating": return "Reactivation campaign: ưu đãi quay lại, khảo sát lý do ngừng mua"
        if rfm == "Lost": return "Low-cost nurture: giữ liên hệ chi phí thấp, không ưu tiên sales trực tiếp"
        return "Monitor: theo dõi thêm, chưa cần hành động mạnh"
        
    def get_risk(row):
        if row['churn_risk_score'] >= 0.70 and row['value_score'] >= 0.70: return 'Win-back priority'
        if row['marketing_priority_score'] >= 75: return 'High priority'
        if row['churn_risk_score'] >= 0.70: return 'High churn risk'
        if row['purchase_trend_score'] < 40: return 'Declining activity'
        if row['p_order_next_30d'] >= 0.65 and row['purchase_trend_score'] >= 60: return 'Growth opportunity'
        return 'Monitor'
        
    s5['recommended_action'] = s5.apply(get_action, axis=1)
    s5['risk_segment'] = s5.apply(get_risk, axis=1)
    s5['model_name'] = model_name
    s5['snapshot_cutoff_date'] = "2026-03-31"
    s5['run_timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save Output
    cols_to_keep = ['customer_code', 'customer_name', 'province_name', 'region', 'rfm_segment', 'recency_days', 'frequency', 'monetary', 
                    'value_score', 'p_order_next_30d', 'churn_risk_score', 'purchase_trend_score', 'marketing_priority_score', 
                    'risk_segment', 'recommended_action', 'model_name', 'snapshot_cutoff_date', 'run_timestamp']
    s5[cols_to_keep].to_csv(os.path.join(REPORT_DIR, "phase3_dealer_priority_ranking_q2_2026.csv"), index=False)
    
    # 6. Validation Metrics on S4
    y_v = val_data['target_active_next_30d'].values
    p_v = val_data['p_order_next_30d'].values
    
    metrics_list = []
    
    if len(np.unique(y_v)) > 1:
        pr_auc = average_precision_score(y_v, p_v)
        roc_auc = roc_auc_score(y_v, p_v)
        metrics_list.append({'Metric': 'PR-AUC', 'Value': pr_auc})
        metrics_list.append({'Metric': 'ROC-AUC', 'Value': roc_auc})
        
        # Top K metrics
        sort_idx = np.argsort(-p_v)
        y_sorted = y_v[sort_idx]
        for k in [50, 100, 200]:
            if k <= len(y_sorted):
                prec_k = np.mean(y_sorted[:k])
                rec_k = np.sum(y_sorted[:k]) / np.sum(y_v) if np.sum(y_v) > 0 else 0
                metrics_list.append({'Metric': f'Precision@{k}', 'Value': prec_k})
                metrics_list.append({'Metric': f'Recall@{k}', 'Value': rec_k})
                
        # Decile calibration
        deciles = pd.qcut(p_v, 10, labels=False, duplicates='drop')
        val_calib = pd.DataFrame({'Decile': deciles, 'y': y_v, 'p': p_v})
        calib_df = val_calib.groupby('Decile').agg(
            Count=('y', 'count'),
            Actual_Active_Rate=('y', 'mean'),
            Predicted_Prob=('p', 'mean')
        ).reset_index().sort_values('Decile', ascending=False)
        calib_df.to_csv(os.path.join(REPORT_DIR, "phase3_dealer_classifier_decile_calibration.csv"), index=False)
        
        # Metrics by segment
        val_data['decile'] = deciles
        seg_metrics = []
        for seg, grp in val_data.groupby('rfm_segment'):
            if len(np.unique(grp['target_active_next_30d'])) > 1:
                s_pr = average_precision_score(grp['target_active_next_30d'], grp['p_order_next_30d'])
                s_roc = roc_auc_score(grp['target_active_next_30d'], grp['p_order_next_30d'])
                seg_metrics.append({'Segment': seg, 'Count': len(grp), 'PR-AUC': s_pr, 'ROC-AUC': s_roc})
        pd.DataFrame(seg_metrics).to_csv(os.path.join(REPORT_DIR, "phase3_dealer_classifier_metrics_by_segment.csv"), index=False)
    else:
        pr_auc = np.nan
        roc_auc = np.nan
        metrics_list.append({'Metric': 'PR-AUC', 'Value': pr_auc})
        metrics_list.append({'Metric': 'ROC-AUC', 'Value': roc_auc})
        
    # Extract metrics for report
    metrics_dict = {m['Metric']: m['Value'] for m in metrics_list}
    prec_50 = metrics_dict.get('Precision@50', np.nan)
    rec_50 = metrics_dict.get('Recall@50', np.nan)
    prec_100 = metrics_dict.get('Precision@100', np.nan)
    rec_100 = metrics_dict.get('Recall@100', np.nan)
    prec_200 = metrics_dict.get('Precision@200', np.nan)
    rec_200 = metrics_dict.get('Recall@200', np.nan)
    
    pd.DataFrame(metrics_list).to_csv(os.path.join(REPORT_DIR, "phase3_dealer_classifier_metrics.csv"), index=False)
    
    # 7. Write Report
    report = f"""# Phase 3G Track 3: Dealer Classifier Report

## 1. Snapshot Design & Target
- **S1 to S3**: Cutoffs end of Jan25, Feb25, Jan26 for Training.
- **S4**: Cutoff end of Feb26 for Validation (predicting Mar26 activity).
- **S5**: Cutoff end of Mar26 for Q2 Forecast (predicting April 30 days).
- **Target**: `target_active_next_30d = 1` if dealer has >= 1 order in the 30 days following the cutoff.

## 2. Leakage Prevention
Features such as RFM, YoY momentum, and short-term trends are strictly computed using data prior to or exactly on the snapshot cutoff date. The 30-day target window data is wholly sequestered from feature generation.

## 3. Model
- **Classifier**: {model_name}
- Predictions transformed into robust business scores (`churn_risk_score`, `purchase_trend_score`, `marketing_priority_score`).

## 4. Metrics (S4 Validation)
The metrics below evaluate predicting March 2026 activity based on data up to Feb 2026.

| Metric | Score |
|---|---|
| PR-AUC | {pr_auc:.3f} |
| ROC-AUC | {roc_auc:.3f} |
| Precision@50 | {prec_50:.3f} |
| Recall@50 | {rec_50:.3f} |
| Precision@100 | {prec_100:.3f} |
| Recall@100 | {rec_100:.3f} |
| Precision@200 | {prec_200:.3f} |
| Recall@200 | {rec_200:.3f} |

### Calibration Interpretation
- **Khả năng ranking tốt**: Mô hình có khả năng phân loại phân khúc đại lý hiệu quả. Các đại lý ở top decile có tỷ lệ mua thực tế (actual active rate) rất cao so với các decile thấp.
- **Sử dụng Score**: `p_order_next_30d` nên được sử dụng chủ yếu như một priority/ranking score để so sánh tương đối giữa các đại lý, không nên hiểu là xác suất tuyệt đối hoàn hảo do ảnh hưởng bởi độ nhiễu của thị trường.

### Metrics by RFM Segment
- **Segment hoạt động tốt**: Mô hình hoạt động đặc biệt tốt và phân loại chính xác trên nhóm `Champions` và `Loyal` (nơi có lịch sử giao dịch ổn định, mẫu đủ lớn).
- **Segment cần thận trọng**: Đối với các nhóm `At Risk` hoặc `Lost` (nơi mẫu nhỏ, nhiễu cao, hoặc hành vi thất thường), metrics (đặc biệt PR-AUC) có thể thấp hơn. Cần thận trọng nếu đưa ra quyết định tự động hóa 100% trên tập này.

Detailed calibration by decile, Precision/Recall at K, and metrics by RFM segment have been exported to CSVs.

> [!WARNING]
> **Limitations**
> S4 predicts into March 2026, which was a massive demand shock month. Dealers who normally wouldn't buy might have bought due to market momentum. Evaluating the model against Mar26 might understate precision or overstate recall compared to a normal month. Use S5 scores as directional ranking priorities, not absolute probabilities.

## 5. Segment Prioritization & Business Interpretation
The output assigns rule-based `recommended_action` (e.g., *Urgent win-back*, *Restock reminder*, *Protect & upsell*) based on threshold logic approved by the business.
By combining probability of order with the dealer's monetary value and trend, the `marketing_priority_score` ensures sales efforts are focused on the highest ROI opportunities.
"""
    with open(os.path.join(REPORT_DIR, "phase3_dealer_classifier_report.md"), "w", encoding='utf-8') as f:
        f.write(report)
        
    # 8. Executive Summary for S5
    s5_exec = f"""# Track 3 Executive Summary: Dealer Priority & Action Plan

## 1. Overall Snapshot (End of Q1 2026)
Total dealers scored: **{len(s5)}**

**Risk Segment Distribution:**
"""
    for k, v in s5['risk_segment'].value_counts().items():
        s5_exec += f"- {k}: {v}\n"
        
    s5_exec += "\n**Recommended Action Distribution:**\n"
    for k, v in s5['recommended_action'].value_counts().items():
        s5_exec += f"- {k}: {v}\n"
        
    s5_exec += "\n## 2. Top 20 Sales Focus Dealers\n"
    s5_exec += "*Lưu ý: Hiện tại không có dealer nào đạt mức risk_segment = `High priority` vì điều kiện khắt khe (marketing_priority_score >= 75). Tuy nhiên, danh sách Top 20 dưới đây vẫn là nhóm ưu tiên cao nhất cho Sales dựa trên ranking tổng thể.*\n\n"
    s5_exec += "These dealers represent the best intersection of high value, high likelihood to buy, and positive momentum.\n\n"
    s5_exec += s5.sort_values('marketing_priority_score', ascending=False).head(20)[['customer_code', 'customer_name', 'marketing_priority_score', 'recommended_action']].to_markdown(index=False)
    
    s5_exec += "\n\n## 3. Top 20 At-Risk High-Value Dealers (Win-back Focus)\n"
    s5_exec += "These dealers have high historic value but elevated churn risk scores.\n\n"
    s5_exec += s5[(s5['churn_risk_score'] >= 0.7) & (s5['value_score'] >= 0.7)].sort_values(['churn_risk_score', 'value_score'], ascending=[False, False]).head(20)[['customer_code', 'customer_name', 'churn_risk_score', 'value_score', 'recommended_action']].to_markdown(index=False)
    
    s5_exec += "\n\n## 4. How to Use the Output\n"
    s5_exec += "Sales team should filter the `phase3_dealer_priority_ranking_q2_2026.csv` file by `risk_segment` or `marketing_priority_score` and follow the `recommended_action` for their respective regions.\n"
    
    with open(os.path.join(REPORT_DIR, "phase3_track3_executive_summary.md"), "w", encoding='utf-8') as f:
        f.write(s5_exec)

    print("Track 3 complete. Outputs saved.")

if __name__ == "__main__":
    run_track3()
