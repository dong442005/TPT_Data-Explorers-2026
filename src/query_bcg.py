import psycopg2
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg2.connect(dbname='tnbike_db', user='postgres', password='442005', host='localhost', port='5432')
cur = conn.cursor()

query = """
SELECT line_name, rev_q1_2025, rev_q1_2026, growth_pct_yoy 
FROM tnbike.v_bcg_matrix 
ORDER BY growth_pct_yoy DESC NULLS LAST
LIMIT 10;
"""

cur.execute(query)
rows = cur.fetchall()

print("Top 10 dòng xe có tốc độ tăng trưởng cao nhất:")
print(f"{'Line Name':<25} | {'Q1 2025':<15} | {'Q1 2026':<15} | {'Growth YoY':<15}")
print("-" * 75)
for r in rows:
    print(f"{r[0]:<25} | {r[1]:<15} | {r[2]:<15} | {r[3]}")

cur.close()
conn.close()
