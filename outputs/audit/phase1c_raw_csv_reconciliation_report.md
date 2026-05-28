# Phase 1C: Raw CSV Reconciliation Report

## 1. Core Counts
- `fact_sales.csv`: 25754 rows ✅ PASS
- `order_line.csv`: 25754 rows ✅ PASS
- `sales_order.csv`: 2759 rows ✅ PASS
- `email_log.csv`: 1132 rows ✅ PASS
- `customer.csv`: 798 rows ✅ PASS
- `product.csv`: 265 rows ✅ PASS
- `product_line.csv`: 77 rows ✅ PASS
- `product_group.csv`: 5 rows ✅ PASS

## 2. Global Aggregation Checks
- sales_order amount: 109,445,161,439 vs order_line amount: 109,445,161,439 ✅
- sales_order quantity: 72,146 vs order_line qty: 72,146 ✅
- fact_sales amount: 109,445,161,439 vs order_line amount: 109,445,161,439 ✅
- fact_sales quantity: 72,146 vs order_line qty: 72,146 ✅

## 3. Product Hierarchy Audit
- Số SKU trong `product.csv` bị NULL `line_id`: **55**
- Số dòng fact_sales bị NULL `line_id_fk`: 3371
- Số dòng fact_sales bị NULL/UNMAPPED `group_code`: 3371

### Giải thích sai lệch (90 vs 55):
- Số SKU có trong fact_sales nhưng KHÔNG có trong product master: 0
- Số SKU trong product master có line_id nhưng JOIN THẤT BẠI sang product_line: 0
- **Kết luận:** 55 SKU thực sự NULL line_id từ source. Con số 90 trước đây có thể do đếm cả các SKU bị join fail hoặc các bản ghi tạp từ DB view cũ. **Source of Truth là 55 SKU NULL line_id trong product.csv**.

### UNKNOWN Hierarchy Impact:
- Transactions (rows): 3371 (13.09%)
- Quantity: 7,668 (10.63%)
- Revenue: 14,119,196,840 (12.90%)
- % of March Quantity: 14.70%
- Phân bố theo tháng: (Xem file `outputs/audit/unknown_hierarchy_impact_summary.csv`)

## 4. Customer Tier Decision
- Xác nhận `customer_tier` chỉ có 1 giá trị duy nhất (STANDARD). Không dùng làm feature chính, sẽ bị drop trong quá trình RFM feature engineering do zero variance.

## 5. Province Clean Integration
- Tỷ lệ fact_sales.province_id khớp với province_clean.province_id: 99.55%

## 6. Price Table Review
- Nhận định: `product_price.csv` dường như chứa giá theo từng invoice/order chứ không phải bảng giá list price chuẩn. Chúng ta sẽ dùng `implied_price = revenue / quantity` và `median_unit_price` trong quá trình aggregation.