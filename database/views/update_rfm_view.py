import psycopg2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg2.connect(dbname='tnbike_db', user='postgres', password='442005', host='localhost', port='5432')
cur = conn.cursor()
cur.execute('SET search_path TO tnbike, public;')

sql = """
DROP VIEW IF EXISTS tnbike.v_rfm_analysis CASCADE;

CREATE VIEW tnbike.v_rfm_analysis AS
WITH rfm_raw AS (
    SELECT
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        COALESCE(pr.province_name, 'Chưa xác định')::varchar(100) AS province_name,
        COALESCE(pr.region, 'Chưa xác định')::varchar(50) AS region,
        MAX(f.order_date) AS last_order_date,
        DATE '2026-03-31' - MAX(f.order_date) AS recency_days,
        COUNT(DISTINCT f.so_number) AS frequency,
        SUM(f.line_total) AS monetary
    FROM tnbike.fact_sales f
    JOIN tnbike.customer c ON c.customer_code = f.customer_code
    LEFT JOIN tnbike.province pr ON pr.province_id = c.province_id
    GROUP BY f.customer_code, c.customer_name, c.customer_tier, 
             pr.province_name, pr.region
),
rfm_scored AS (
    SELECT *,
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 60  THEN 4
            WHEN recency_days <= 90  THEN 3
            WHEN recency_days <= 180 THEN 2
            ELSE                          1
        END AS r_score,
        
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6  THEN 4
            WHEN frequency >= 3  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE                      1
        END AS f_score,
        
        CASE
            WHEN monetary >= 1000000000  THEN 5
            WHEN monetary >= 300000000   THEN 4
            WHEN monetary >= 100000000   THEN 3
            WHEN monetary >= 30000000    THEN 2
            ELSE                              1
        END AS m_score
    FROM rfm_raw
)
SELECT *,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 4 THEN 'Big Spender'
        WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 2 THEN 'Potential'
        WHEN r_score >= 4 AND f_score = 1 AND m_score <= 3 THEN 'New'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND (f_score >= 2 OR m_score >= 2) THEN 'Hibernating'
        ELSE 'Lost'
    END AS rfm_segment
FROM rfm_scored;
"""

try:
    cur.execute(sql)
    conn.commit()
    print("✅ Đã cập nhật thành công View tnbike.v_rfm_analysis")
    
    cur.execute("SELECT rfm_segment, COUNT(*) FROM tnbike.v_rfm_analysis GROUP BY rfm_segment ORDER BY COUNT(*) DESC;")
    print('\nPhân bố segment thực tế sau khi tạo View:')
    print('-'*50)
    total = 0
    for row in cur.fetchall():
        print(f"{row[0]:<15}: {row[1]:>5} đại lý")
        total += row[1]
    print('-'*50)
    print(f"{'Tổng cộng':<15}: {total:>5} đại lý")

except Exception as e:
    print(f"❌ Lỗi: {e}")
finally:
    cur.close()
    conn.close()
