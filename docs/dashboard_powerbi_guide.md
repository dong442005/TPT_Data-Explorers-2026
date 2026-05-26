# Hướng dẫn Dashboard PowerBI - Hạng mục B
## Data Explorers 2026 | Thống Nhất Bike

---

## 1. BỐI CẢNH ĐỀ BÀI VÀ PHẠM VI DỮ LIỆU

### 1.1. Bối cảnh cuộc thi

Data Explorers 2026 vòng 2 yêu cầu xây dựng hệ thống phân tích dữ liệu kinh doanh cho Công ty Cổ phần Xe đạp Thống Nhất.

Có 3 hạng mục liên quan trực tiếp đến dashboard:

1. Hạng mục A - Vận hành dữ liệu
   - Đọc 1,132 email `.eml` tháng 3/2026.
   - Tách PDF đính kèm.
   - Extract thông tin đơn hàng.
   - Validate dữ liệu.
   - Ghi vào PostgreSQL.
2. Hạng mục B - Phân tích
   - Xây dựng dashboard PowerBI.
   - Dashboard phải dùng trực tiếp dữ liệu T3/2026 do pipeline hạng mục A tạo ra.
   - Dashboard phân tích doanh thu, sản lượng, sản phẩm, đại lý và địa lý.
3. Hạng mục C - Dự báo
   - Dashboard và các view phải tạo nền dữ liệu đủ sạch cho forecasting Q2/2026.

### 1.2. Bản chất dữ liệu

Đây là bài toán phân phối xe đạp B2B, không phải retail:

- Doanh nghiệp bán sỉ cho đại lý.
- Đại lý mua theo lô, tần suất thưa, giá trị đơn lớn.
- Có thể có hành vi ôm hàng trước mùa cao điểm.
- Không có dữ liệu inventory, sell-through, COGS.

Vì vậy không được diễn giải dữ liệu như retail demand trực tiếp.

### 1.3. Phạm vi thời gian thực tế

> [!IMPORTANT]
> Dữ liệu thực tế chỉ có 6 tháng, không phải 14 tháng liên tục.

| Nguồn | Tháng |
|---|---|
| BTC cung cấp | T1, T2, T3/2025 |
| BTC cung cấp | T1, T2/2026 |
| Team extract từ email/PDF | T3/2026 |

Hệ quả:

- Không vẽ line chart như chuỗi 14 tháng liên tục.
- Không gọi T1/2026 so với T3/2025 là MoM đúng nghĩa.
- YoY chỉ có ý nghĩa cho T1, T2, T3.
- So sánh Q1/2025 với Q1/2026 là cặp hợp lệ nhất.

> [!WARNING]
> Không có dữ liệu T4 đến T12/2025. Mọi visual thời gian phải ghi chú rõ khoảng trống này.

---

## 2. TRẠNG THÁI DATABASE HIỆN TẠI SAU RESET VÀ PATCH

### 2.1. Pipeline và patch đã chạy

```text
01_create_tables.sql
-> 02_import_data.sql
-> extract_validate.py
-> normalize.py
-> load_to_database.py
-> geo_clean_patch_final.sql
-> db_data_quality_patch.sql
-> audit tổng thể
```

### 2.2. Các bảng giao dịch chính đã pass audit

| Bảng | Số dòng |
|---|---:|
| sales_order | 2,759 |
| order_line | 25,754 |
| fact_sales | 25,754 |

Riêng T3/2026:

| Metric | Số lượng |
|---|---:|
| sales_order_t3 | 1,132 |
| order_line_t3 | 8,723 |
| fact_sales_t3 | 8,723 |

Kiểm tra đã pass:

- `sales_order`, `order_line`, `fact_sales` khớp tổng số dòng.
- T3/2026 có đủ 1,132 đơn.
- T3/2026 có đủ 8,723 dòng chi tiết.
- `fact_sales` có đủ 8,723 dòng tháng 3.
- Không có `order_line` thiếu trong `fact_sales`.
- `min(order_date) = 2025-01-02`.
- `max(order_date) = 2026-03-31`.
- Không còn ngày placeholder `1970-01-01`.

### 2.3. Địa lý đã pass patch

Luồng địa lý hiện tại:

```text
province raw + province_correction_map -> province_clean
customer.province_id -> province_clean.province_id
fact_sales geography synced from customer + province_clean
```

Nguyên tắc đã chốt:

- `province` là bảng raw, chỉ giữ để audit.
- `province_clean` là dimension địa lý dùng cho dashboard.
- PowerBI không dùng `province` raw cho dashboard chính.
- `fact_sales.province_id`, `fact_sales.province_name`, `fact_sales.region` đã sync từ `customer + province_clean`.

Kết quả địa lý sau patch:

| Vùng | fact_rows | total_quantity | total_revenue |
|---|---:|---:|---:|
| Miền Bắc | 20,226 | 54,740 | 81.63 tỷ |
| Miền Trung | 4,584 | 14,002 | 21.41 tỷ |
| Miền Nam | 829 | 3,144 | 6.03 tỷ |
| Chưa xác định | 115 | 260 | 0.381 tỷ |

Còn 4 customer thiếu `province_id`:

1. `KH-00004`: address `NULL`.
2. `KH-00711`: có Lâm Đồng nhưng chưa nằm trong danh mục `province_clean`.
3. `KH-00722`: có Tây Ninh nhưng chưa nằm trong danh mục `province_clean`.
4. `KH-00757`: có Khánh Hòa nhưng chưa nằm trong danh mục `province_clean`.

### 2.4. Product, group, color, customer đã audit ổn

Nguyên tắc dùng trong dashboard:

- Nếu còn `line_id_fk` hoặc `group_code` `NULL` thì không xóa.
- Hiển thị nhóm đó là `Chưa phân loại`.
- Dùng `base_color` trong dashboard chính.
- Không normalize màu lại trong Power Query nếu database đã có `base_color`.

---

## 3. NHỮNG ĐIỂM TRONG GUIDE CŨ PHẢI CẬP NHẬT

### 3.1. Không dùng `province` raw nữa

Mọi chỗ trước đây import `tnbike.province` phải đổi sang:

```text
tnbike.province_clean
```

### 3.2. Không giữ số liệu địa lý cũ

Không dùng lại các số cũ như:

```text
97 customer thiếu province_id
5.88 tỷ doanh thu Chưa xác định
Miền Nam 4 đại lý
```

Sau patch, phải dùng bộ số đã clean:

```text
4 customer thiếu province_id
115 fact rows Chưa xác định
0.381 tỷ doanh thu Chưa xác định
```

### 3.3. Không normalize color bằng Power Query nếu DB đã có `base_color`

Hướng cũ dùng `Text.Proper([color])` không còn là hướng chính.

Dashboard nên:

- Dùng `base_color` cho KPI, slicer, heatmap tổng quan.
- Dùng `color` cho drill-down chi tiết nếu cần.

### 3.4. MoM cũ phải tách logic

Phải tách thành:

1. `Calendar MoM %`
   - So sánh tháng liền trước theo lịch.
   - Nếu thiếu T12/2025 thì T1/2026 trả `BLANK()`.
2. `Previous Available Growth %`
   - So với kỳ dữ liệu liền trước có trong dataset.
   - Có thể dùng để so T1/2026 với T3/2025.
   - Không gọi là MoM.

### 3.5. BCG dùng bản clean

Giữ các cải tiến đã chốt:

- Dùng median thay vì average.
- Thêm `New Launch`.
- Thêm `revenue_share_pct`.
- Ghi rõ annotation.

Nhưng phải dùng view:

```text
v_bcg_matrix_clean
```

---

## 4. BẢNG VÀ VIEW NÊN IMPORT VÀO POWERBI

### 4.1. Kết nối PowerBI -> PostgreSQL

```text
Server:   localhost
Database: tnbike_db
User:     postgres
Schema:   tnbike
```

> [!CAUTION]
> Không hardcode password vào tài liệu. Dùng cấu hình thực tế trong `DB_CONFIG`.

### 4.2. Bảng nên import

| Table/View | Vai trò | Ghi chú |
|---|---|---|
| `tnbike.fact_sales` | Fact trung tâm | Bảng chính cho hầu hết visuals |
| `tnbike.sales_order` | Header đơn hàng | Dùng đối soát số đơn |
| `tnbike.order_line` | Chi tiết gốc | Chỉ import nếu cần drill đến dòng gốc |
| `tnbike.customer` | Dimension đại lý | Dùng RFM |
| `tnbike.product` | Dimension SKU | Dùng drill-down |
| `tnbike.product_line` | Dimension dòng sản phẩm | Dùng hierarchy |
| `tnbike.product_group` | Dimension nhóm sản phẩm | Dùng slicer |
| `tnbike.province_clean` | Dimension địa lý sạch | Thay cho `province` raw |
| `tnbike.email_log` | Audit kỹ thuật | Không bắt buộc cho main dashboard |
| `v_monthly_sales_clean` | View thời gian | Page 1, 2 |
| `v_product_performance_clean` | View product | Page 3 |
| `v_geo_sales_clean` | View địa lý | Page 5 |
| `v_customer_rfm_clean` | View RFM | Page 4 |
| `v_bcg_matrix_clean` | View BCG | Page 3 |
| `v_data_quality_summary` | View quality | Note nhỏ Page 1 hoặc appendix |

### 4.3. Bảng không dùng cho dashboard chính

| Table | Lý do |
|---|---|
| `tnbike.province` | Bảng raw còn để audit |
| `tnbike.province_correction_map` | Chỉ là rule transform |

---

## 5. SQL VIEWS CẦN TẠO TRONG POSTGRESQL TRƯỚC KHI IMPORT

File triển khai chuẩn:

- [powerbi_views.sql](d:/Đề thi và Data - Vòng 1 - Data Explorers/TPT_Data-Explorers-2026/database/views/powerbi_views.sql)

`dashboard_powerbi_guide.md` giữ vai trò mô tả logic và phạm vi sử dụng.

Sau khi bỏ Page 6, bộ view chính còn 6 view:

1. `v_monthly_sales_clean`
2. `v_product_performance_clean`
3. `v_geo_sales_clean`
4. `v_customer_rfm_clean`
5. `v_bcg_matrix_clean`
6. `v_data_quality_summary`

`v_pipeline_status` không còn nằm trong flow chính của PowerBI dashboard.

### 5.1. `v_monthly_sales_clean`

```sql
CREATE OR REPLACE VIEW tnbike.v_monthly_sales_clean AS
SELECT
    fiscal_year,
    fiscal_quarter,
    fiscal_month,
    MAKE_DATE(fiscal_year::int, fiscal_month::int, 1) AS month_start,
    fiscal_year::TEXT || '-T' || fiscal_month::TEXT AS period_label,
    COUNT(DISTINCT so_number) AS order_count,
    COUNT(*) AS fact_rows,
    COUNT(DISTINCT customer_code) AS active_dealers,
    COUNT(DISTINCT product_code) AS active_skus,
    SUM(quantity) AS total_quantity,
    SUM(line_total) AS total_revenue,
    AVG(line_total) AS avg_line_total,
    SUM(line_total) / NULLIF(COUNT(DISTINCT so_number), 0) AS avg_revenue_per_order,
    SUM(line_total) / NULLIF(COUNT(DISTINCT customer_code), 0) AS avg_revenue_per_dealer
FROM tnbike.fact_sales
GROUP BY
    fiscal_year,
    fiscal_quarter,
    fiscal_month
ORDER BY
    fiscal_year,
    fiscal_month;
```

### 5.2. `v_product_performance_clean`

```sql
CREATE OR REPLACE VIEW tnbike.v_product_performance_clean AS
SELECT
    COALESCE(group_code, 'UNCLASSIFIED') AS group_code,
    COALESCE(group_name, 'Chưa phân loại') AS group_name,
    COALESCE(line_name, 'Chưa phân loại') AS line_name,
    product_code,
    product_name,
    COALESCE(color, 'Chưa xác định') AS color,
    COALESCE(base_color, 'Chưa xác định') AS base_color,
    COUNT(DISTINCT so_number) AS order_count,
    COUNT(DISTINCT customer_code) AS active_dealers,
    SUM(quantity) AS total_quantity,
    SUM(line_total) AS total_revenue,
    AVG(unit_price) AS avg_unit_price,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
FROM tnbike.fact_sales
GROUP BY
    COALESCE(group_code, 'UNCLASSIFIED'),
    COALESCE(group_name, 'Chưa phân loại'),
    COALESCE(line_name, 'Chưa phân loại'),
    product_code,
    product_name,
    COALESCE(color, 'Chưa xác định'),
    COALESCE(base_color, 'Chưa xác định');
```

### 5.3. `v_geo_sales_clean`

```sql
CREATE OR REPLACE VIEW tnbike.v_geo_sales_clean AS
SELECT
    COALESCE(region, 'Chưa xác định') AS region,
    COALESCE(province_name, 'Chưa xác định') AS province_name,
    COUNT(*) AS fact_rows,
    COUNT(DISTINCT customer_code) AS active_dealers,
    COUNT(DISTINCT so_number) AS order_count,
    COUNT(DISTINCT product_code) AS active_skus,
    SUM(quantity) AS total_quantity,
    SUM(line_total) AS total_revenue,
    SUM(line_total) / NULLIF(COUNT(DISTINCT customer_code), 0) AS avg_revenue_per_dealer
FROM tnbike.fact_sales
GROUP BY
    COALESCE(region, 'Chưa xác định'),
    COALESCE(province_name, 'Chưa xác định');
```

Ghi chú:

- View này dùng geography đã sync trong `fact_sales`.
- Không join `tnbike.province` raw.
- Nếu cần matrix `Region x Product Group`, dùng trực tiếp `fact_sales` hoặc tạo view phụ riêng.

### 5.4. `v_customer_rfm_clean`

```sql
CREATE OR REPLACE VIEW tnbike.v_customer_rfm_clean AS
WITH rfm_raw AS (
    SELECT
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        c.tax_code,
        c.address,
        COALESCE(f.province_name, 'Chưa xác định') AS province_name,
        COALESCE(f.region, 'Chưa xác định') AS region,
        MIN(f.order_date) AS first_order_date,
        MAX(f.order_date) AS last_order_date,
        DATE '2026-03-31' - MAX(f.order_date) AS recency_days,
        COUNT(DISTINCT f.so_number) AS frequency,
        COUNT(*) AS fact_rows,
        COUNT(DISTINCT f.product_code) AS sku_count,
        SUM(f.quantity) AS total_quantity,
        SUM(f.line_total) AS monetary
    FROM tnbike.fact_sales f
    JOIN tnbike.customer c
        ON c.customer_code = f.customer_code
    GROUP BY
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        c.tax_code,
        c.address,
        COALESCE(f.province_name, 'Chưa xác định'),
        COALESCE(f.region, 'Chưa xác định')
),
rfm_scored AS (
    SELECT *,
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 60  THEN 4
            WHEN recency_days <= 90  THEN 3
            WHEN recency_days <= 180 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6  THEN 4
            WHEN frequency >= 3  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE 1
        END AS f_score,
        CASE
            WHEN monetary >= 1000000000 THEN 5
            WHEN monetary >= 300000000  THEN 4
            WHEN monetary >= 100000000  THEN 3
            WHEN monetary >= 30000000   THEN 2
            ELSE 1
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
```

### 5.5. `v_bcg_matrix_clean`

```sql
CREATE OR REPLACE VIEW tnbike.v_bcg_matrix_clean AS
WITH revenue_by_line AS (
    SELECT
        line_name,
        group_code,
        group_name,
        SUM(CASE
            WHEN fiscal_year = 2026 AND fiscal_month BETWEEN 1 AND 3
            THEN line_total ELSE 0
        END) AS rev_q1_2026,
        SUM(CASE
            WHEN fiscal_year = 2025 AND fiscal_month BETWEEN 1 AND 3
            THEN line_total ELSE 0
        END) AS rev_q1_2025,
        SUM(line_total) AS total_revenue,
        SUM(quantity) AS total_qty,
        COUNT(DISTINCT product_code) AS sku_count,
        COUNT(DISTINCT customer_code) AS active_dealers
    FROM tnbike.fact_sales
    WHERE line_name IS NOT NULL
      AND group_code IS NOT NULL
    GROUP BY
        line_name,
        group_code,
        group_name
),
with_growth AS (
    SELECT *,
        ROUND(
            100.0 * (rev_q1_2026 - rev_q1_2025) / NULLIF(rev_q1_2025, 0),
            1
        ) AS growth_pct_yoy
    FROM revenue_by_line
),
with_median AS (
    SELECT *,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_revenue) OVER () AS median_revenue,
        SUM(total_revenue) OVER () AS total_classified_revenue
    FROM with_growth
)
SELECT
    line_name,
    group_code,
    group_name,
    rev_q1_2025,
    rev_q1_2026,
    growth_pct_yoy,
    total_revenue,
    total_qty,
    sku_count,
    active_dealers,
    median_revenue,
    ROUND(
        100.0 * total_revenue / NULLIF(total_classified_revenue, 0),
        1
    ) AS revenue_share_pct,
    CASE
        WHEN rev_q1_2025 = 0 AND rev_q1_2026 > 0 THEN 'New Launch'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Stars'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) <= 0 THEN 'Cash Cows'
        WHEN total_revenue <= median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Question Marks'
        ELSE 'Dogs'
    END AS bcg_category
FROM with_median;
```

> [!IMPORTANT]
> BCG Matrix dùng doanh thu nội bộ làm proxy thị phần. Chỉ bao gồm product lines đã phân loại. Tăng trưởng tính theo Q1/2025 vs Q1/2026 do thiếu dữ liệu T4-T12/2025.

### 5.6. `v_data_quality_summary`

```sql
CREATE OR REPLACE VIEW tnbike.v_data_quality_summary AS
SELECT
    'customers_missing_province' AS issue,
    COUNT(*)::NUMERIC AS issue_count,
    NULL::NUMERIC AS affected_revenue
FROM tnbike.customer
WHERE province_id IS NULL

UNION ALL

SELECT
    'fact_rows_missing_geography',
    COUNT(*)::NUMERIC,
    SUM(line_total)::NUMERIC
FROM tnbike.fact_sales
WHERE province_id IS NULL
   OR province_name IS NULL
   OR region IS NULL

UNION ALL

SELECT
    'sku_missing_group',
    COUNT(DISTINCT product_code)::NUMERIC,
    SUM(line_total)::NUMERIC
FROM tnbike.fact_sales
WHERE line_id_fk IS NULL
   OR group_code IS NULL

UNION ALL

SELECT
    'customers_missing_tax_code',
    COUNT(*)::NUMERIC,
    NULL::NUMERIC
FROM tnbike.customer
WHERE tax_code IS NULL
   OR TRIM(tax_code) = '';
```

---

## 6. DAX MEASURES

File triển khai chuẩn:

- [powerbi_dax_measures.md](d:/Đề thi và Data - Vòng 1 - Data Explorers/TPT_Data-Explorers-2026/docs/powerbi_dax_measures.md)

Phần dưới đây là bản tóm tắt để bám khi build dashboard.

```dax
Total Revenue = SUM(fact_sales[line_total])
Total Quantity = SUM(fact_sales[quantity])
Total Orders = DISTINCTCOUNT(fact_sales[so_number])
Active Dealers = DISTINCTCOUNT(fact_sales[customer_code])
Avg Revenue per Order = DIVIDE([Total Revenue], [Total Orders])
Avg Revenue per Dealer = DIVIDE([Total Revenue], [Active Dealers])
```

### 6.1. Calendar MoM

```dax
Revenue Calendar MoM % =
VAR cur = [Total Revenue]
VAR prev =
    CALCULATE(
        [Total Revenue],
        DATEADD('Date'[Date], -1, MONTH)
    )
RETURN
DIVIDE(cur - prev, prev)
```

Lưu ý:

- T1/2026 sẽ `BLANK()` vì thiếu T12/2025.
- Đây là hành vi đúng.

### 6.2. Previous Available Growth

```dax
Revenue Previous Available Period =
VAR curPeriod = MAX(fact_sales[fiscal_year]) * 12 + MAX(fact_sales[fiscal_month])
VAR prevPeriod =
    MAXX(
        FILTER(
            ALL(fact_sales[fiscal_year], fact_sales[fiscal_month]),
            fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month] < curPeriod
        ),
        fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month]
    )
RETURN
CALCULATE(
    [Total Revenue],
    FILTER(
        ALL(fact_sales),
        fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month] = prevPeriod
    )
)
```

```dax
Revenue Previous Available Growth % =
VAR cur = [Total Revenue]
VAR prev = [Revenue Previous Available Period]
RETURN
DIVIDE(cur - prev, prev)
```

### 6.3. YoY

```dax
Revenue YoY % =
VAR curYear = MAX(fact_sales[fiscal_year])
VAR curMonth = MAX(fact_sales[fiscal_month])
VAR cur = [Total Revenue]
VAR prev =
    CALCULATE(
        [Total Revenue],
        REMOVEFILTERS(fact_sales[fiscal_year], fact_sales[fiscal_month]),
        fact_sales[fiscal_year] = curYear - 1,
        fact_sales[fiscal_month] = curMonth
    )
RETURN
DIVIDE(cur - prev, prev)
```

### 6.4. Q1 và T3

```dax
Revenue Q1 2025 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2025, fact_sales[fiscal_quarter] = 1)

Revenue Q1 2026 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2026, fact_sales[fiscal_quarter] = 1)

Growth Q1 YoY =
DIVIDE([Revenue Q1 2026] - [Revenue Q1 2025], [Revenue Q1 2025])

Revenue T3 2025 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2025, fact_sales[fiscal_month] = 3)

Revenue T3 2026 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2026, fact_sales[fiscal_month] = 3)
```

### 6.5. Pareto và churn

```dax
Revenue Share Top 20pct =
VAR dealerTable =
    ADDCOLUMNS(
        ALLSELECTED(fact_sales[customer_code]),
        "DealerRevenue", [Total Revenue]
    )
VAR topNValue =
    ROUNDUP(COUNTROWS(dealerTable) * 0.2, 0)
VAR topDealers =
    TOPN(topNValue, dealerTable, [DealerRevenue], DESC)
VAR topRevenue =
    SUMX(topDealers, [DealerRevenue])
RETURN
DIVIDE(topRevenue, [Total Revenue])
```

```dax
Churn Risk Dealers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_code]),
    FILTER(
        VALUES(fact_sales[customer_code]),
        CALCULATE(MAX(fact_sales[order_date])) < DATE(2026, 1, 1)
    )
)
```

---

## 7. NĂM MÀN HÌNH DASHBOARD

### Page 1 - Executive Overview

Visuals:

- KPI cards: total revenue, revenue T3/2026, total orders, total quantity, active dealers.
- KPI tăng trưởng: T3 YoY, Q1 YoY, Previous Available Growth.
- Monthly revenue chart 6 điểm dữ liệu.
- Q1/2025 vs Q1/2026 comparison.
- Small note/table từ `v_data_quality_summary`.
- Text note: `T3/2026 imported 1,132 orders | 8,723 order lines | 8,723 fact rows`.

### Page 2 - Time Analysis

Visuals:

- Clustered bar T1-T3 theo năm.
- Matrix month x year với revenue, quantity.
- YoY % by month.
- Previous Available Growth.

Lưu ý:

- Không claim seasonality mạnh từ 6 điểm.
- Không forecast dài hạn từ 6 điểm.

### Page 3 - Product Analysis

Visuals:

- Revenue by `group_name`.
- Top product lines.
- Top SKU.
- Heatmap `line_name x base_color`.
- BCG scatter từ `v_bcg_matrix_clean`.
- Card cho nhóm `Chưa phân loại`.

### Page 4 - Dealer / Customer / RFM

Visuals:

- Cards theo segment: Champions, Loyal, At Risk, Hibernating, Lost.
- Scatter R/F/M.
- Top customers by monetary.
- At Risk customers.
- Big Spender customers.
- Pareto top 20% dealers.

### Page 5 - Geography Analysis

Visuals:

- Revenue by region.
- Top province by revenue.
- Province treemap.
- Active dealers by region.

Lưu ý:

- Dùng geography clean.
- Không dùng lại các con số cũ trước patch.
- Giữ nhóm `Chưa xác định`.

---

## 8. INSIGHTS KINH DOANH NÊN GIỮ

1. T3 là tháng đỉnh trong phạm vi dữ liệu hiện có.
2. Có concentration risk theo đại lý và địa lý.
3. Nhóm `Chưa phân loại` là data quality issue có ảnh hưởng business.
4. Có nhóm single-purchase churn cần retention.
5. BCG chỉ là internal proxy, cần annotation rõ.

---

## 9. THỨ TỰ THỰC HIỆN

```text
Bước 1 - Tạo 6 SQL views
Bước 1a - Chạy file `database/views/powerbi_views.sql`
Bước 2 - Import bảng và views vào PowerBI
Bước 3 - Tạo Date Table và relationships
Bước 4 - Tạo DAX measures theo `docs/powerbi_dax_measures.md`
Bước 5 - Build 5 pages
Bước 6 - Thêm insights và notes data quality
```

---

## 10. LƯU Ý QUAN TRỌNG KHI TRÌNH BÀY

| Vấn đề thực tế | Cách xử lý trong dashboard |
|---|---|
| Chỉ có 6 tháng data | Ghi rõ `Data range: T1-T3/2025 & T1-T3/2026` |
| Thiếu T4-T12/2025 | Không diễn giải như chuỗi tháng liên tục |
| Chưa phân loại | Không ẩn đi, biến thành insight |
| Geography unresolved | Giữ `Chưa xác định`, không bịa tỉnh |
| BCG là internal proxy | Ghi annotation rõ |

---

*Power BI Desktop | PostgreSQL tnbike_db localhost*
