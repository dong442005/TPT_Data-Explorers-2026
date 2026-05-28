"""
EDA Tổng Quan — Phân tích Dữ liệu Bán Hàng TNBike
=========================================================
Mục đích: Cung cấp góc nhìn tổng quan (Exploratory Data Analysis) về doanh thu, 
          sản phẩm, và phân bổ địa lý trước khi đưa vào Power BI hoặc Machine Learning.
Đầu ra: Hiển thị các chỉ số thống kê trên Console và xuất biểu đồ ra thư mục plots/
"""

import os
import sys
import io
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Đảm bảo in Tiếng Việt không bị lỗi font trên Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Cấu hình Matplotlib ---
try:
    import matplotlib
    matplotlib.use('Agg')  # Chạy ngầm không cần hiện giao diện UI
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("⚠️ Thiếu thư viện matplotlib. Đang chạy ở chế độ chỉ xuất text.")
    print("💡 Gợi ý: Chạy lệnh `pip install matplotlib` để vẽ biểu đồ.")

# ============================================================
# 1. KẾT NỐI DATABASE VÀ TẢI DỮ LIỆU
# ============================================================
load_dotenv()
DB_CONFIG = dict(
    dbname=os.getenv('DB_NAME', 'tnbike_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("🚀 ĐANG KHỞI CHẠY QUÁ TRÌNH EDA TỔNG QUAN...")
print("=" * 60)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
    SELECT 
        order_date, so_number, customer_code, province_name, region,
        line_name, group_name, base_color, quantity, line_total
    FROM tnbike.fact_sales
    """
    df = pd.read_sql(query, conn)
    conn.close()
    print(f"✅ Đã tải thành công {len(df):,} dòng dữ liệu từ Database.")
except Exception as e:
    print(f"❌ Lỗi kết nối CSDL: {e}")
    sys.exit(1)

# ============================================================
# 2. KIỂM TRA CHẤT LƯỢNG DỮ LIỆU (DATA QUALITY)
# ============================================================
print("\n🔍 1. KIỂM TRA CHẤT LƯỢNG DỮ LIỆU (MISSING VALUES):")
missing_data = df.isnull().sum()
missing_data = missing_data[missing_data > 0]
if missing_data.empty:
    print("  -> Tuyệt vời! Không có giá trị NULL nào trong các trường quan trọng.")
else:
    print(missing_data.to_string())

# ============================================================
# 3. THỐNG KÊ KINH DOANH (BUSINESS METRICS)
# ============================================================
total_revenue = df['line_total'].sum()
total_orders = df['so_number'].nunique()
total_customers = df['customer_code'].nunique()
total_quantity = df['quantity'].sum()

print("\n📈 2. CHỈ SỐ KINH DOANH TỔNG QUAN:")
print(f"  - Tổng Doanh Thu:      {total_revenue:,.0f} VNĐ")
print(f"  - Tổng Sản Lượng:      {total_quantity:,.0f} chiếc")
print(f"  - Tổng Số Đơn Hàng:    {total_orders:,} đơn")
print(f"  - Tổng Số Đại Lý:      {total_customers:,} đại lý")
print(f"  - Giá trị Đơn TB (AOV): {total_revenue/total_orders:,.0f} VNĐ/đơn")

# ============================================================
# 4. PHÂN TÍCH THEO SẢN PHẨM & MÀU SẮC
# ============================================================
print("\n🚴 3. TOP 5 DÒNG XE BÁN CHẠY NHẤT (Theo Doanh Thu):")
top_lines = df.groupby('line_name')['line_total'].sum().sort_values(ascending=False).head(5)
for name, rev in top_lines.items():
    print(f"  - {name:<25}: {rev:,.0f} VNĐ ({rev/total_revenue*100:.1f}%)")

print("\n🎨 4. THỊ HIẾU MÀU SẮC (Top 5):")
top_colors = df.groupby('base_color')['quantity'].sum().sort_values(ascending=False).head(5)
for color, qty in top_colors.items():
    print(f"  - {color:<15}: {qty:,.0f} chiếc")

# ============================================================
# 5. PHÂN TÍCH ĐỊA LÝ
# ============================================================
print("\n🗺️ 5. PHÂN BỔ DOANH THU THEO VÙNG MIỀN:")
region_rev = df.groupby('region')['line_total'].sum().sort_values(ascending=False)
for region, rev in region_rev.items():
    print(f"  - {region:<15}: {rev:,.0f} VNĐ ({rev/total_revenue*100:.1f}%)")

# ============================================================
# 6. XUẤT BIỂU ĐỒ (VISUALIZATIONS)
# ============================================================
if HAS_PLOT:
    print("\n📊 Đang tạo biểu đồ phân tích...")
    
    # Thiết lập kích thước
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('EDA Tổng Quan — Thống Nhất Bike', fontsize=16, fontweight='bold')
    
    # 1. Biểu đồ Doanh thu theo tháng
    df['order_date'] = pd.to_datetime(df['order_date'])
    monthly_rev = df.groupby(df['order_date'].dt.to_period('M'))['line_total'].sum()
    monthly_rev.index = monthly_rev.index.astype(str)
    
    axes[0, 0].plot(monthly_rev.index, monthly_rev.values / 1e9, marker='o', color='#1f77b4', linewidth=2)
    axes[0, 0].set_title('Xu hướng Doanh thu theo tháng (Tỷ VNĐ)')
    axes[0, 0].set_ylabel('Tỷ VNĐ')
    axes[0, 0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 2. Top 10 Dòng xe
    top_10_lines = df.groupby('line_name')['line_total'].sum().sort_values().tail(10)
    axes[0, 1].barh(top_10_lines.index, top_10_lines.values / 1e9, color='#ff7f0e')
    axes[0, 1].set_title('Top 10 Dòng xe mang lại Doanh thu lớn nhất (Tỷ VNĐ)')
    
    # 3. Phân bổ Vùng miền
    axes[1, 0].pie(region_rev, labels=region_rev.index, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    axes[1, 0].set_title('Tỷ trọng Doanh thu theo Vùng miền')
    
    # 4. Phân bổ Màu sắc
    top_7_colors = df.groupby('base_color')['quantity'].sum().sort_values().tail(7)
    axes[1, 1].bar(top_7_colors.index, top_7_colors.values, color='#2ca02c')
    axes[1, 1].set_title('Top 7 Màu sắc được ưa chuộng nhất (Sản lượng)')
    axes[1, 1].set_ylabel('Số lượng (Chiếc)')
    plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_path = os.path.join(OUTPUT_DIR, 'eda_general_dashboard.png')
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"✅ Đã xuất biểu đồ tổng hợp tại: {plot_path}")

print("\n🎉 EDA TỔNG QUAN HOÀN TẤT!")
print("=" * 60)
