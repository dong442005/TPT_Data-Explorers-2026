# 📊 Hướng dẫn Dashboard PowerBI — Hạng mục B
## Data Explorers 2026 | Thống Nhất Bike | 30 điểm
### ✅ Đã kiểm tra thực tế từ Database (24/05/2026)

---

## 1. SỐ LIỆU THỰC TẾ TRONG DATABASE

> [!IMPORTANT]
> Dữ liệu thực tế **chỉ có 6 tháng** — không phải 14 tháng như tài liệu ban đầu nói.
> - **BTC cung cấp:** T1, T2, T3/2025 + T1, T2/2026 (5 tháng)
> - **Team tự extract:** T3/2026 từ email/PDF pipeline (1 tháng)

### Phân bổ data theo tháng

| Năm | Tháng | Số đơn | Số dòng | Sản lượng | Doanh thu | Đại lý active | MoM |
|---|---|---|---|---|---|---|---|
| 2025 | T1 | 61 | 339 | 1,837 | 3.20 tỷ | 46 | — |
| 2025 | T2 | 185 | 1,892 | 5,030 | 6.34 tỷ | 141 | +98.2% |
| 2025 | T3 | 447 | 5,184 | 14,609 | 18.58 tỷ | 242 | +193.2% |
| 2026 | T1 | 482 | 4,778 | 12,541 | 21.14 tỷ | 290 | +13.7%* |
| 2026 | T2 | 452 | 4,838 | 12,522 | 19.39 tỷ | 268 | -8.3% |
| 2026 | T3 | **1,132** | **8,723** | **25,607** | **40.80 tỷ** | **394** | **+110.4%** |
| **TỔNG** | | **2,759** | **25,754** | **72,146** | **109.45 tỷ** | **798** | |

> *MoM T1/2026 so với T3/2025 (bỏ qua khoảng trống T4-T12/2025)

> [!WARNING]
> **Không có dữ liệu T4 → T12/2025** — Đây là khoảng trống lớn. Chỉ có thể so sánh YoY đúng nghĩa cho T1, T2, T3.

### So sánh cùng kỳ (YoY) — chỉ có 3 cặp tháng

| Tháng | Doanh thu 2025 | Doanh thu 2026 | YoY | Sản lượng 2025 | Sản lượng 2026 | YoY qty |
|---|---|---|---|---|---|---|
| T1 | 3.20 tỷ | 21.14 tỷ | **+560.8%** | 1,837 | 12,541 | +583% |
| T2 | 6.34 tỷ | 19.39 tỷ | **+206.0%** | 5,030 | 12,522 | +149% |
| T3 | 18.58 tỷ | 40.80 tỷ | **+119.6%** | 14,609 | 25,607 | +75% |

---

## 2. DATA QUALITY ISSUES CẦN BIẾT

> [!CAUTION]
> Có một số vấn đề data quality đã được xử lý qua DB patch, nhưng vẫn ảnh hưởng trực tiếp đến thiết kế dashboard.

| Vấn đề | Con số thực tế | Ảnh hưởng | Xử lý trong PowerBI |
|---|---|---|---|
| **55 SKU chưa map vào product_line/group** | 55/265 SKU (21%) → 7,668 chiếc (11%) → 14.12 tỷ (12.9%) | Trang 3 sẽ có nhóm "Chưa xếp loại" lớn thứ 2 | Tạo nhóm "Chưa phân loại" trong visual |
| **4 Customer thiếu province_id** | 4/798 KH → 381 triệu doanh thu | Trang 5 địa lý bị thiếu một lượng nhỏ | Label là "Chưa xác định" |
| **"Đen" vs "đen" (viết hoa/thường)** | **Đã được sửa hoàn toàn qua DB patch** (`db_data_quality_patch.sql`) | Dữ liệu màu sắc đã chuẩn hóa | **Không cần xử lý thêm** |
| **Miền Nam chỉ có 7 đại lý** | 7 DL / 3,144 chiếc / 6.03 tỷ | Bản đồ miền Nam rất thưa | Ghi chú trong visual insight |
| **Miền Bắc áp đảo** | 625/798 DL (78.3%) | Dashboard lệch hẳn về miền Bắc | Highlight trong insight |

### Region Distribution thực tế
| Vùng | Số đại lý | Sản lượng | Doanh thu | Tỷ trọng DT |
|---|---|---|---|---|
| Miền Bắc | 625 (78.3%) | 54,740 chiếc | 81.63 tỷ | **74.6%** |
| Miền Trung | 162 (20.3%) | 14,002 chiếc | 21.41 tỷ | 19.6% |
| Miền Nam | **7 (0.9%)** | 3,144 chiếc | 6.03 tỷ | 5.5% |
| Chưa xác định | 4 (0.5%) | 260 chiếc | 0.38 tỷ | 0.3% |

> [!NOTE]
> Bảng `province_clean` trong DB đã xử lý phần lớn dữ liệu địa lý lỗi từ file gốc, map thành công 93 khách hàng bị mất địa chỉ vào tỉnh thành tương ứng. Tuy nhiên, phân bố region vẫn bị lệch tự nhiên: Miền Bắc 625 đại lý, Miền Nam 7 đại lý.

### Top 10 tỉnh doanh thu
| Tỉnh | Vùng | Số đại lý | Doanh thu |
|---|---|---|---|
| Hà Nội | Miền Bắc | 272 | 41.14 tỷ |
| Thanh Hóa | Miền Trung | 69 | 9.49 tỷ |
| Ninh Bình | Miền Bắc | 27 | 5.91 tỷ |
| TP. Hồ Chí Minh | Miền Nam | 3 | 5.78 tỷ |
| Nghệ An | Miền Trung | 27 | 5.72 tỷ |
| Hải Phòng | Miền Bắc | 39 | 5.37 tỷ |
| Hưng Yên | Miền Bắc | 56 | 4.91 tỷ |
| Phú Thọ | Miền Bắc | 41 | 4.00 tỷ |
| Bắc Ninh | Miền Bắc | 33 | 3.78 tỷ |
| Bắc Giang | Miền Bắc | 12 | 3.45 tỷ |

---

## 3. THỰC TẾ CÁC DIMENSION

### Sản phẩm
| Nhóm | SKU | Sản lượng | Doanh thu | Lưu ý |
|---|---|---|---|---|
| CITYBIKE_P (Xe phổ thông) | 83 | 43,439 | 65.93 tỷ | **Nhóm lớn nhất — 60.2%** |
| **Chưa phân loại (NULL)** | 55 | 7,668 | 14.12 tỷ | ⚠️ 12.9% doanh thu thiếu group |
| KIDBIKE_1 (Xe trẻ em 1) | 42 | 10,074 | 12.55 tỷ | |
| SPORTBIKE_A (Thể thao nhôm) | 26 | 2,480 | 7.03 tỷ | |
| KIDBIKE_2 (Xe trẻ em 2) | 23 | 6,204 | 5.57 tỷ | |
| SPORTBIKE_S (Thể thao thép) | 36 | 2,281 | 4.24 tỷ | |
| **TỔNG** | **265** | **72,146** | **109.45 tỷ** | |

### Top 5 Product Lines bán chạy nhất
| Dòng xe | Nhóm | Sản lượng | Doanh thu | Số đại lý |
|---|---|---|---|---|
| Xe New 26 | CITYBIKE_P | 10,127 | 15.22 tỷ | 542 |
| Xe New 24 | CITYBIKE_P | 6,790 | 9.44 tỷ | 472 |
| Xe LD 26 | CITYBIKE_P | 4,856 | 8.69 tỷ | 320 |
| Xe LD 24-01_2023 | CITYBIKE_P | 3,885 | 5.95 tỷ | 349 |
| Xe GN 06-26 2.0 | CITYBIKE_P | 3,625 | 5.50 tỷ | 383 |

### Top 5 màu sắc
| Màu | Sản lượng | Doanh thu | Lưu ý |
|---|---|---|---|
| Đen | 10,764 | 18.02 tỷ | **Màu #1 Doanh thu** (Đã chuẩn hóa) |
| Kem | 11,829 | 17.52 tỷ | Màu #1 Sản lượng |
| Ghi | 7,553 | 12.78 tỷ | |
| Trắng | 5,486 | 8.93 tỷ | |
| Hồng | 6,897 | 8.70 tỷ | |

### Đại lý (Customer)
| Chỉ số | Giá trị |
|---|---|
| Tổng đại lý trong DB | 798 |
| Đại lý có giao dịch | 798 |
| Top đại lý (KH-00091) | 55 đơn, 9.587 tỷ, last order T3/2026 |
| Đại lý churn nặng nhất | KH-00002: 1 đơn hàng T1/2025, không mua từ đó (503 ngày) |
| Email log status | 1,132 READY_TO_INSERT |

---

## 4. Kết nối PowerBI → PostgreSQL

```
Server:   localhost
Database: tnbike_db
User:     postgres
Password: 442005 (hoặc theo config của bạn)
Schema:   tnbike
```

> [!CAUTION]
> Không hardcode password vào file tài liệu. Password thực tế nằm trong `DB_CONFIG` của các file Python trong project.

### Bảng/View cần import
| Bảng/View | Dùng cho | Lưu ý |
|---|---|---|
| `tnbike.fact_sales` | **TẤT CẢ** (bảng chính) | 25,754 dòng |
| `tnbike.customer` | Trang 4 - Đại lý | 798 rows |
| `tnbike.province_clean` | Trang 5 - Địa lý | Đã được chuẩn hóa từ file patch |
| `tnbike.product` | Trang 3 - Sản phẩm | 265 rows |
| `tnbike.product_group` | Trang 3 | 5 rows |
| `tnbike.product_line` | Trang 3 | ~68 rows |
| `tnbike.email_log` | Trang 6 - Vận hành | 1,132 rows |
| `tnbike.sales_order` | Trang 6 - Vận hành | 2,759 rows |

---

## 5. SQL Views cần tạo trong PostgreSQL trước khi import

### 5.1 RFM Analysis View (Cập nhật sau EDA)
```sql
CREATE OR REPLACE VIEW tnbike.v_rfm_analysis AS
WITH rfm_raw AS (
    SELECT
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        COALESCE(pr.province_name_clean, 'Chưa xác định') AS province_name,
        COALESCE(pr.region_clean, 'Chưa xác định') AS region,
        MAX(f.order_date) AS last_order_date,
        DATE '2026-03-31' - MAX(f.order_date) AS recency_days,
        COUNT(DISTINCT f.so_number) AS frequency,
        SUM(f.line_total) AS monetary
    FROM tnbike.fact_sales f
    JOIN tnbike.customer c ON c.customer_code = f.customer_code
    LEFT JOIN tnbike.province_clean pr ON pr.province_id = c.province_id
    GROUP BY f.customer_code, c.customer_name, c.customer_tier, 
             pr.province_name_clean, pr.region_clean
),
rfm_scored AS (
    SELECT *,
        -- R Score: Dựa trên chu kỳ B2B
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 60  THEN 4
            WHEN recency_days <= 90  THEN 3
            WHEN recency_days <= 180 THEN 2
            ELSE                          1
        END AS r_score,
        
        -- F Score: Dựa trên phân bố B2B 6 tháng
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6  THEN 4
            WHEN frequency >= 3  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE                      1
        END AS f_score,
        
        -- M Score: Dựa trên doanh thu thực tế
        CASE
            WHEN monetary >= 1000000000  THEN 5  -- >=1 tỷ
            WHEN monetary >= 300000000   THEN 4  -- >=300 triệu
            WHEN monetary >= 100000000   THEN 3  -- >=100 triệu
            WHEN monetary >= 30000000    THEN 2  -- >=30 triệu
            ELSE                              1  -- <30 triệu
        END AS m_score
    FROM rfm_raw
)
SELECT *,
    r_score + f_score + m_score AS rfm_total, -- Tổng điểm (để làm màu heatmap nếu cần)
    CASE
        -- Rất siêng mua, mua gần đây và chi cực nhiều -> Vua/Tướng (Bảo vệ bằng mọi giá)
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        
        -- Mua gần đây, mua thường xuyên nhưng chưa chi siêu lớn -> Khách trung thành
        WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        
        -- CHỈ CÓ TRONG B2B: Lâu lâu mới mua 1 đơn, nhưng đơn đó trị giá tiền tỷ!
        WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 4 THEN 'Big Spender'
        
        -- Mọi thứ ở mức khá, có tiềm năng upsell thêm
        WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 2 THEN 'Potential'
        
        -- Mua gần đây, nhưng mới có 1 đơn và tiền chưa nhiều -> Khách mới tinh
        WHEN r_score >= 4 AND f_score = 1  AND m_score <= 3 THEN 'New'
        
        -- Từng mua tốt, chi nhiều nhưng dạo này LÂU RỒI KHÔNG THẤY MUA -> Có nguy cơ bỏ đi sang đối thủ
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
        
        -- Đã ngủ đông lâu ngày, từng có mua bán khá khẩm
        WHEN r_score <= 2 AND (f_score >= 2 OR m_score >= 2) THEN 'Hibernating'
        
        -- Mua đúng 1 lần rất ít tiền, và bặt vô âm tín luôn -> Coi như đã mất
        ELSE 'Lost'
    END AS rfm_segment
FROM rfm_scored;

```

> [!TIP]
> View trên đã được **tùy chỉnh cho B2B**. Nó thay thế hàm NTILE(5) ban đầu bằng các ngưỡng business-driven, và thêm nhóm **"Big Spender"** (chi lớn nhưng tần suất thấp — đại lý mua sỉ theo quý). Chú ý đã chuyển sang dùng `province_clean`.

### 5.2 BCG Matrix View

> [!NOTE]
> **Phiên bản cải tiến v2** — sửa 3 lỗi thiết kế so với bản gốc (xem giải thích bên dưới SQL).

```sql
CREATE OR REPLACE VIEW tnbike.v_bcg_matrix AS
WITH revenue_by_line AS (
    SELECT
        line_name,
        group_code,
        group_name,
        -- Chỉ lấy dòng xe đã phân loại (line_name IS NOT NULL).
        -- 55 SKU chưa phân loại (14.12 tỷ, 12.9%) bị loại — xem cột revenue_share_pct để rõ scope.
        SUM(CASE WHEN fiscal_year=2026 AND fiscal_month BETWEEN 1 AND 3 THEN line_total ELSE 0 END) AS rev_q1_2026,
        SUM(CASE WHEN fiscal_year=2025 AND fiscal_month BETWEEN 1 AND 3 THEN line_total ELSE 0 END) AS rev_q1_2025,
        SUM(line_total) AS total_revenue,
        SUM(quantity)   AS total_qty
    FROM tnbike.fact_sales
    WHERE line_name IS NOT NULL
    GROUP BY line_name, group_code, group_name
),
with_growth AS (
    SELECT *,
        -- YoY chỉ tính được Q1 (T1-T3) vì đây là khoảng duy nhất có data đầy đủ cả 2 năm.
        -- NULLIF(rev_q1_2025, 0) → tránh chia-cho-0; kết quả NULL nếu không có data 2025.
        ROUND(100.0 * (rev_q1_2026 - rev_q1_2025) / NULLIF(rev_q1_2025, 0), 1) AS growth_pct_yoy
    FROM revenue_by_line
),
with_median AS (
    SELECT *,
        -- [FIX 2] Dùng MEDIAN thay vì AVG làm ngưỡng "thị phần cao/thấp".
        -- Lý do: Doanh thu product line lệch phải (Xe New 26 = 15.22 tỷ kéo AVG lên cao).
        -- Median robust với outlier — cùng lý luận đã áp dụng cho RFM Monetary scoring.
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
    median_revenue,
    -- [FIX 1] Tỷ trọng trong tổng doanh thu classified — dùng làm bubble size trong Scatter Plot Power BI.
    -- Giúp người xem thấy rõ BCG chỉ cover một phần tổng doanh thu.
    ROUND(100.0 * total_revenue / NULLIF(total_classified_revenue, 0), 1) AS revenue_share_pct,
    CASE
        -- [FIX 3] Xe mới ra mắt trong 2026: không có lịch sử Q1/2025 để so YoY.
        -- Không nên xếp vào Stars/Dogs khi thiếu dữ liệu — tách riêng thành 'New Launch'.
        WHEN rev_q1_2025 = 0 AND rev_q1_2026 > 0
            THEN 'New Launch'

        -- Stars: Doanh thu CAO (trên median) + Tăng trưởng DƯƠNG → đầu tư mạnh
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) > 0
            THEN 'Stars'

        -- Cash Cows: Doanh thu CAO + Tăng trưởng KHÔNG dương → khai thác, không đầu tư thêm
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) <= 0
            THEN 'Cash Cows'

        -- Question Marks: Doanh thu THẤP + Tăng trưởng DƯƠNG → cân nhắc đầu tư
        WHEN total_revenue <= median_revenue AND COALESCE(growth_pct_yoy, 0) > 0
            THEN 'Question Marks'

        -- Dogs: Doanh thu THẤP + Tăng trưởng KHÔNG dương → xem xét loại bỏ
        ELSE 'Dogs'
    END AS bcg_category
FROM with_median
ORDER BY total_revenue DESC;
```

> [!IMPORTANT]
> **3 cải tiến so với bản gốc — lý do kỹ thuật + business:**
>
> | # | Thay đổi | Lý do |
> |---|---|---|
> | **Fix 1** | Thêm cột `revenue_share_pct` | BCG chỉ cover ~87.1% doanh thu (55 SKU chưa phân loại bị loại). Người xem dashboard phải thấy scope này rõ ràng — không để mislead. |
> | **Fix 2** | `AVG` → `PERCENTILE_CONT(0.5)` (Median) | Xe New 26 (15.22 tỷ) là outlier lớn. Nếu dùng AVG, ngưỡng bị kéo lên làm nhiều dòng xe "trung bình thực sự" bị gán "thị phần thấp". Median robust với phân bố lệch — cùng logic đã áp dụng cho RFM Monetary. |
> | **Fix 3** | Thêm `'New Launch'` category | Dòng xe chỉ có data 2026 (không có Q1/2025) bị `growth_pct_yoy = NULL → COALESCE = 0` → gán nhầm "Dogs". Xe mới ra mắt phải được tách riêng, không đánh giá sớm. |
>
> **Những gì không thể thay đổi với data hiện tại:**
> - Vẫn so sánh Q1/2025 vs Q1/2026 — đây là cặp dữ liệu đầy đủ **duy nhất** (không có T4-T12/2025).
> - Vẫn dùng "Internal BCG" (so sánh nội bộ) — không có dữ liệu thị trường ngành xe đạp Việt Nam.
> - **Bắt buộc ghi annotation trong Power BI:** `"BCG Matrix dùng doanh thu nội bộ làm proxy thị phần. Chỉ bao gồm 210/265 SKU đã phân loại (~87.1% doanh thu). Tăng trưởng tính theo Q1/2025 vs Q1/2026."`

### 5.3 Pipeline Status View (cho Trang 6)
```sql
CREATE OR REPLACE VIEW tnbike.v_pipeline_status AS
SELECT
    processing_status,
    COUNT(*) AS email_count
FROM tnbike.email_log
GROUP BY processing_status;
-- Kết quả: READY_TO_INSERT = 1,132
```

---

## 6. DAX Measures — Chỉnh theo 6 tháng thực tế

```dax
// === MEASURES CƠ BẢN ===
Total Revenue = SUM(fact_sales[line_total])
Total Quantity = SUM(fact_sales[quantity])
Total Orders = DISTINCTCOUNT(fact_sales[so_number])
Active Dealers = DISTINCTCOUNT(fact_sales[customer_code])
Avg Revenue per Order = DIVIDE([Total Revenue], [Total Orders])
Avg Revenue per Dealer = DIVIDE([Total Revenue], [Active Dealers])

// === MoM (áp dụng được toàn bộ 6 điểm) ===
// ⚠️ Lưu ý: MoM T1/2026 sẽ trả về BLANK vì không có data T12/2025 (gap T4-T12/2025).
// Đây là hành vi đúng — không phải lỗi. Ghi chú trong dashboard tooltip.
Revenue MoM % =
VAR cur = [Total Revenue]
VAR prev = CALCULATE([Total Revenue], DATEADD(fact_sales[order_date], -1, MONTH))
RETURN DIVIDE(cur - prev, ABS(prev))

// === YoY — CHỈ CÓ THỂ SO SÁNH T1, T2, T3 ===
Revenue YoY % =
VAR cur = [Total Revenue]
VAR same_last_year = CALCULATE([Total Revenue],
    DATEADD(fact_sales[order_date], -1, YEAR))
RETURN DIVIDE(cur - same_last_year, ABS(same_last_year))

// Q1 so sánh (Q1 = fiscal_quarter=1 = T1+T2+T3)
Revenue Q1 2025 = CALCULATE([Total Revenue], fact_sales[fiscal_year]=2025, fact_sales[fiscal_quarter]=1)
Revenue Q1 2026 = CALCULATE([Total Revenue], fact_sales[fiscal_year]=2026, fact_sales[fiscal_quarter]=1)
Growth Q1 YoY = DIVIDE([Revenue Q1 2026] - [Revenue Q1 2025], [Revenue Q1 2025])
// Q1/2025 = 3.20+6.34+18.58 = 28.12 tỷ | Q1/2026 = 21.14+19.39+40.80 = 81.33 tỷ
// Kết quả thực tế: (81.33-28.12)/28.12 = +189.2%

// T3 (tháng cao điểm có data của cả 2 năm)
Revenue T3 2025 = CALCULATE([Total Revenue], fact_sales[fiscal_year]=2025, fact_sales[fiscal_month]=3)
Revenue T3 2026 = CALCULATE([Total Revenue], fact_sales[fiscal_year]=2026, fact_sales[fiscal_month]=3)
// Kết quả thực tế T3: +119.6%

// === PARETO — TOP 20% DEALERS ===
Revenue Share Top 20pct =
VAR top_n = ROUNDUP(COUNTROWS(VALUES(fact_sales[customer_code])) * 0.2, 0)
VAR top_dealers = TOPN(top_n,
    SUMMARIZE(ALL(fact_sales), fact_sales[customer_code], "r", [Total Revenue]),
    [r], DESC)
VAR top_rev = SUMX(top_dealers, [r])
RETURN DIVIDE(top_rev, CALCULATE([Total Revenue], ALL(fact_sales[customer_code])))
// Để tính: top 160 dealers (20% của 798) chiếm bao nhiêu %

// === CHURN SIGNAL ===
// Lấy ngày cuối cùng trong data = 2026-03-31
Churn Risk Dealers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_code]),
    FILTER(
        VALUES(fact_sales[customer_code]),
        CALCULATE(MAX(fact_sales[order_date])) < DATE(2026, 1, 1)
    )
)
// Đại lý không mua trong 2026 (last order trong 2025) = churn signal

// === KPI TARGETS Q2/2026 ===
// Đặt mục tiêu dựa trên Q1/2026 + growth rate
Target Revenue Q2 2026 = [Revenue Q1 2026] * 1.10   // +10% vs Q1/2026
Target Qty Q2 2026 =
CALCULATE([Total Quantity], fact_sales[fiscal_year]=2026, fact_sales[fiscal_quarter]=1) * 1.10

// === GROUP REVENUE SHARE ===
Group Revenue Share =
DIVIDE([Total Revenue],
    CALCULATE([Total Revenue], ALL(fact_sales[group_code])))
```

---

## 7. Sáu màn hình bắt buộc

### 📄 TRANG 1: Tổng quan kinh doanh

**KPI Cards (số thực):**
- Tổng doanh thu: **109.45 tỷ** (6 tháng)
- Doanh thu T3/2026: **40.80 tỷ** (+110.4% MoM, +119.6% YoY)
- Tổng đơn hàng: **2,759**
- Sản lượng: **72,146 chiếc**
- Đại lý active: **798** (nhưng chỉ 394 đặt hàng trong T3/2026)

**Phễu Pipeline T3/2026 (từ email_log):**
```
1,132 emails đã xử lý
    └── 1,132 READY_TO_INSERT (100% thành công)
        └── 1,132 đơn → sales_order
```

**Layout:**
```
[Card] 40.8 tỷ doanh thu T3/2026
[Card] 1,132 đơn T3/2026 (từ pipeline email)
[Card] 25,607 chiếc sản lượng T3/2026
[Card] 394 đại lý active T3/2026
[KPI] T3 YoY: +119.6%   [KPI] T3 MoM: +110.4%

[Line Chart: Doanh thu 6 tháng — 6 điểm dữ liệu]
   2025-T1: 3.2ty | T2: 6.3ty | T3: 18.6ty || 2026-T1: 21.1ty | T2: 19.4ty | T3: 40.8ty
   ↑ Annotation: "Không có data T4-T12/2025"

[Clustered Bar: Q1/2025 vs Q1/2026 by Group (Q1 YoY: +189.2%)]
[Funnel: Pipeline 1,132 emails T3/2026]
```

> [!WARNING]
> Line chart chỉ có 6 điểm — **bỏ qua T4-T12/2025**. Cần thêm chú thích "Dữ liệu hiện có: T1-T3/2025 và T1-T3/2026" để tránh hiểu nhầm.

---

### 📄 TRANG 2: Phân tích thời gian

**Thực tế có thể làm:**
- ✅ So sánh YoY: T1, T2, T3 (chỉ 3 cặp)
- ✅ MoM trend: cả 6 tháng
- ✅ Q1/2025 vs Q1/2026 (đủ data)
- ❌ Pattern mùa vụ: **không đủ data** (thiếu T4-T12/2025)

**Layout:**
```
[Line: 6 tháng — highlight T3 là cao nhất cả 2 năm]
[Clustered Bar: T1/T2/T3 mỗi năm, grouped by year]
[Matrix: Month (T1-T3) × Year (2025/2026) × Revenue — so sánh trực tiếp]
[Bar: MoM % change — 5 mũi tên +98% +193% (gap) +14% -8% +110%]
```

**DAX cụ thể cho matrix so sánh:**
```dax
// Tạo measure để hiển thị cả 2 năm cạnh nhau
Revenue by Month =
CALCULATE([Total Revenue],
    KEEPFILTERS(fact_sales[fiscal_month]))
```

---

### 📄 TRANG 3: Phân tích sản phẩm

**Thực tế cần lưu ý:**
- **55 SKU (21%) chưa có group** → nhóm "Chưa phân loại" chiếm 14.12 tỷ (12.9%)
- Xe New 26 là dòng bán chạy nhất (10,127 chiếc)
- Màu Kem #1 bán chạy nhất về số lượng (11,829 chiếc), màu Đen #1 về doanh thu (18.02 tỷ)
- Khắc phục màu "đen/Đen" đã hoàn thành tại Database. BCG tính trên ~87.1% doanh thu.

**Layout:**
```
[Slicer: Group] [Slicer: Line]

[Donut: Revenue by Group — 5 nhóm + 1 "Chưa phân loại"]
[Bar: Top 10 Product Lines]

[Scatter BCG: line_name × (total_revenue, growth_pct_yoy), Size=revenue_share_pct]
   5 màu: Stars / Cash Cows / Question Marks / Dogs / New Launch (xe mới 2026)
   Stars: Xe New 26/24 (revenue trên median + growth dương)
   Cash Cows: dòng xe revenue cao nhưng tăng trưởng ≤0
   Annotation: "BCG cover 210/265 SKU (~87.1% DT). 55 SKU chưa phân loại không xuất hiện."

[Matrix Heatmap: Line × Color → Quantity]
   Không cần dùng Power Query fix màu, DB đã chuẩn.
```

---

### 📄 TRANG 4: Phân tích đại lý

**Số liệu thực tế:**
- Tổng: 798 đại lý có giao dịch
- Top dealer: KH-00091 (9.587 tỷ, 55 đơn, còn active T3/2026)
- Churn nặng: KH-00002, KH-00003, KH-00005... (chỉ 1 đơn từ T1/2025, ~500 ngày không mua)
- Concentration risk: cần tính top 20% = 160 đại lý chiếm bao nhiêu %

**Layout:**
```
[Card] Champions  [Card] Loyal  [Card] At Risk  [Card] Lost/Churn(recency>365 ngay)

[Scatter: F_score(trục Y) × R_score(trục X), Size=monetary, Color=rfm_segment]
   — Data từ view v_rfm_analysis

[Table: Top 20 đại lý]     [Table: Churn Risk (recency > 90 ngày)]
  KH | Revenue | Freq       KH | Last Order | Days | Revenue
  KH-00091 | 9.59 tỷ | 55  KH-00002 | 2025-01-06 | 503 | 3.5M

[Bar: Pareto — Tích lũy % doanh thu theo số đại lý]
   Annotation: "Top 20% (~160 DL) chiếm X% doanh thu"
```

---

### 📄 TRANG 5: Phân tích địa lý

> [!IMPORTANT]
> **Bất thường địa lý cần highlight trong dashboard:**
> - Miền Bắc: 625 đại lý, 81.63 tỷ (74.6%)
> - Miền Nam: **chỉ 7 đại lý** — rất bất thường cho thị trường lớn nhất VN
> - 4 KH (0.5%) không có thông tin tỉnh thành

**Layout:**
```
[Card] Miền Bắc: 81.63 tỷ (74.6%)   [Card] Miền Trung: 21.41 tỷ (19.6%)
[Card] Miền Nam: 6.03 tỷ (5.5%)     [Card] Chưa xác định: 0.38 tỷ (0.3%)

[Map/Treemap: Province → Revenue (màu gradient)]
   Highlight: Hà Nội 41.14 tỷ (37.6% tổng doanh thu!)

[Bar: Top 10 tỉnh]                  [Bar: YoY by Province (chỉ T1-T3)]
  HN: 41.14ty | TH: 9.49ty          (chỉ tính được với tỉnh có data cả 2 năm)
```

**Insight bắt buộc cho trang này:**
> Hà Nội chiếm 272/798 đại lý (34%) và 41.14/109.45 tỷ (37.6%) doanh thu → Rủi ro tập trung địa lý cực cao. Cần mở rộng sang các tỉnh/thành phố khác.

---

### 📄 TRANG 6: Trạng thái vận hành (Pipeline)

**Số liệu email_log thực tế:**
- Tổng: 1,132 emails
- READY_TO_INSERT: 1,132 (100%)
- Không có FAILED → Pipeline hoạt động hoàn hảo

**Layout:**
```
[Card] 1,132 emails xử lý   [Card] 1,132 đơn insert   [Card] 0 lỗi   [Card] 100% tỷ lệ thành công

[Funnel: Emails → Extract → Validate → Insert]
   1,132 → 1,132 → 1,132 → 1,132 (100% mỗi bước)

[Line/Bar: Phân bố đơn hàng T3/2026 theo ngày (31 ngày)]
   Từ fact_sales WHERE fiscal_year=2026 AND fiscal_month=3

[Table: Thông tin kỹ thuật pipeline]
   Nguồn: 1,132 file .eml + PDF đính kèm
   Method: pdfplumber + RegEx
   DB: PostgreSQL tnbike_db
   Runtime: ~X phút (ghi vào đây)

[Comparison: T3/2025 vs T3/2026]
   Đơn: 447 → 1,132 (+153%)
   Doanh thu: 18.58 tỷ → 40.80 tỷ (+119.6%)
```

---

## 8. ≥5 Insights có giá trị kinh doanh (theo format đề bài)

### Insight 1 — T3 luôn là tháng đỉnh (2 năm liên tiếp)
> **Phát hiện:** T3/2025 (18.58 tỷ) và T3/2026 (40.80 tỷ) đều là tháng cao nhất trong năm tương ứng. T3/2026 tăng **+119.6%** so với T3/2025 và gấp **1.93 lần** T1/2026 (40.80/21.14). Nhìn rộng hơn, Q1/2026 (81.33 tỷ) tăng **+189.2%** so với Q1/2025 (28.12 tỷ).
> **Ý nghĩa:** Tháng 3 là chu kỳ cao điểm của TNBike, nhiều khả năng do đại lý ôm hàng trước mùa hè và dịp Quốc tế Lao động 1/5. Dữ liệu T3 là kỳ "bình thường mới" — không nên so sánh T1/T2 với T3 trực tiếp.
> **Khuyến nghị:** Lên kế hoạch sản xuất tăng 30-40% vào tháng 2-3 hàng năm; đảm bảo tồn kho sẵn sàng cho đại lý đặt hàng sớm từ tháng 2.

### Insight 2 — Concentration Risk: Hà Nội + 1 đại lý áp đảo
> **Phát hiện:** KH-00091 (1 đại lý) có doanh thu 9.587 tỷ = **8.76% tổng doanh thu cả 6 tháng**. Hà Nội (272 đại lý) chiếm 41.14 tỷ = **37.6% tổng**. Top 5% đại lý chiếm ước tính >40% doanh thu.
> **Ý nghĩa:** Rủi ro tập trung kép — theo địa lý và theo đại lý. Nếu KH-00091 ngừng hoạt động hoặc chuyển sang đối thủ, doanh thu tức thì giảm ~9%. Nếu thị trường Hà Nội bị ảnh hưởng, doanh thu giảm gần 38%.
> **Khuyến nghị:** (1) Ký hợp đồng độc quyền/ưu đãi đặc biệt với top 10 đại lý. (2) Đặt mục tiêu phát triển đại lý các khu vực khác để pha loãng tỷ trọng của Hà Nội.

### Insight 3 — Miền Nam: Thị trường lớn, đại lý cực ít
> **Phát hiện:** Miền Nam (TP.HCM + các tỉnh) chỉ có **7 đại lý** nhưng đạt 6.03 tỷ doanh thu — trung bình **861 triệu/đại lý** (6.03 tỷ/7), cao hơn nhiều so với mức trung bình **130 triệu/đại lý** của Miền Bắc (81.63 tỷ / 625 đại lý).
> **Ý nghĩa:** Mỗi đại lý miền Nam hiệu quả gấp **~6.6 lần** so với đại lý miền Bắc (861M / 130M) — chứng tỏ tiềm năng thị trường miền Nam rất lớn nhưng mạng lưới lưới đại lý còn quá thưa thớt.
> **Khuyến nghị:** Đầu tư mạnh vào mở rộng mạng lưới đại lý miền Nam — mục tiêu tăng thêm 20-30 đại lý tại TP.HCM, Bình Dương, Đồng Nai trong năm 2026.

### Insight 4 — "Chưa xếp loại" chiếm 12.9% doanh thu
> **Phát hiện:** Có 55/265 SKU (21%) chưa được map vào nhóm sản phẩm nào, tạo ra nhóm "Chưa phân loại" với doanh thu 14.12 tỷ (12.9% tổng). Tuy đã được cải thiện từ mức 23% ban đầu qua DB patch nhưng đây vẫn là nhóm doanh thu lớn thứ 2.
> **Ý nghĩa:** 12.9% doanh thu bị thất thoát khỏi cơ cấu phân tích sản phẩm (nhất là ma trận BCG), dẫn tới rủi ro sai lệch khi đánh giá hiệu năng danh mục.
> **Khuyến nghị:** Đội ngũ Data cần review 55 SKU còn lại để update dữ liệu gốc trên hệ thống quản lý vào các Product Lines chính xác trong lần chạy ETL tiếp theo.

### Insight 5 — Đại lý một lần (Single-Purchase Churn)
> **Phát hiện:** Nhiều đại lý chỉ có đúng **1 đơn hàng** từ T1/2025 và không quay lại sau 500 ngày (ví dụ KH-00002, KH-00003, KH-00005...). Nhóm này đã "mất" hoàn toàn sau lần mua đầu tiên.
> **Ý nghĩa:** Tỷ lệ giữ chân đại lý mới (first-purchase retention) có thể rất thấp. Chi phí tìm đại lý mới tốn kém hơn giữ chân đại lý cũ 5-7 lần trong B2B.
> **Khuyến nghị:** Xây dựng chương trình onboarding 90 ngày cho đại lý mới: liên hệ sau đơn hàng đầu tiên, ưu đãi đơn hàng thứ 2, nhân viên kinh doanh phụ trách trực tiếp.

---

## 9. Thứ tự thực hiện

```
BƯỚC 1 — SQL (5 phút)
├── Chạy 5.1: CREATE VIEW v_rfm_analysis
├── Chạy 5.2: CREATE VIEW v_bcg_matrix
└── Chạy 5.3: CREATE VIEW v_pipeline_status

BƯỚC 2 — PowerBI kết nối (10 phút)
├── Get Data → PostgreSQL → localhost / tnbike_db
├── Import: fact_sales, customer, province_clean, product, product_group, product_line,
│           email_log, sales_order + 3 views vừa tạo
└── Thiết lập Relationships (fact_sales là bảng trung tâm)

BƯỚC 3 — Power Query cleanup (5 phút)
├── Thêm cột "group_display": if group_code = null then "Chưa phân loại" else group_name
└── Tạo cột "period_label": "2025-T1", "2025-T2" ... "2026-T3"

BƯỚC 4 — DAX Measures (30 phút)
└── Tạo tất cả measures ở mục 6

BƯỚC 5 — Build 6 trang (2-3 giờ)
├── Trang 1: Executive Overview
├── Trang 2: Time Analysis (6 điểm dữ liệu, chú thích rõ)
├── Trang 3: Product (BCG + Drilldown + Heatmap màu - Lưu ý màu đã chuẩn)
├── Trang 4: Dealer RFM (từ view v_rfm_analysis)
├── Trang 5: Geographic (Treemap vì Map có thể khó với 63 tỉnh)
└── Trang 6: Pipeline Operations

BƯỚC 6 — Insights & Polish (1 giờ)
├── Thêm text boxes với 5 insights format đề bài
└── Chỉnh màu sắc, font, layout đồng nhất
```

---

## 10. Lưu ý quan trọng khi trình bày

| Vấn đề thực tế | Cách xử lý trong Dashboard |
|---|---|
| Chỉ có 6 tháng data | Thêm annotation "Data range: T1-T3/2025 & T1-T3/2026" |
| Thiếu T4-T12/2025 | Không vẽ line chart liên tục — dùng clustered bar chart |
| 12.9% doanh thu "Chưa phân loại" | Highlight là data quality issue, không ẩn đi |
| Miền Nam 7 đại lý | Đây là business insight quan trọng, không phải lỗi |
| Hà Nội chiếm 37.6% | Highlight trong insight về concentration risk |

---

*Deadline: 28/05/2026 | Tool: Power BI Desktop | DB: PostgreSQL tnbike_db localhost*
*Đã kiểm tra thực tế database ngày 24/05/2026, cập nhật bản vá Data Quality & Geo mới nhất*
