"""
normalize_color.py
==================
Chuẩn hóa cột `color` trong bảng product và đồng bộ sang fact_sales.

Vấn đề: fact_sales.color là cột denormalized (sao chép từ product.color tại thời điểm insert).
Khi product.color có chữ hoa/thường không nhất quán ("đen" / "Đen" / "ĐEN"),
fact_sales giữ nguyên giá trị cũ → heatmap màu sắc trong Power BI bị duplicate.

Giải pháp:
  Bước 1 — UPDATE product: INITCAP(LOWER(color)) → "đen","ĐEN","Đen" → tất cả thành "Đen"
  Bước 2 — UPDATE fact_sales: sync color từ product theo product_code

Chạy: python normalize_color.py
"""

import psycopg2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = dict(
    dbname='tnbike_db',
    user='postgres',
    password='442005',
    host='localhost',
    port='5432',
)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('SET search_path TO tnbike, public;')

try:
    # ----------------------------------------------------------------
    # BƯỚC 0: Xem tình trạng trước khi normalize
    # ----------------------------------------------------------------
    print("=" * 60)
    print("  NORMALIZE COLOR — TNBike fact_sales")
    print("=" * 60)

    cur.execute("""
        SELECT color, COUNT(*) AS so_dong
        FROM tnbike.fact_sales
        GROUP BY color
        ORDER BY so_dong DESC
        LIMIT 20;
    """)
    rows_before = cur.fetchall()

    # Kiểm tra có bị duplicate màu không
    colors_before = [r[0] for r in rows_before if r[0]]
    colors_lower = [c.lower() for c in colors_before]
    duplicates = set(c for c in colors_lower if colors_lower.count(c) > 1)

    print(f"\n  📊 TRƯỚC khi normalize — Top màu trong fact_sales:")
    print(f"  {'Màu':<20} {'Số dòng':>10}")
    print(f"  {'─'*20} {'─'*10}")
    for color, count in rows_before:
        flag = " ⚠️ DUPLICATE" if color and color.lower() in duplicates else ""
        print(f"  {str(color):<20} {count:>10,}{flag}")

    if not duplicates:
        print("\n  ✅ Không phát hiện duplicate màu — có thể đã normalize rồi.")
        print("     Script vẫn chạy để đảm bảo đồng nhất.")
    else:
        print(f"\n  ⚠️  Phát hiện {len(duplicates)} màu bị duplicate: {duplicates}")

    # ----------------------------------------------------------------
    # BƯỚC 1: Normalize color trong bảng product
    # ----------------------------------------------------------------
    print("\n  🔧 Bước 1: Normalize color trong bảng product...")
    cur.execute("""
        UPDATE tnbike.product
        SET color = INITCAP(LOWER(color))
        WHERE color IS NOT NULL;
    """)
    rows_updated_product = cur.rowcount
    print(f"  ✅ Đã cập nhật {rows_updated_product} dòng trong bảng product.")

    # ----------------------------------------------------------------
    # BƯỚC 2: Sync color từ product → fact_sales
    # ----------------------------------------------------------------
    print("\n  🔧 Bước 2: Sync color từ product → fact_sales...")
    cur.execute("""
        UPDATE tnbike.fact_sales AS fs
        SET color = p.color
        FROM tnbike.product AS p
        WHERE fs.product_code = p.product_code;
    """)
    rows_updated_facts = cur.rowcount
    print(f"  ✅ Đã cập nhật {rows_updated_facts:,} dòng trong bảng fact_sales.")

    conn.commit()

    # ----------------------------------------------------------------
    # KIỂM TRA KẾT QUẢ SAU KHI NORMALIZE
    # ----------------------------------------------------------------
    cur.execute("""
        SELECT color, COUNT(*) AS so_dong
        FROM tnbike.fact_sales
        GROUP BY color
        ORDER BY so_dong DESC
        LIMIT 20;
    """)
    rows_after = cur.fetchall()

    colors_after = [r[0] for r in rows_after if r[0]]
    colors_after_lower = [c.lower() for c in colors_after]
    still_duplicates = set(c for c in colors_after_lower if colors_after_lower.count(c) > 1)

    print(f"\n  📊 SAU khi normalize — Top màu trong fact_sales:")
    print(f"  {'Màu':<20} {'Số dòng':>10}")
    print(f"  {'─'*20} {'─'*10}")
    for color, count in rows_after:
        print(f"  {str(color):<20} {count:>10,}")

    print("\n" + "=" * 60)
    if not still_duplicates:
        print("  ✅ HOÀN TẤT — Không còn duplicate màu.")
        print("  → fact_sales.color đã đồng nhất, sẵn sàng import Power BI.")
    else:
        print(f"  ⚠️  VẪN CÒN duplicate: {still_duplicates}")
        print("  → Kiểm tra lại bảng product xem có mã hàng chưa map không.")
    print("=" * 60)

except Exception as e:
    conn.rollback()
    print(f"\n❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()

finally:
    cur.close()
    conn.close()
