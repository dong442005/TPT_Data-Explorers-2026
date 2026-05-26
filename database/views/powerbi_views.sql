SET search_path TO tnbike, public;

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


CREATE OR REPLACE VIEW tnbike.v_product_performance_clean AS
SELECT
    COALESCE(group_code, 'UNCLASSIFIED') AS group_code,
    COALESCE(group_name, 'Chua phan loai') AS group_name,
    COALESCE(line_name, 'Chua phan loai') AS line_name,
    product_code,
    product_name,
    COALESCE(color, 'Chua xac dinh') AS color,
    COALESCE(base_color, 'Chua xac dinh') AS base_color,
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
    COALESCE(group_name, 'Chua phan loai'),
    COALESCE(line_name, 'Chua phan loai'),
    product_code,
    product_name,
    COALESCE(color, 'Chua xac dinh'),
    COALESCE(base_color, 'Chua xac dinh');


CREATE OR REPLACE VIEW tnbike.v_geo_sales_clean AS
SELECT
    COALESCE(region, 'Chua xac dinh') AS region,
    COALESCE(province_name, 'Chua xac dinh') AS province_name,
    COUNT(*) AS fact_rows,
    COUNT(DISTINCT customer_code) AS active_dealers,
    COUNT(DISTINCT so_number) AS order_count,
    COUNT(DISTINCT product_code) AS active_skus,
    SUM(quantity) AS total_quantity,
    SUM(line_total) AS total_revenue,
    SUM(line_total) / NULLIF(COUNT(DISTINCT customer_code), 0) AS avg_revenue_per_dealer
FROM tnbike.fact_sales
GROUP BY
    COALESCE(region, 'Chua xac dinh'),
    COALESCE(province_name, 'Chua xac dinh');


CREATE OR REPLACE VIEW tnbike.v_customer_rfm_clean AS
WITH rfm_raw AS (
    SELECT
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        c.tax_code,
        c.address,
        COALESCE(f.province_name, 'Chua xac dinh') AS province_name,
        COALESCE(f.region, 'Chua xac dinh') AS region,
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
        COALESCE(f.province_name, 'Chua xac dinh'),
        COALESCE(f.region, 'Chua xac dinh')
),
rfm_scored AS (
    SELECT *,
        CASE
            WHEN recency_days <= 30 THEN 5
            WHEN recency_days <= 60 THEN 4
            WHEN recency_days <= 90 THEN 3
            WHEN recency_days <= 180 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6 THEN 4
            WHEN frequency >= 3 THEN 3
            WHEN frequency >= 2 THEN 2
            ELSE 1
        END AS f_score,
        CASE
            WHEN monetary >= 1000000000 THEN 5
            WHEN monetary >= 300000000 THEN 4
            WHEN monetary >= 100000000 THEN 3
            WHEN monetary >= 30000000 THEN 2
            ELSE 1
        END AS m_score
    FROM rfm_raw
)
SELECT
    *,
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
    SELECT
        *,
        ROUND(100.0 * (rev_q1_2026 - rev_q1_2025) / NULLIF(rev_q1_2025, 0), 1) AS growth_pct_yoy
    FROM revenue_by_line
),
with_median AS (
    SELECT
        *,
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
    ROUND(100.0 * total_revenue / NULLIF(total_classified_revenue, 0), 1) AS revenue_share_pct,
    CASE
        WHEN rev_q1_2025 = 0 AND rev_q1_2026 > 0 THEN 'New Launch'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Stars'
        WHEN total_revenue > median_revenue AND COALESCE(growth_pct_yoy, 0) <= 0 THEN 'Cash Cows'
        WHEN total_revenue <= median_revenue AND COALESCE(growth_pct_yoy, 0) > 0 THEN 'Question Marks'
        ELSE 'Dogs'
    END AS bcg_category
FROM with_median;


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
