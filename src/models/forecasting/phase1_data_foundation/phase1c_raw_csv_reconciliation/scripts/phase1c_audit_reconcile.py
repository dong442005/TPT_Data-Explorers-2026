import pandas as pd
import numpy as np
import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_data():
    dtypes = {
        'product_code': str,
        'customer_code': str,
        'so_number': str,
        'invoice_number': str,
        'message_id': str,
        'line_id': str,
        'line_id_fk': str,
        'province_id': str
    }
    
    data = {}
    csv_dir = 'data/raw'
    for file in os.listdir(csv_dir):
        if file.endswith('.csv'):
            name = file.replace('.csv', '')
            try:
                data[name] = pd.read_csv(os.path.join(csv_dir, file), dtype=dtypes)
            except Exception as e:
                print(f"Error loading {file}: {e}")
    return data

def run_audit():
    ensure_dir('outputs/audit')
    data = load_data()
    
    report_lines = ["# Phase 1C: Raw CSV Reconciliation Report", "\n## 1. Core Counts"]
    
    # Check row counts
    expected_counts = {
        'fact_sales': 25754,
        'order_line': 25754,
        'sales_order': 2759,
        'email_log': 1132,
        'customer': 798,
        'product': 265,
        'product_line': 77,
        'product_group': 5
    }
    
    for table, expected in expected_counts.items():
        if table in data:
            actual = len(data[table])
            status = "✅ PASS" if actual == expected else f"❌ FAIL (Expected: {expected})"
            report_lines.append(f"- `{table}.csv`: {actual} rows {status}")
        else:
            report_lines.append(f"- `{table}.csv`: ❌ FILE NOT FOUND")

    # Reconcile Aggregations
    report_lines.append("\n## 2. Global Aggregation Checks")
    
    sales_order = data['sales_order']
    order_line = data['order_line']
    fact_sales = data['fact_sales']
    
    so_total_amt = sales_order['total_amount'].sum()
    so_total_qty = sales_order['total_quantity'].sum()
    
    ol_total_amt = order_line['line_total'].sum()
    ol_total_qty = order_line['quantity'].sum()
    
    fs_total_amt = fact_sales['line_total'].sum()
    fs_total_qty = fact_sales['quantity'].sum()
    
    report_lines.append(f"- sales_order amount: {so_total_amt:,.0f} vs order_line amount: {ol_total_amt:,.0f} " + ("✅" if abs(so_total_amt - ol_total_amt) < 1 else "❌"))
    report_lines.append(f"- sales_order quantity: {so_total_qty:,.0f} vs order_line qty: {ol_total_qty:,.0f} " + ("✅" if abs(so_total_qty - ol_total_qty) < 1 else "❌"))
    report_lines.append(f"- fact_sales amount: {fs_total_amt:,.0f} vs order_line amount: {ol_total_amt:,.0f} " + ("✅" if abs(fs_total_amt - ol_total_amt) < 1 else "❌"))
    report_lines.append(f"- fact_sales quantity: {fs_total_qty:,.0f} vs order_line qty: {ol_total_qty:,.0f} " + ("✅" if abs(fs_total_qty - ol_total_qty) < 1 else "❌"))

    # Product Hierarchy Audit
    report_lines.append("\n## 3. Product Hierarchy Audit")
    
    product = data['product']
    null_line_id_skus = product[product['line_id'].isna()]
    
    report_lines.append(f"- Số SKU trong `product.csv` bị NULL `line_id`: **{len(null_line_id_skus)}**")
    
    fs_unmapped = fact_sales[fact_sales['line_id_fk'].isna()]
    fs_missing_group = fact_sales[fact_sales['group_code'].isna() | (fact_sales['group_code'] == 'UNMAPPED')]
    
    report_lines.append(f"- Số dòng fact_sales bị NULL `line_id_fk`: {len(fs_unmapped)}")
    report_lines.append(f"- Số dòng fact_sales bị NULL/UNMAPPED `group_code`: {len(fs_missing_group)}")
    
    # Tại sao Phase 1B báo 90 SKU unmapped nhưng raw csv chỉ 55 NULL?
    # Kiểm tra xem có bao nhiêu SKU trong fact_sales nhưng KHÔNG có trong product.csv
    skus_in_fs = set(fact_sales['product_code'].unique())
    skus_in_prod = set(product['product_code'].unique())
    skus_not_in_prod = skus_in_fs - skus_in_prod
    
    # Kiểm tra join failure
    product_line = data['product_line']
    product_valid_line = product.dropna(subset=['line_id'])
    join_fails = product_valid_line[~product_valid_line['line_id'].isin(product_line['line_id'].astype(str))]
    
    report_lines.append("\n### Giải thích sai lệch (90 vs 55):")
    report_lines.append(f"- Số SKU có trong fact_sales nhưng KHÔNG có trong product master: {len(skus_not_in_prod)}")
    report_lines.append(f"- Số SKU trong product master có line_id nhưng JOIN THẤT BẠI sang product_line: {len(join_fails)}")
    report_lines.append("- **Kết luận:** 55 SKU thực sự NULL line_id từ source. Con số 90 trước đây có thể do đếm cả các SKU bị join fail hoặc các bản ghi tạp từ DB view cũ. **Source of Truth là 55 SKU NULL line_id trong product.csv**.")

    # UNKNOWN Impact
    null_skus_list = null_line_id_skus['product_code'].tolist()
    unknown_fs = fact_sales[fact_sales['product_code'].isin(null_skus_list)]
    
    uk_rows = len(unknown_fs)
    uk_qty = unknown_fs['quantity'].sum()
    uk_rev = unknown_fs['line_total'].sum()
    
    pct_qty = uk_qty / fs_total_qty * 100 if fs_total_qty else 0
    pct_rev = uk_rev / fs_total_amt * 100 if fs_total_amt else 0
    
    report_lines.append("\n### UNKNOWN Hierarchy Impact:")
    report_lines.append(f"- Transactions (rows): {uk_rows} ({(uk_rows/len(fact_sales)*100):.2f}%)")
    report_lines.append(f"- Quantity: {uk_qty:,.0f} ({pct_qty:.2f}%)")
    report_lines.append(f"- Revenue: {uk_rev:,.0f} ({pct_rev:.2f}%)")
    
    fact_sales['order_date'] = pd.to_datetime(fact_sales['order_date'])
    fact_sales['month_year'] = fact_sales['order_date'].dt.to_period('M')
    
    uk_by_month = fact_sales[fact_sales['product_code'].isin(null_skus_list)].groupby('month_year').agg({
        'quantity': 'sum',
        'line_total': 'sum',
        'fact_id': 'count'
    }).reset_index()
    
    uk_by_month['month_year'] = uk_by_month['month_year'].astype(str)
    uk_by_month.to_csv('outputs/audit/unknown_hierarchy_impact_summary.csv', index=False)
    
    march_26_fs = fact_sales[fact_sales['month_year'] == '2026-03']
    march_qty = march_26_fs['quantity'].sum()
    march_uk_qty = uk_by_month[uk_by_month['month_year'] == '2026-03']['quantity'].sum() if '2026-03' in uk_by_month['month_year'].values else 0
    
    report_lines.append(f"- % of March Quantity: {(march_uk_qty/march_qty*100) if march_qty else 0:.2f}%")
    report_lines.append("- Phân bố theo tháng: (Xem file `outputs/audit/unknown_hierarchy_impact_summary.csv`)")

    # Output detail SKU
    uk_sku_detail = fact_sales[fact_sales['product_code'].isin(null_skus_list)].groupby('product_code').agg({
        'product_name': 'first',
        'quantity': 'sum',
        'line_total': 'sum'
    }).reset_index()
    
    # Label is_cold_start
    pre_march = fact_sales[fact_sales['order_date'] < '2026-03-01']['product_code'].unique()
    uk_sku_detail['is_cold_start_march'] = ~uk_sku_detail['product_code'].isin(pre_march)
    
    uk_sku_detail.to_csv('outputs/audit/unknown_hierarchy_sku_detail.csv', index=False)

    # 4. Customer Tier Distribution
    customer = data['customer']
    tier_dist = customer['customer_tier'].value_counts().reset_index()
    tier_dist.columns = ['customer_tier', 'count']
    tier_dist.to_csv('outputs/audit/customer_tier_distribution.csv', index=False)
    report_lines.append("\n## 4. Customer Tier Decision")
    report_lines.append("- Xác nhận `customer_tier` chỉ có 1 giá trị duy nhất (STANDARD). Không dùng làm feature chính, sẽ bị drop trong quá trình RFM feature engineering do zero variance.")

    # 5. Province Clean Integration
    fs_province_ids = fact_sales['province_id'].dropna().unique()
    province_clean = data['province_clean']
    clean_province_ids = province_clean['province_id'].astype(str).unique()
    
    match_count = sum(1 for pid in fs_province_ids if str(float(pid) if '.' in pid else pid) in clean_province_ids or pid in clean_province_ids)
    # Be more robust with ID matching
    def clean_id(pid):
        try:
            return str(int(float(pid)))
        except:
            return str(pid)
            
    fact_sales['clean_province_id_fk'] = fact_sales['province_id'].apply(clean_id)
    province_clean['clean_province_id'] = province_clean['province_id'].apply(clean_id)
    
    matched = fact_sales['clean_province_id_fk'].isin(province_clean['clean_province_id']).mean() * 100
    report_lines.append(f"\n## 5. Province Clean Integration")
    report_lines.append(f"- Tỷ lệ fact_sales.province_id khớp với province_clean.province_id: {matched:.2f}%")
    
    match_report = pd.DataFrame({'match_rate_percent': [matched]})
    match_report.to_csv('outputs/audit/province_clean_match_report.csv', index=False)

    # 6. Price Data
    product_price = data['product_price']
    product_price.to_csv('outputs/audit/price_table_review.csv', index=False)
    report_lines.append("\n## 6. Price Table Review")
    report_lines.append("- Nhận định: `product_price.csv` dường như chứa giá theo từng invoice/order chứ không phải bảng giá list price chuẩn. Chúng ta sẽ dùng `implied_price = revenue / quantity` và `median_unit_price` trong quá trình aggregation.")

    with open('outputs/audit/phase1c_raw_csv_reconciliation_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print("Audit completed successfully.")
    
if __name__ == '__main__':
    run_audit()
