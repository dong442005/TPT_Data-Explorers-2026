SET search_path TO tnbike, public;

-- 1. RFM Analysis View (Đã chuẩn hóa nguồn địa lý từ bảng province_clean)
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

-- 2. BCG Matrix View (Bao gồm 100% doanh thu)
CREATE OR REPLACE VIEW tnbike.v_bcg_matrix AS
WITH revenue_by_line AS (
    SELECT
        COALESCE(line_name, 'Chưa phân loại') AS line_name,
        COALESCE(group_code, 'UNKNOWN') AS group_code,
        COALESCE(group_name, 'Chưa phân loại') AS group_name,
        -- Đã bao gồm toàn bộ 100% doanh thu, kể cả 55 SKU chưa phân loại (14.12 tỷ)
        SUM(CASE WHEN fiscal_year=2026 AND fiscal_month BETWEEN 1 AND 3 THEN line_total ELSE 0 END) AS rev_q1_2026,
        SUM(CASE WHEN fiscal_year=2025 AND fiscal_month BETWEEN 1 AND 3 THEN line_total ELSE 0 END) AS rev_q1_2025,
        SUM(line_total) AS total_revenue,
        SUM(quantity)   AS total_qty
    FROM tnbike.fact_sales
    GROUP BY COALESCE(line_name, 'Chưa phân loại'), COALESCE(group_code, 'UNKNOWN'), COALESCE(group_name, 'Chưa phân loại')
),
with_growth AS (
    SELECT *,
        -- YoY chỉ tính được Q1 (T1-T3) vì đây là khoảng duy nhất có data đầy đủ cả 2 năm.
        ROUND(100.0 * (rev_q1_2026 - rev_q1_2025) / NULLIF(rev_q1_2025, 0), 1) AS growth_pct_yoy
    FROM revenue_by_line
),
with_median AS (
    SELECT *,
        -- Dùng MEDIAN thay vì AVG làm ngưỡng "thị phần cao/thấp"
        (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_revenue) FROM with_growth) AS median_revenue,
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
    -- Tỷ trọng trong tổng doanh thu classified
    ROUND(100.0 * total_revenue / NULLIF(total_classified_revenue, 0), 1) AS revenue_share_pct,
    CASE
        WHEN rev_q1_2025 = 0 AND rev_q1_2026 > 0 THEN 'New Launch'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Stars'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) <= 0 THEN 'Cash Cows'
        WHEN total_revenue <= median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Question Marks'
        ELSE 'Dogs'
    END AS bcg_category
FROM with_median
ORDER BY total_revenue DESC;

-- 3. Pipeline Status View (Cho trang Vận hành)
CREATE OR REPLACE VIEW tnbike.v_pipeline_status AS
SELECT
    processing_status,
    COUNT(*) AS email_count
FROM tnbike.email_log
GROUP BY processing_status;

-- 4. Data Quality Summary View (Dành cho Audit)
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
