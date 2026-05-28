import os
import re
import json
import psycopg2
import pandas as pd
from pathlib import Path

# Thư mục gốc của project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cấu hình đường dẫn
INPUT_JSON = PROJECT_ROOT / "data" / "processed" / "processed_data.json"
OUTPUT_JSON = PROJECT_ROOT / "data" / "processed" / "processed_data_clean.json"

from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "tnbike_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

# ---- 1. Đọc file JSON ----
if not INPUT_JSON.exists():
    print(f"Lỗi: Không tìm thấy file JSON đầu vào tại {INPUT_JSON}")
    print("Vui lòng chạy 'python src/extract_validate.py' trước để trích xuất dữ liệu.")
    exit(1)

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

orders = data.get('ready_orders', [])

# ---- 2. Flatten tất cả lines ----
lines_list = []
for order in orders:
    so_number = order.get("so_number")
    order_date = order.get("order_date")
    tax_code = order.get("tax_code")
    customer_name = order.get("customer_name")
    address = order.get("address")
    meta = order.get("meta")
    for line in order.get("lines", []):
        lines_list.append({
            "so_number": so_number,
            "order_date": order_date,
            "tax_code": tax_code,
            "customer_name": customer_name,
            "address": address,
            "meta": json.dumps(meta) if meta else None,
            "product_code": line.get("product_code"),
            "product_name": line.get("product_name"),
            "unit": line.get("unit"),
            "color": line.get("color"),
            "line_id": line.get("line_id"),
            "quantity": line.get("quantity"),
            "unit_price": line.get("unit_price"),
            "line_total": line.get("line_total")
        })

if not lines_list:
    print("Không có dòng đơn hàng nào sẵn sàng để xử lý.")
    exit(0)

df = pd.DataFrame(lines_list)

# ---- 3. Chuẩn hóa unit ----
df['unit_clean'] = 'Chiếc'

# ---- 4. Chuẩn hóa color ----
def normalize_color(name, raw_color):
    name_lower = str(name).lower() if name else ''
    if any(x in name_lower for x in ['xanh']):
        return 'Xanh'
    if any(x in name_lower for x in ['đen', 'den']):
        return 'Đen'
    if any(x in name_lower for x in ['đỏ', 'do']):
        return 'Đỏ'
    for color in ['Cam','Tím','Trắng','Rêu','Hồng','Ghi','Kem','Coban','Vàng','Nâu','Ngọc','Be']:
        if color and (color.lower() in name_lower):
            return color
    return raw_color if raw_color else 'Chưa xác định'

df['color_clean'] = df.apply(lambda r: normalize_color(r['product_name'], r.get('color')), axis=1)

# ---- 5. Tải động line_id từ PostgreSQL Database ----
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SET search_path TO tnbike, public;")
    cur.execute("SELECT line_id, line_name FROM tnbike.product_line;")
    product_lines = cur.fetchall()
    product_line_df = pd.DataFrame(product_lines, columns=["line_id", "line_name"])
    cur.close()
    conn.close()
    print(f"Đã kết nối DB và tải {len(product_line_df)} dòng sản phẩm thành công.")
except Exception as e:
    print(f"Cảnh báo kết nối Database thất bại: {e}")
    print("Không thể tải product_line từ DB. Tự động kiểm tra file csv local dự phòng...")
    
    # Dự phòng nếu DB chưa chạy (để chạy offline khi build thử)
    csv_fallback = Path("Data_Explorers_Vong_2/product_line.csv")
    if csv_fallback.exists():
        product_line_df = pd.read_csv(csv_fallback)
        print("Đã tải product_line thành công từ file CSV dự phòng.")
    else:
        print("Lỗi: Không tìm thấy danh mục product_line ở cả DB và CSV dự phòng.")
        exit(1)

def normalize_key(s):
    s = str(s).lower() if s else ''
    s = ''.join(c for c in s if c.isalnum())
    # Remove common noise words to handle PDF encoding errors
    for word in ['xennpthnngnhnt', 'xenngthnngnhnt', 'xedapthongnhat', 'xedap', 'xennp', 'thnngnhnt', 'thongnhat', 'xe', 'te']:
        s = s.replace(word, '')
    return s

product_line_df['line_key'] = product_line_df['line_name'].apply(normalize_key)
df['product_key'] = df['product_name'].apply(normalize_key)

line_map = {k: v for k, v in zip(product_line_df['line_key'], product_line_df['line_id'])}
def map_line_id(product_key):
    matches = [line_map[k] for k in line_map if k in product_key or product_key in k]
    return matches[0] if len(matches) == 1 else None

df['line_id_clean'] = df['product_key'].apply(map_line_id)

# ---- 6. Tạo product_name_clean từ line_name + color ----
def build_product_name(row):
    if pd.notnull(row['line_id_clean']):
        line_name = product_line_df.loc[product_line_df['line_id'] == row['line_id_clean'], 'line_name'].values[0]
        base_name = 'Xe đạp Thống Nhất ' + line_name.replace('(IP - Bản quyền','').strip()
        return f"{base_name} {row['color_clean']}".strip()
    else:
        return row['product_name']

df['product_name_clean'] = df.apply(build_product_name, axis=1)

# ---- 7. Xóa các trường raw ----
df = df.drop(columns=['product_name','unit','color','line_id','product_key'])

# ---- 8. Chuyển lại thành cấu trúc JSON ----
cleaned_orders = []
for so_number, group in df.groupby('so_number'):
    meta_val = group['meta'].iloc[0] if 'meta' in group else None
    meta_dict = json.loads(meta_val) if pd.notnull(meta_val) else {}
    
    order_info = {
        "so_number": so_number,
        "order_date": group['order_date'].iloc[0] if pd.notnull(group['order_date'].iloc[0]) else None,
        "tax_code": group['tax_code'].iloc[0] if pd.notnull(group['tax_code'].iloc[0]) else None,
        "customer_name": group['customer_name'].iloc[0] if pd.notnull(group['customer_name'].iloc[0]) else None,
        "address": group['address'].iloc[0] if ('address' in group and pd.notnull(group['address'].iloc[0])) else None,
        "meta": meta_dict,
        "lines": []
    }
    for _, row in group.iterrows():
        order_info["lines"].append({
            "product_code": row['product_code'],
            "product_name_clean": row['product_name_clean'],
            "unit_clean": row['unit_clean'],
            "color_clean": row['color_clean'],
            "line_id_clean": row['line_id_clean'] if pd.notnull(row['line_id_clean']) else None,
            "quantity": row['quantity'],
            "unit_price": row['unit_price'],
            "line_total": row['line_total']
        })
    cleaned_orders.append(order_info)

data['ready_orders'] = cleaned_orders

# ---- 9. Ghi lại JSON sạch ----
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Hoàn tất chuẩn hóa: {len(cleaned_orders)} đơn hàng đã được xử lý và ghi nhận tại {OUTPUT_JSON.name}.")
