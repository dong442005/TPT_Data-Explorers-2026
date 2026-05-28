import psycopg2
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME', 'tnbike_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)
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
