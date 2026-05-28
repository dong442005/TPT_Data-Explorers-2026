"""
EDA — Phân tích phân bố R/F/M thực tế từ Database TNBike
=========================================================
Mục đích: Xem data thực tế TRƯỚC khi quyết định scoring method (NTILE vs Manual thresholds)
Kết nối: PostgreSQL localhost / tnbike_db / schema tnbike
Output : Console + biểu đồ PNG lưu vào thư mục eda_output/
"""

import psycopg2
import sys, io, os
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Thử import matplotlib, nếu chưa có thì thông báo ---
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("⚠️  matplotlib chưa cài — chỉ xuất số liệu console, không vẽ biểu đồ.")
    print("    Cài bằng: pip install matplotlib\n")

# ============================================================
# 0. KẾT NỐI DATABASE
# ============================================================
import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = dict(
    dbname=os.getenv('DB_NAME', 'tnbike_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('SET search_path TO tnbike, public;')

# Thư mục output
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eda_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 1. TRUY VẤN RFM RAW — Tính R, F, M cho mỗi đại lý
# ============================================================
print("=" * 70)
print("  EDA — PHÂN BỐ R / F / M THỰC TẾ CỦA 798 ĐẠI LÝ TNBIKE")
print("  Mốc tính Recency: 2026-03-31 (ngày cuối cùng có data)")
print("=" * 70)

RFM_QUERY = """
SELECT
    f.customer_code,
    c.customer_name,
    c.customer_tier,
    COALESCE(pr.province_name, 'Chưa xác định') AS province_name,
    COALESCE(pr.region, 'Chưa xác định') AS region,
    MAX(f.order_date) AS last_order_date,
    DATE '2026-03-31' - MAX(f.order_date) AS recency_days,
    COUNT(DISTINCT f.so_number) AS frequency,
    SUM(f.line_total) AS monetary
FROM tnbike.fact_sales f
JOIN tnbike.customer c ON c.customer_code = f.customer_code
LEFT JOIN tnbike.province pr ON pr.province_id = c.province_id
GROUP BY f.customer_code, c.customer_name, c.customer_tier,
         pr.province_name, pr.region
ORDER BY monetary DESC;
"""

cur.execute(RFM_QUERY)
rows = cur.fetchall()
columns = [desc[0] for desc in cur.description]

# Chuyển thành dict list để dễ xử lý
data = []
for r in rows:
    data.append(dict(zip(columns, r)))

n = len(data)
print(f"\n📊 Tổng số đại lý có giao dịch: {n}\n")

# Trích xuất arrays
recency_arr = np.array([d['recency_days'] for d in data], dtype=float)
frequency_arr = np.array([d['frequency'] for d in data], dtype=float)
monetary_arr = np.array([d['monetary'] for d in data], dtype=float)

# ============================================================
# 2. THỐNG KÊ MÔ TẢ (Descriptive Statistics)
# ============================================================
def print_stats(name, arr, unit=""):
    """In thống kê mô tả cho 1 mảng"""
    pcts = [5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]
    percentiles = np.percentile(arr, pcts)
    
    print(f"\n{'─' * 60}")
    print(f"  📈 {name}")
    print(f"{'─' * 60}")
    print(f"  Count:   {len(arr)}")
    print(f"  Mean:    {np.mean(arr):,.1f} {unit}")
    print(f"  Std:     {np.std(arr):,.1f} {unit}")
    print(f"  Min:     {np.min(arr):,.0f} {unit}")
    print(f"  Max:     {np.max(arr):,.0f} {unit}")
    print(f"  Skew:    {skewness(arr):.2f}  {'(lệch phải ↗)' if skewness(arr) > 0.5 else '(khá đối xứng)' if abs(skewness(arr)) < 0.5 else '(lệch trái ↙)'}")
    print()
    print(f"  {'Percentile':>12}  {'Value':>15}")
    print(f"  {'─'*12}  {'─'*15}")
    for p, v in zip(pcts, percentiles):
        marker = ""
        if p == 50:
            marker = " ◄ MEDIAN"
        elif p in (20, 40, 60, 80):
            marker = f" ◄ P{p} (NTILE boundary)"
        print(f"  {'P' + str(p):>12}  {v:>15,.0f} {unit}{marker}")
    
    return dict(zip(pcts, percentiles))

def skewness(arr):
    """Tính skewness (độ lệch)"""
    m = np.mean(arr)
    s = np.std(arr)
    if s == 0:
        return 0
    return np.mean(((arr - m) / s) ** 3)

r_pcts = print_stats("RECENCY (ngày kể từ lần mua cuối → 2026-03-31)", recency_arr, "ngày")
f_pcts = print_stats("FREQUENCY (số đơn hàng duy nhất)", frequency_arr, "đơn")
m_pcts = print_stats("MONETARY (tổng chi tiêu VND)", monetary_arr, "VND")

# ============================================================
# 3. PHÂN BỐ TẦN SUẤT (Frequency Distribution Table)
# ============================================================
print(f"\n{'=' * 60}")
print(f"  📊 BẢNG PHÂN BỐ TẦN SUẤT CHI TIẾT")
print(f"{'=' * 60}")

# --- Recency bins ---
print(f"\n  ▸ RECENCY — Phân bố theo khoảng ngày")
r_bins = [(0, 7), (8, 14), (15, 30), (31, 60), (61, 90), (91, 180), (181, 365), (366, 9999)]
r_labels = ["0-7 ngày", "8-14 ngày", "15-30 ngày", "31-60 ngày", "61-90 ngày", 
            "91-180 ngày", "181-365 ngày", ">365 ngày"]
print(f"  {'Khoảng':<18} {'Số DL':>8} {'Tỷ lệ':>8} {'Tích lũy':>10}  {'Bar'}")
cumul = 0
for (lo, hi), label in zip(r_bins, r_labels):
    count = np.sum((recency_arr >= lo) & (recency_arr <= hi))
    pct = count / n * 100
    cumul += pct
    bar = "█" * int(pct / 2)
    print(f"  {label:<18} {count:>8,} {pct:>7.1f}% {cumul:>9.1f}%  {bar}")

# --- Frequency bins ---
print(f"\n  ▸ FREQUENCY — Phân bố theo số đơn hàng")
f_bins = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 9), (10, 19), (20, 49), (50, 9999)]
f_labels = ["1 đơn", "2 đơn", "3 đơn", "4-5 đơn", "6-9 đơn", 
            "10-19 đơn", "20-49 đơn", "50+ đơn"]
print(f"  {'Khoảng':<18} {'Số DL':>8} {'Tỷ lệ':>8} {'Tích lũy':>10}  {'Bar'}")
cumul = 0
for (lo, hi), label in zip(f_bins, f_labels):
    count = np.sum((frequency_arr >= lo) & (frequency_arr <= hi))
    pct = count / n * 100
    cumul += pct
    bar = "█" * int(pct / 2)
    print(f"  {label:<18} {count:>8,} {pct:>7.1f}% {cumul:>9.1f}%  {bar}")

# --- Monetary bins ---
print(f"\n  ▸ MONETARY — Phân bố theo tổng chi tiêu (VND)")
m_bins_val = [0, 5e6, 10e6, 30e6, 50e6, 100e6, 300e6, 500e6, 1e9, 5e9, float('inf')]
m_labels_m = ["<5 triệu", "5-10 triệu", "10-30 triệu", "30-50 triệu", "50-100 triệu",
              "100-300 triệu", "300-500 triệu", "500 triệu-1 tỷ", "1-5 tỷ", ">5 tỷ"]
print(f"  {'Khoảng':<20} {'Số DL':>8} {'Tỷ lệ':>8} {'Tích lũy':>10} {'Tổng DT (tỷ)':>14}  {'Bar'}")
cumul = 0
for i in range(len(m_labels_m)):
    lo = m_bins_val[i]
    hi = m_bins_val[i + 1]
    mask = (monetary_arr >= lo) & (monetary_arr < hi)
    count = np.sum(mask)
    pct = count / n * 100
    cumul += pct
    total_rev = np.sum(monetary_arr[mask]) / 1e9
    bar = "█" * int(pct / 2)
    print(f"  {m_labels_m[i]:<20} {count:>8,} {pct:>7.1f}% {cumul:>9.1f}% {total_rev:>13.2f}  {bar}")

# ============================================================
# 4. CROSS-TAB: R/F/M vs CUSTOMER_TIER
# ============================================================
print(f"\n{'=' * 60}")
print(f"  📊 CROSS-TAB: CUSTOMER_TIER × R/F/M")
print(f"{'=' * 60}")

# Tier distribution
tiers = {}
for d in data:
    tier = d.get('customer_tier') or 'NULL'
    if tier not in tiers:
        tiers[tier] = {'count': 0, 'recency': [], 'frequency': [], 'monetary': []}
    tiers[tier]['count'] += 1
    tiers[tier]['recency'].append(float(d['recency_days']))
    tiers[tier]['frequency'].append(float(d['frequency']))
    tiers[tier]['monetary'].append(float(d['monetary']))

print(f"\n  {'Tier':<12} {'Count':>7} {'Avg Recency':>13} {'Avg Freq':>10} {'Avg Monetary':>16} {'Med Monetary':>16}")
print(f"  {'─'*12} {'─'*7} {'─'*13} {'─'*10} {'─'*16} {'─'*16}")
for tier in sorted(tiers.keys()):
    t = tiers[tier]
    r_arr = np.array(t['recency'])
    f_arr_t = np.array(t['frequency'])
    m_arr = np.array(t['monetary'])
    print(f"  {tier:<12} {t['count']:>7,} {np.mean(r_arr):>12.0f}d {np.mean(f_arr_t):>9.1f} {np.mean(m_arr):>15,.0f} {np.median(m_arr):>15,.0f}")

# ============================================================
# 5. PHÂN BỐ THEO REGION
# ============================================================
print(f"\n{'=' * 60}")
print(f"  📊 CROSS-TAB: REGION × R/F/M")
print(f"{'=' * 60}")

regions = {}
for d in data:
    region = d['region']
    if region not in regions:
        regions[region] = {'count': 0, 'recency': [], 'frequency': [], 'monetary': []}
    regions[region]['count'] += 1
    regions[region]['recency'].append(float(d['recency_days']))
    regions[region]['frequency'].append(float(d['frequency']))
    regions[region]['monetary'].append(float(d['monetary']))

print(f"\n  {'Region':<18} {'Count':>7} {'Avg R':>8} {'Avg F':>8} {'Avg M (triệu)':>16} {'Med M (triệu)':>16}")
print(f"  {'─'*18} {'─'*7} {'─'*8} {'─'*8} {'─'*16} {'─'*16}")
for region in sorted(regions.keys()):
    t = regions[region]
    r_arr = np.array(t['recency'])
    f_arr_t = np.array(t['frequency'])
    m_arr = np.array(t['monetary'])
    print(f"  {region:<18} {t['count']:>7,} {np.mean(r_arr):>7.0f}d {np.mean(f_arr_t):>7.1f} {np.mean(m_arr)/1e6:>15,.1f} {np.median(m_arr)/1e6:>15,.1f}")

# ============================================================
# 6. SPOT-CHECK: TOP 10 + BOTTOM 10 ĐẠI LÝ
# ============================================================
print(f"\n{'=' * 60}")
print(f"  🔍 SPOT-CHECK: TOP 10 ĐẠI LÝ (Monetary cao nhất)")
print(f"{'=' * 60}")
print(f"\n  {'#':>3} {'KH Code':<12} {'Tier':<10} {'Region':<15} {'Recency':>8} {'Freq':>5} {'Monetary':>18}")
print(f"  {'─'*3} {'─'*12} {'─'*10} {'─'*15} {'─'*8} {'─'*5} {'─'*18}")
for i, d in enumerate(data[:10]):
    tier = d.get('customer_tier') or 'N/A'
    print(f"  {i+1:>3} {d['customer_code']:<12} {tier:<10} {d['region']:<15} {int(d['recency_days']):>7}d {int(d['frequency']):>5} {float(d['monetary']):>17,.0f}")

print(f"\n  🔍 BOTTOM 10 ĐẠI LÝ (Monetary thấp nhất)")
print(f"\n  {'#':>3} {'KH Code':<12} {'Tier':<10} {'Region':<15} {'Recency':>8} {'Freq':>5} {'Monetary':>18}")
print(f"  {'─'*3} {'─'*12} {'─'*10} {'─'*15} {'─'*8} {'─'*5} {'─'*18}")
for i, d in enumerate(data[-10:]):
    tier = d.get('customer_tier') or 'N/A'
    idx = n - 10 + i + 1
    print(f"  {idx:>3} {d['customer_code']:<12} {tier:<10} {d['region']:<15} {int(d['recency_days']):>7}d {int(d['frequency']):>5} {float(d['monetary']):>17,.0f}")

# ============================================================
# 7. ĐẠI LÝ CÓ RECENCY CAO NHẤT (lâu nhất không mua)
# ============================================================
print(f"\n{'=' * 60}")
print(f"  🔍 TOP 10 ĐẠI LÝ RECENCY CAO NHẤT (lâu nhất không mua)")
print(f"{'=' * 60}")
data_by_recency = sorted(data, key=lambda x: x['recency_days'], reverse=True)
print(f"\n  {'#':>3} {'KH Code':<12} {'Tier':<10} {'Last Order':<12} {'Recency':>8} {'Freq':>5} {'Monetary':>18}")
print(f"  {'─'*3} {'─'*12} {'─'*10} {'─'*12} {'─'*8} {'─'*5} {'─'*18}")
for i, d in enumerate(data_by_recency[:10]):
    tier = d.get('customer_tier') or 'N/A'
    print(f"  {i+1:>3} {d['customer_code']:<12} {tier:<10} {str(d['last_order_date']):<12} {int(d['recency_days']):>7}d {int(d['frequency']):>5} {float(d['monetary']):>17,.0f}")

# ============================================================
# 8. PHÂN TÍCH KHOẢNG CÁCH CỤM RECENCY (Gap analysis)
# ============================================================
print(f"\n{'=' * 60}")
print(f"  📊 GAP ANALYSIS — Phân bố Recency theo tháng cuối cùng mua")
print(f"{'=' * 60}")

# Nhóm theo tháng mua cuối cùng
cur.execute("""
    SELECT 
        EXTRACT(YEAR FROM MAX(order_date))::int AS last_year,
        EXTRACT(MONTH FROM MAX(order_date))::int AS last_month,
        COUNT(DISTINCT customer_code) AS dealer_count
    FROM tnbike.fact_sales
    GROUP BY customer_code
    ORDER BY last_year, last_month;
""")
# Aggregate by year-month
period_counts = {}
for r in cur.fetchall():
    key = f"{int(r[0])}-T{int(r[1]):02d}"
    period_counts[key] = period_counts.get(key, 0) + r[2]

print(f"\n  {'Tháng mua cuối':<18} {'Số ĐL':>8} {'Tỷ lệ':>8}  {'Bar'}")
print(f"  {'─'*18} {'─'*8} {'─'*8}  {'─'*30}")
for period in sorted(period_counts.keys()):
    count = period_counts[period]
    pct = count / n * 100
    bar = "█" * int(pct / 1.5)
    print(f"  {period:<18} {count:>8,} {pct:>7.1f}%  {bar}")

# ============================================================
# 9. SO SÁNH NTILE vs MANUAL SCORING (Preview)
# ============================================================
print(f"\n{'=' * 60}")
print(f"  ⚖️  SO SÁNH: NTILE(5) vs MANUAL THRESHOLDS — Preview")
print(f"{'=' * 60}")

# NTILE scoring (simulated)
r_sorted_idx = np.argsort(recency_arr)   # ASC → nhỏ nhất = rank thấp nhất
f_sorted_idx = np.argsort(-frequency_arr) # DESC
m_sorted_idx = np.argsort(-monetary_arr)  # DESC

def ntile_score(arr, ascending=True):
    """Simulate NTILE(5): chia đều thành 5 nhóm"""
    n_val = len(arr)
    if ascending:
        sorted_idx = np.argsort(arr)
    else:
        sorted_idx = np.argsort(-arr)
    scores = np.zeros(n_val, dtype=int)
    for i, idx in enumerate(sorted_idx):
        scores[idx] = (i * 5) // n_val + 1
    return scores

def manual_r_score(recency):
    if recency <= 30:  return 5
    if recency <= 60:  return 4
    if recency <= 90:  return 3
    if recency <= 180: return 2
    return 1

def manual_f_score(freq):
    if freq >= 10: return 5
    if freq >= 6:  return 4
    if freq >= 3:  return 3
    if freq >= 2:  return 2
    return 1

def manual_m_score(monetary):
    if monetary >= 1e9:   return 5
    if monetary >= 3e8:   return 4
    if monetary >= 1e8:   return 3
    if monetary >= 3e7:   return 2
    return 1

# Tính scores
ntile_r = ntile_score(recency_arr, ascending=True)
ntile_f = ntile_score(frequency_arr, ascending=False)
ntile_m = ntile_score(monetary_arr, ascending=False)

manual_r = np.array([manual_r_score(r) for r in recency_arr])
manual_f = np.array([manual_f_score(f) for f in frequency_arr])
manual_m = np.array([manual_m_score(m) for m in monetary_arr])

# Phân bố điểm
print("\n  ▸ RECENCY SCORE — Phân bố")
print(f"  {'Điểm':>6}  {'NTILE(5)':>10}  {'Manual':>10}  {'NTILE %':>9}  {'Manual %':>9}")
print(f"  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*9}  {'─'*9}")
for s in range(1, 6):
    n_ntile = np.sum(ntile_r == s)
    n_manual = np.sum(manual_r == s)
    print(f"  {s:>6}  {n_ntile:>10,}  {n_manual:>10,}  {n_ntile/n*100:>8.1f}%  {n_manual/n*100:>8.1f}%")

print("\n  ▸ FREQUENCY SCORE — Phân bố")
print(f"  {'Điểm':>6}  {'NTILE(5)':>10}  {'Manual':>10}  {'NTILE %':>9}  {'Manual %':>9}")
print(f"  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*9}  {'─'*9}")
for s in range(1, 6):
    n_ntile = np.sum(ntile_f == s)
    n_manual = np.sum(manual_f == s)
    print(f"  {s:>6}  {n_ntile:>10,}  {n_manual:>10,}  {n_ntile/n*100:>8.1f}%  {n_manual/n*100:>8.1f}%")

print("\n  ▸ MONETARY SCORE — Phân bố")
print(f"  {'Điểm':>6}  {'NTILE(5)':>10}  {'Manual':>10}  {'NTILE %':>9}  {'Manual %':>9}")
print(f"  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*9}  {'─'*9}")
for s in range(1, 6):
    n_ntile = np.sum(ntile_m == s)
    n_manual = np.sum(manual_m == s)
    print(f"  {s:>6}  {n_ntile:>10,}  {n_manual:>10,}  {n_ntile/n*100:>8.1f}%  {n_manual/n*100:>8.1f}%")

# ============================================================
# 10. SPOT-CHECK: Cùng 5 đại lý — so sánh segment
# ============================================================
print(f"\n{'=' * 60}")
print(f"  🔍 SPOT-CHECK: So sánh Scoring cho từng đại lý cụ thể")
print(f"{'=' * 60}")

# Lấy một số đại lý đáng chú ý
check_indices = list(range(5)) + list(range(n-5, n))  # Top 5 + Bottom 5
# Thêm đại lý ở giữa
mid = n // 2
check_indices += [mid - 1, mid, mid + 1]

print(f"\n  {'KH Code':<12} {'Tier':<8} {'R_days':>7} {'Freq':>5} {'M(triệu)':>11} │ {'R_nt':>4} {'F_nt':>4} {'M_nt':>4} │ {'R_mn':>4} {'F_mn':>4} {'M_mn':>4} │ {'Chênh lệch?'}")
print(f"  {'─'*12} {'─'*8} {'─'*7} {'─'*5} {'─'*11} │ {'─'*4} {'─'*4} {'─'*4} │ {'─'*4} {'─'*4} {'─'*4} │ {'─'*12}")

for i in sorted(set(check_indices)):
    if i < 0 or i >= n:
        continue
    d = data[i]
    tier = (d.get('customer_tier') or 'N/A')[:7]
    rn = ntile_r[i]; fn = ntile_f[i]; mn = ntile_m[i]
    rm = manual_r[i]; fm = manual_f[i]; mm = manual_m[i]
    diff = "⚠️ KHÁC" if (rn != rm or fn != fm or mn != mm) else "✅ Giống"
    print(f"  {d['customer_code']:<12} {tier:<8} {int(d['recency_days']):>7} {int(d['frequency']):>5} {float(d['monetary'])/1e6:>10,.1f} │ {rn:>4} {fn:>4} {mn:>4} │ {rm:>4} {fm:>4} {mm:>4} │ {diff}")

# ============================================================
# 11. VẼ BIỂU ĐỒ (nếu có matplotlib)
# ============================================================
if HAS_PLOT:
    print(f"\n{'=' * 60}")
    print(f"  📊 ĐANG VẼ BIỂU ĐỒ...")
    print(f"{'=' * 60}")
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle('EDA — Phân bố R/F/M của 798 Đại lý TNBike', fontsize=16, fontweight='bold')
    
    # --- Row 1: Recency ---
    # Histogram
    ax = axes[0, 0]
    ax.hist(recency_arr, bins=50, color='#4C72B0', edgecolor='white', alpha=0.85)
    ax.axvline(np.median(recency_arr), color='red', linestyle='--', label=f'Median = {np.median(recency_arr):.0f}')
    ax.axvline(np.mean(recency_arr), color='orange', linestyle='--', label=f'Mean = {np.mean(recency_arr):.0f}')
    # Ngưỡng manual
    for thresh, lbl in [(30, '30d'), (60, '60d'), (90, '90d'), (180, '180d')]:
        ax.axvline(thresh, color='green', linestyle=':', alpha=0.6)
        ax.text(thresh, ax.get_ylim()[1]*0.9, lbl, rotation=90, fontsize=8, color='green')
    ax.set_title('Recency (ngày) — Histogram', fontweight='bold')
    ax.set_xlabel('Recency (ngày)')
    ax.set_ylabel('Số đại lý')
    ax.legend(fontsize=9)
    
    # Boxplot
    ax = axes[0, 1]
    bp = ax.boxplot(recency_arr, vert=False, widths=0.7,
                    boxprops=dict(color='#4C72B0'), medianprops=dict(color='red', linewidth=2))
    ax.set_title('Recency (ngày) — Boxplot', fontweight='bold')
    ax.set_xlabel('Recency (ngày)')
    
    # --- Row 2: Frequency ---
    ax = axes[1, 0]
    max_f = int(np.max(frequency_arr))
    bins_f = list(range(1, min(max_f + 2, 30))) + ([max_f + 1] if max_f >= 30 else [])
    ax.hist(frequency_arr, bins=bins_f, color='#55A868', edgecolor='white', alpha=0.85)
    ax.axvline(np.median(frequency_arr), color='red', linestyle='--', label=f'Median = {np.median(frequency_arr):.0f}')
    ax.axvline(np.mean(frequency_arr), color='orange', linestyle='--', label=f'Mean = {np.mean(frequency_arr):.1f}')
    for thresh, lbl in [(2, '2'), (3, '3'), (6, '6'), (10, '10')]:
        ax.axvline(thresh - 0.5, color='green', linestyle=':', alpha=0.6)
        ax.text(thresh - 0.3, ax.get_ylim()[1]*0.85, lbl, fontsize=8, color='green')
    ax.set_title('Frequency (số đơn) — Histogram', fontweight='bold')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Số đại lý')
    ax.legend(fontsize=9)
    
    ax = axes[1, 1]
    ax.boxplot(frequency_arr, vert=False, widths=0.7,
               boxprops=dict(color='#55A868'), medianprops=dict(color='red', linewidth=2))
    ax.set_title('Frequency — Boxplot', fontweight='bold')
    ax.set_xlabel('Số đơn hàng')
    
    # --- Row 3: Monetary ---
    ax = axes[2, 0]
    ax.hist(monetary_arr / 1e6, bins=50, color='#C44E52', edgecolor='white', alpha=0.85)
    ax.axvline(np.median(monetary_arr) / 1e6, color='blue', linestyle='--', label=f'Median = {np.median(monetary_arr)/1e6:,.0f}M')
    ax.axvline(np.mean(monetary_arr) / 1e6, color='orange', linestyle='--', label=f'Mean = {np.mean(monetary_arr)/1e6:,.0f}M')
    for thresh, lbl in [(30, '30M'), (100, '100M'), (300, '300M'), (1000, '1B')]:
        ax.axvline(thresh, color='green', linestyle=':', alpha=0.6)
        ax.text(thresh, ax.get_ylim()[1]*0.85, lbl, rotation=90, fontsize=8, color='green')
    ax.set_title('Monetary (triệu VND) — Histogram', fontweight='bold')
    ax.set_xlabel('Monetary (triệu VND)')
    ax.set_ylabel('Số đại lý')
    ax.legend(fontsize=9)
    
    ax = axes[2, 1]
    ax.boxplot(monetary_arr / 1e6, vert=False, widths=0.7,
               boxprops=dict(color='#C44E52'), medianprops=dict(color='blue', linewidth=2))
    ax.set_title('Monetary (triệu VND) — Boxplot', fontweight='bold')
    ax.set_xlabel('Triệu VND')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    chart_path = os.path.join(OUTPUT_DIR, 'rfm_distributions.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"  ✅ Đã lưu: {chart_path}")
    plt.close()
    
    # --- Chart 2: NTILE vs Manual comparison ---
    fig2, axes2 = plt.subplots(1, 3, figsize=(16, 5))
    fig2.suptitle('So sánh Phân bố Điểm: NTILE(5) vs Manual Thresholds', fontsize=14, fontweight='bold')
    
    labels = ['R Score', 'F Score', 'M Score']
    ntile_scores_list = [ntile_r, ntile_f, ntile_m]
    manual_scores_list = [manual_r, manual_f, manual_m]
    colors_pair = [('#4C72B0', '#A8C8E8'), ('#55A868', '#A8D8A8'), ('#C44E52', '#E8A8A8')]
    
    for ax, label, nt_s, mn_s, (c1, c2) in zip(axes2, labels, ntile_scores_list, manual_scores_list, colors_pair):
        x = np.arange(1, 6)
        width = 0.35
        nt_counts = [np.sum(nt_s == s) for s in range(1, 6)]
        mn_counts = [np.sum(mn_s == s) for s in range(1, 6)]
        ax.bar(x - width/2, nt_counts, width, label='NTILE(5)', color=c1, edgecolor='white')
        ax.bar(x + width/2, mn_counts, width, label='Manual', color=c2, edgecolor='white')
        ax.set_title(label, fontweight='bold')
        ax.set_xlabel('Điểm')
        ax.set_ylabel('Số đại lý')
        ax.set_xticks(x)
        ax.legend(fontsize=9)
        
        # Annotate counts
        for i, (nc, mc) in enumerate(zip(nt_counts, mn_counts)):
            ax.text(x[i] - width/2, nc + 5, str(nc), ha='center', fontsize=8, color=c1)
            ax.text(x[i] + width/2, mc + 5, str(mc), ha='center', fontsize=8, color=c2)
    
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    chart2_path = os.path.join(OUTPUT_DIR, 'ntile_vs_manual.png')
    plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
    print(f"  ✅ Đã lưu: {chart2_path}")
    plt.close()

# ============================================================
# TỔNG KẾT
# ============================================================
print(f"\n{'=' * 70}")
print(f"  ✅ EDA HOÀN TẤT")
print(f"{'=' * 70}")
print(f"""
  📁 Output: {OUTPUT_DIR}
  📊 Tổng đại lý: {n}
  
  Key Observations (kiểm tra ở trên):
  ├── Recency: Xem có GAP rõ giữa 2025 và 2026 không?
  ├── Frequency: Bao nhiêu % đại lý chỉ mua 1 lần?
  ├── Monetary: Skewness bao nhiêu? Top 10% chiếm bao nhiêu %?
  ├── Tier × RFM: VIP/KEY có thực sự R↑F↑M↑ không?
  └── NTILE vs Manual: Bao nhiêu đại lý bị gán điểm KHÁC nhau?
  
  → Dùng kết quả này để quyết định scoring method cho v_rfm_analysis.
""")

# Cleanup
cur.close()
conn.close()
