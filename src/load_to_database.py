import json
import re
import psycopg2
from datetime import datetime
from email.utils import parsedate_to_datetime

DB_CONFIG = {
    "dbname": "tnbike_db",
    "user": "postgres",
    "password": "Gamegunny321",
    "host": "localhost",
    "port": "5432",
}

INPUT_JSON = "processed_data.json"


def normalize_so_number(value):
    return str(value).replace("_", ".")


def parse_ddmmyyyy(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except Exception:
        return None


def parse_email_datetime(value):
    if not value or value == "Unknown":
        return None
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def get_order_date(order):
    d = parse_ddmmyyyy(order.get("order_date"))
    if d:
        return d

    meta = order.get("meta", {})

    d = parse_ddmmyyyy(meta.get("order_date_email"))
    if d:
        return d

    subject = meta.get("subject", "")
    m = re.search(r"(\d{2}/\d{2}/\d{4})", subject)
    if m:
        d = parse_ddmmyyyy(m.group(1))
        if d:
            return d

    received = parse_email_datetime(meta.get("received_at"))
    if received:
        return received.date()

    return None


def create_email_log_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tnbike.email_log (
            log_id BIGSERIAL PRIMARY KEY,
            message_id TEXT,
            from_address TEXT,
            received_at TIMESTAMPTZ,
            attachment_name TEXT,
            processing_status VARCHAR(50)
        );
    """)


def get_or_create_customer(cur, tax_code, customer_name, address):
    tax_code = str(tax_code or "").strip()

    cur.execute("""
        SELECT customer_code
        FROM tnbike.customer
        WHERE TRIM(tax_code) = %s
        LIMIT 1;
    """, (tax_code,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        SELECT COALESCE(MAX(CAST(SUBSTRING(customer_code FROM 4) AS INTEGER)), 0) + 1
        FROM tnbike.customer
        WHERE customer_code LIKE 'KH-%';
    """)
    next_num = cur.fetchone()[0]
    customer_code = f"KH-{next_num:05d}"

    cur.execute("""
        INSERT INTO tnbike.customer (
            customer_code, customer_name, tax_code, address
        )
        VALUES (%s, %s, %s, %s);
    """, (
        customer_code,
        customer_name or f"Khách hàng {tax_code}",
        tax_code,
        address
    ))

    return customer_code


def ensure_product(cur, line):
    product_code = line["product_code"]

    cur.execute("""
        SELECT 1
        FROM tnbike.product
        WHERE product_code = %s
        LIMIT 1;
    """, (product_code,))
    if cur.fetchone():
        return

    cur.execute("""
        INSERT INTO tnbike.product (
            product_code, product_name, unit
        )
        VALUES (%s, %s, %s);
    """, (
        product_code,
        line.get("product_name") or product_code,
        line.get("unit") or "Chiếc"
    ))


def refresh_fact_sales(cur):
    cur.execute("""
        DELETE FROM tnbike.fact_sales
        WHERE order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31';
    """)

    cur.execute("""
        INSERT INTO tnbike.fact_sales (
            order_date, fiscal_year, fiscal_quarter, fiscal_month, week_of_year,
            so_number, order_id, line_id,
            customer_code, customer_name, province_id, province_name, region,
            product_code, product_name, color, line_id_fk, line_name, group_code, group_name,
            quantity, unit_price, line_total
        )
        SELECT
            so.order_date,
            EXTRACT(YEAR FROM so.order_date)::SMALLINT,
            EXTRACT(QUARTER FROM so.order_date)::SMALLINT,
            EXTRACT(MONTH FROM so.order_date)::SMALLINT,
            EXTRACT(WEEK FROM so.order_date)::SMALLINT,
            ol.so_number,
            so.order_id,
            ol.line_id,
            c.customer_code,
            c.customer_name,
            c.province_id,
            pr.province_name,
            pr.region,
            p.product_code,
            p.product_name,
            p.color,
            p.line_id AS line_id_fk,
            pl.line_name,
            pg.group_code,
            pg.group_name,
            ol.quantity,
            ol.unit_price,
            ol.line_total
        FROM tnbike.order_line ol
        JOIN tnbike.sales_order so ON so.order_id = ol.order_id
        JOIN tnbike.customer c ON c.customer_code = so.customer_code
        JOIN tnbike.product p ON p.product_code = ol.product_code
        LEFT JOIN tnbike.product_line pl ON pl.line_id = p.line_id
        LEFT JOIN tnbike.product_group pg ON pg.group_code = pl.group_code
        LEFT JOIN tnbike.province pr ON pr.province_id = c.province_id
        WHERE so.order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31';
    """)


def main():
    print("BẮT ĐẦU NẠP DỮ LIỆU VÀO DATABASE...")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    orders = data["ready_orders"]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    inserted_count = 0

    try:
        cur.execute("SET search_path TO tnbike, public;")
        create_email_log_table(cur)

        print("Đang xóa dữ liệu tháng 3 cũ nếu có...")

        cur.execute("""
            DELETE FROM tnbike.fact_sales
            WHERE order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31';
        """)

        cur.execute("""
            DELETE FROM tnbike.order_line
            WHERE order_id IN (
                SELECT order_id
                FROM tnbike.sales_order
                WHERE order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
            );
        """)

        cur.execute("""
            DELETE FROM tnbike.sales_order
            WHERE order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31';
        """)

        cur.execute("DELETE FROM tnbike.email_log;")

        print("Đang ghi email_log...")

        for log in data["logs"]:
            cur.execute("""
                INSERT INTO tnbike.email_log (
                    message_id,
                    from_address,
                    received_at,
                    attachment_name,
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (
                log.get("message_id"),
                log.get("from_address"),
                parse_email_datetime(log.get("received_at")),
                log.get("attachment_name"),
                log.get("status"),
            ))

        print("Đang nạp sales_order và order_line...")

        for order in orders:
            so_number = normalize_so_number(order["so_number"])
            order_date = get_order_date(order)

            if not order_date:
                raise ValueError(f"Không xác định được order_date cho {so_number}")

            tax_code = str(order.get("tax_code", "")).strip()
            customer_name = order.get("customer_name")
            address = order.get("address")
            lines = order["lines"]

            customer_code = get_or_create_customer(
                cur,
                tax_code,
                customer_name,
                address
            )

            for line in lines:
                ensure_product(cur, line)

            total_quantity = sum(int(float(line["quantity"])) for line in lines)
            total_amount = sum(int(float(line["line_total"])) for line in lines)

            cur.execute("""
                INSERT INTO tnbike.sales_order (
                    so_number,
                    invoice_symbol,
                    invoice_number,
                    order_date,
                    customer_code,
                    total_amount,
                    total_quantity
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING order_id;
            """, (
                so_number,
                "C26TTN",
                so_number,
                order_date,
                customer_code,
                total_amount,
                total_quantity,
            ))

            order_id = cur.fetchone()[0]

            for line in lines:
                cur.execute("""
                    INSERT INTO tnbike.order_line (
                        order_id,
                        so_number,
                        product_code,
                        quantity,
                        unit_price,
                        line_total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    order_id,
                    so_number,
                    line["product_code"],
                    line["quantity"],
                    line["unit_price"],
                    line["line_total"],
                ))

            inserted_count += 1

        print("Đang cập nhật fact_sales...")
        refresh_fact_sales(cur)

        conn.commit()

        print("HOÀN TẤT")
        print(f"Tổng đơn trong JSON: {len(orders)}")
        print(f"Đã insert: {inserted_count}")
        print("fact_sales đã được cập nhật.")

    except Exception as e:
        conn.rollback()
        print(f"Lỗi hệ thống: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()