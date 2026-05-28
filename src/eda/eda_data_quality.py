"""
EDA Chất Lượng Dữ Liệu (Data Quality Assessment) — TNBike
=========================================================
Mục đích: Khám phá và thống kê các lỗi dữ liệu trước khi chúng được sửa bằng SQL Patches.
"""

import os
import sys
import io
import json
import pandas as pd
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "processed_data.json"
CLEAN_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "processed_data_clean.json"
OUTPUT_DIR = PROJECT_ROOT / "src" / "eda" / "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("🔍 EDA CHẤT LƯỢNG DỮ LIỆU (PRE-SQL PATCHES)")
print("=" * 70)

if not RAW_JSON_PATH.exists() or not CLEAN_JSON_PATH.exists():
    print("❌ Thiếu file JSON. Vui lòng chạy `extract_validate.py` và `normalize.py` trước.")
    sys.exit(1)

# Đọc RAW JSON (để xem lỗi OCR Font)
with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

raw_lines = []
for order in raw_data.get('ready_orders', []):
    for line in order.get('lines', []):
        raw_lines.append(line.get('product_name', ''))
df_raw = pd.DataFrame({'product_name': raw_lines})

# Đọc CLEAN JSON (để xem lỗi thiếu Line_ID sau Normalization)
with open(CLEAN_JSON_PATH, "r", encoding="utf-8") as f:
    clean_data = json.load(f)

clean_lines = []
customers = []
for order in clean_data.get('ready_orders', []):
    customers.append({'address': order.get('address')})
    for line in order.get('lines', []):
        clean_lines.append({
            'product_name': line.get('product_name_clean'),
            'color': line.get('color_clean'),
            'line_id': line.get('line_id_clean'),
            'quantity': float(line.get('quantity', 0))
        })
df_clean = pd.DataFrame(clean_lines)
df_cust = pd.DataFrame(customers)

print(f"✅ Đã tải thành công {len(df_raw)} dòng sản phẩm thô.")

# ============================================================
# VẤN ĐỀ 1: NHIỄU CẤU TRÚC FONT CHỮ
# ============================================================
print("\n🚨 VẤN ĐỀ 1: LỖI FONT CHỮ TRONG TÊN SẢN PHẨM (Raw PDF Data)")
noise_keywords = ['xennpthnngnhnt', 'xenngthnngnhnt', 'thnngnhnt', 'nnp']
noise_counts = df_raw['product_name'].apply(lambda x: any(k in str(x).lower() for k in noise_keywords)).sum()
print(f"  -> Phát hiện {noise_counts} dòng sản phẩm (chiếm {noise_counts/len(df_raw)*100:.1f}%) bị lỗi biến dạng font chữ (VD: 'xennpthnngnhnt').")

# ============================================================
# VẤN ĐỀ 2: THIẾU LINE_ID SAU BƯỚC NORMALIZE
# ============================================================
print("\n🚨 VẤN ĐỀ 2: ĐIỂM MÙ PHÂN LOẠI SẢN PHẨM (Missing Line_ID)")
missing_line_id_count = df_clean['line_id'].isnull().sum()
total_qty_missing = df_clean[df_clean['line_id'].isnull()]['quantity'].sum()
total_qty = df_clean['quantity'].sum()

print(f"  -> {missing_line_id_count} dòng sản phẩm KHÔNG CÓ mã danh mục sau khi Normalize Python.")
print(f"  -> Tổng sản lượng bị mất liên kết: {total_qty_missing:,.0f} chiếc (chiếm {total_qty_missing/total_qty*100:.1f}% tổng sản lượng).")
print("  -> Bắt buộc phải dùng SQL Patch (Geo_Clean) để fix dứt điểm.")

# ============================================================
# VẤN ĐỀ 3: RÁC DỮ LIỆU MÀU SẮC
# ============================================================
print("\n🚨 VẤN ĐỀ 3: RÁC DỮ LIỆU MÀU SẮC")
unique_colors = df_clean['color'].dropna().unique()
dirty_colors = [c for c in unique_colors if 'Chưa xác định' in str(c) or len(str(c)) > 15]
print(f"  -> Phát hiện nhiều màu sắc bị dính liền tên nhân vật hoặc bị gán 'Chưa xác định'.")
print(f"  -> (Ví dụ: {', '.join(dirty_colors[:4])}...)")

# ============================================================
# VẤN ĐỀ 4: LỖI DỮ LIỆU ĐỊA LÝ
# ============================================================
print("\n🚨 VẤN ĐỀ 4: THIẾU DỮ LIỆU TỈNH THÀNH (Province)")
print("  -> Dữ liệu khách hàng thô chỉ có chuỗi Địa chỉ dài, không có trường Tỉnh thành riêng biệt (Province_ID = NULL).")
print(f"  [VD]: {df_cust['address'].dropna().iloc[0]}")

# ============================================================
# XUẤT BIỂU ĐỒ
# ============================================================
if HAS_PLOT:
    print("\n📊 Đang vẽ biểu đồ Data Quality (Lưu tại: src/eda/plots/data_quality_issues.png)...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Đánh Giá Lỗi Dữ Liệu Trước SQL Patches', fontsize=15, fontweight='bold')
    
    # 1. Tỷ lệ Missing Line ID
    labels_pie = ['Có Line_ID (Chuẩn)', 'Thiếu Line_ID (Mồ côi)']
    sizes_pie = [total_qty - total_qty_missing, total_qty_missing]
    axes[0].pie(sizes_pie, labels=labels_pie, autopct='%1.1f%%', startangle=90, colors=['#2ca02c', '#d62728'])
    axes[0].set_title('Tỷ lệ thất thoát dữ liệu do thiếu Danh mục', fontweight='bold')
    
    # 2. Top 10 Màu sắc "Rác" xuất hiện nhiều nhất
    # Plotting top colors regardless, to show fragmentation
    color_counts = df_clean['color'].value_counts().head(10)
    sns.barplot(x=color_counts.values, y=color_counts.index, ax=axes[1], palette='Reds_r')
    axes[1].set_title('Phân mảnh dữ liệu Màu Sắc (Top 10)', fontweight='bold')
    axes[1].set_xlabel('Số lượng dòng (Lines)')
    
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, 'data_quality_issues.png')
    plt.savefig(plot_path, dpi=150)
    plt.close()

print("\n🎉 EDA CHẤT LƯỢNG DỮ LIỆU HOÀN TẤT!")
print("=" * 70)
