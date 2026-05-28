# Phase 3G Track 3: Dealer Classifier Report

## 1. Snapshot Design & Target
- **S1 to S3**: Cutoffs end of Jan25, Feb25, Jan26 for Training.
- **S4**: Cutoff end of Feb26 for Validation (predicting Mar26 activity).
- **S5**: Cutoff end of Mar26 for Q2 Forecast (predicting April 30 days).
- **Target**: `target_active_next_30d = 1` if dealer has >= 1 order in the 30 days following the cutoff.

## 2. Leakage Prevention
Features such as RFM, YoY momentum, and short-term trends are strictly computed using data prior to or exactly on the snapshot cutoff date. The 30-day target window data is wholly sequestered from feature generation.

## 3. Model
- **Classifier**: XGBoost
- Predictions transformed into robust business scores (`churn_risk_score`, `purchase_trend_score`, `marketing_priority_score`).

## 4. Metrics (S4 Validation)
The metrics below evaluate predicting March 2026 activity based on data up to Feb 2026.

| Metric | Score |
|---|---|
| PR-AUC | 0.805 |
| ROC-AUC | 0.901 |
| Precision@50 | 0.840 |
| Recall@50 | 0.143 |
| Precision@100 | 0.850 |
| Recall@100 | 0.289 |
| Precision@200 | 0.825 |
| Recall@200 | 0.561 |

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
