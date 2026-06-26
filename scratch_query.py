import psycopg2
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

conn = psycopg2.connect(host='localhost', port=5432, dbname='tnbike_db', user='postgres', password='442005')
query = "SELECT customer_code, province_name, r_score, f_score, m_score FROM tnbike.v_rfm_analysis WHERE rfm_segment ILIKE '%Champion%'"
df = pd.read_sql(query, conn)

artifact_path = r'C:\Users\DELL\.gemini\antigravity-ide\brain\c792732d-1885-4103-8e8c-de249ec64d44\champions_list.md'
with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write(f"# Danh sách {len(df)} Đại lý Champion\n\n")
    f.write(df.to_markdown(index=False))
