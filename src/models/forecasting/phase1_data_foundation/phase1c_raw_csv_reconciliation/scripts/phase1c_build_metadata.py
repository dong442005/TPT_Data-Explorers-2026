import pandas as pd
import numpy as np
import os

def build_metadata():
    if not os.path.exists('data/metadata'):
        os.makedirs('data/metadata')
        
    dtypes = {'product_code': str, 'line_id': str, 'group_code': str}
    
    product = pd.read_csv('data/raw/product.csv', dtype=dtypes)
    product_line = pd.read_csv('data/raw/product_line.csv', dtype=dtypes)
    product_group = pd.read_csv('data/raw/product_group.csv', dtype=dtypes)
    fact_sales = pd.read_csv('data/raw/fact_sales.csv', dtype={'product_code': str})
    
    # Identify cold start
    fact_sales['order_date'] = pd.to_datetime(fact_sales['order_date'])
    pre_march_skus = fact_sales[fact_sales['order_date'] < '2026-03-01']['product_code'].unique()
    march_skus = fact_sales[fact_sales['order_date'] >= '2026-03-01']['product_code'].unique()
    
    # Left join product to product_line
    pl = product_line[['line_id', 'line_name', 'group_code']]
    pg = product_group[['group_code', 'group_name']]
    
    meta = product[['product_code', 'product_name', 'color', 'base_color', 'line_id']].copy()
    meta = meta.rename(columns={'line_id': 'line_id_original'})
    
    # To find mapping source
    meta['mapping_source'] = 'dimension_join'
    meta.loc[meta['line_id_original'].isna(), 'mapping_source'] = 'original_null'
    
    # Do the merge
    joined = pd.merge(meta, pl, left_on='line_id_original', right_on='line_id', how='left')
    joined = pd.merge(joined, pg, on='group_code', how='left')
    
    # Identify join failures
    join_fail_mask = (joined['mapping_source'] == 'dimension_join') & (joined['line_name'].isna())
    joined.loc[join_fail_mask, 'mapping_source'] = 'join_failed'
    
    joined['line_name_original'] = joined['line_name']
    joined['group_code_original'] = joined['group_code']
    joined['group_name_original'] = joined['group_name']
    
    # Create clean columns
    success_mask = joined['mapping_source'] == 'dimension_join'
    
    # Must be actual pd.NA for clean line_id when not success, but pandas Series doesn't always play nice with pd.NA in object arrays unless dtype is specific
    # To strictly use pd.NA without it becoming 'NaN' string:
    joined['line_id_clean'] = joined['line_id_original'].where(success_mask, pd.NA)
    joined['line_name_clean'] = np.where(success_mask, joined['line_name_original'], 'UNKNOWN')
    joined['group_code_clean'] = np.where(success_mask, joined['group_code_original'], 'UNKNOWN')
    joined['group_name_clean'] = np.where(success_mask, joined['group_name_original'], 'UNKNOWN')
    
    joined['mapping_confidence'] = 'high'
    joined['needs_manual_review'] = False
    
    # cold start flag
    joined['is_cold_start_march_sku'] = joined['product_code'].isin(march_skus) & ~joined['product_code'].isin(pre_march_skus)
    
    # Select final columns
    final_cols = [
        'product_code', 'product_name', 'color', 'base_color',
        'line_id_original', 'line_name_original', 'group_code_original', 'group_name_original',
        'line_id_clean', 'line_name_clean', 'group_code_clean', 'group_name_clean',
        'mapping_source', 'mapping_confidence', 'needs_manual_review', 'is_cold_start_march_sku'
    ]
    
    final_meta = joined[final_cols]
    
    final_meta.to_csv('data/metadata/product_hierarchy_mapping.csv', index=False)
    final_meta.to_parquet('data/metadata/product_metadata.parquet', index=False)
    print("Clean metadata generated successfully. Rows:", len(final_meta))
    print(final_meta['mapping_source'].value_counts())

if __name__ == '__main__':
    build_metadata()
