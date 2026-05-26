-- ============================================================
-- TNBIKE GEO CLEAN PATCH
-- Purpose:
--   1. Keep original tnbike.province as raw/audit source
--   2. Build tnbike.province_clean using explicit correction rules
--   3. Map customer records with NULL province_id from address when possible
--   4. Re-point customer FK to province_clean
--   5. Synchronize fact_sales geography from customer + province_clean
--
-- Safe design:
--   - Does NOT delete raw province table
--   - Does NOT fabricate province_id for customers without reliable address match
--   - Leaves unresolved geography as NULL for honest audit / dashboard "Chưa xác định"
-- ============================================================

SET search_path TO tnbike, public;

BEGIN;

-- ============================================================
-- 0. DROP OLD CUSTOMER -> province_clean FK IF RE-RUNNING PATCH
--    This allows province_clean to be rebuilt safely.
-- ============================================================

DO $$
DECLARE
    fk_name TEXT;
BEGIN
    SELECT conname INTO fk_name
    FROM pg_constraint c
    JOIN pg_class t1 ON c.conrelid = t1.oid
    JOIN pg_class t2 ON c.confrelid = t2.oid
    WHERE t1.relname = 'customer'
      AND t2.relname = 'province_clean'
      AND c.contype = 'f';

    IF fk_name IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE tnbike.customer DROP CONSTRAINT %I',
            fk_name
        );
    END IF;
END $$;


-- ============================================================
-- 1. CREATE CORRECTION MAP
--    This table stores ONLY correction rules.
--    Raw province rows not listed here will be kept as-is.
-- ============================================================

DROP TABLE IF EXISTS tnbike.province_correction_map CASCADE;

CREATE TABLE tnbike.province_correction_map (
    raw_province_id      INTEGER PRIMARY KEY,
    province_name_clean  VARCHAR(100) NOT NULL,
    region_clean         VARCHAR(50)  NOT NULL,
    mapping_type         VARCHAR(50)  NOT NULL,
    note                 TEXT,
    created_at           TIMESTAMPTZ  DEFAULT NOW()
);

COMMENT ON TABLE tnbike.province_correction_map IS
'Correction rules for raw province rows. Used to generate province_clean.';

COMMENT ON COLUMN tnbike.province_correction_map.raw_province_id IS
'province_id from tnbike.province raw table.';

COMMENT ON COLUMN tnbike.province_correction_map.mapping_type IS
'Correction type: fix_typo, normalize_text, district_to_province, address_to_province.';


-- ============================================================
-- 2. SEED CORRECTION RULES
-- ============================================================

INSERT INTO tnbike.province_correction_map (
    raw_province_id,
    province_name_clean,
    region_clean,
    mapping_type,
    note
)
VALUES
    (5,  'Hải Dương',       'Miền Bắc',   'district_to_province', 'Chí Linh thuộc Hải Dương'),
    (6,  'Bắc Ninh',        'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Bắc Ninh'),
    (7,  'Hòa Bình',        'Miền Bắc',   'normalize_text',       'Chuẩn hóa Hoà -> Hòa'),
    (10, 'Hà Nội',          'Miền Bắc',   'fix_typo',             'Hà Nộ -> Hà Nội'),

    (15, 'Hưng Yên',        'Miền Bắc',   'normalize_text',       'Lỗi lặp/xuống dòng'),
    (16, 'Hưng Yên',        'Miền Bắc',   'normalize_text',       'Chuẩn hóa viết hoa'),
    (17, 'Quảng Ninh',      'Miền Bắc',   'district_to_province', 'Hạ Long thuộc Quảng Ninh'),
    (18, 'Hải Dương',       'Miền Bắc',   'fix_typo',             'Hải Dươn -> Hải Dương'),

    (21, 'Quảng Nam',       'Miền Trung', 'district_to_province', 'Hội An thuộc Quảng Nam'),
    (22, 'Thanh Hóa',       'Miền Trung', 'address_to_province',  'Chuỗi địa chỉ thuộc Thanh Hóa'),
    (23, 'Hải Dương',       'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Hải Dương'),
    (25, 'Thanh Hóa',       'Miền Trung', 'address_to_province',  'Chuỗi địa chỉ thuộc Thanh Hóa'),

    (28, 'Nghệ An',         'Miền Trung', 'fix_typo',             'Nghệ A -> Nghệ An'),
    (31, 'Bình Thuận',      'Miền Trung', 'district_to_province', 'Phan Thiết thuộc Bình Thuận'),
    (32, 'Kiên Giang',      'Miền Nam',   'district_to_province', 'Phú Quốc thuộc Kiên Giang'),
    (34, 'Thanh Hóa',       'Miền Trung', 'address_to_province',  'Chuỗi địa chỉ thuộc Thanh Hóa'),
    (35, 'Hà Nam',          'Miền Bắc',   'district_to_province', 'Phủ Lý thuộc Hà Nam'),

    (39, 'Quảng Ninh',      'Miền Bắc',   'fix_typo',             'Quảng NinhSố -> Quảng Ninh'),
    (42, 'Thanh Hóa',       'Miền Trung', 'district_to_province', 'Sầm Sơn thuộc Thanh Hóa'),
    (43, 'Thừa Thiên Huế',  'Miền Trung', 'district_to_province', 'TP Huế thuộc Thừa Thiên Huế'),
    (44, 'Hưng Yên',        'Miền Bắc',   'district_to_province', 'TP Hưng Yên thuộc Hưng Yên'),
    (45, 'Hải Dương',       'Miền Bắc',   'district_to_province', 'TP Hải Dương thuộc Hải Dương'),
    (46, 'Hải Phòng',       'Miền Bắc',   'normalize_text',       'TP Hải Phòng -> Hải Phòng'),
    (47, 'Đà Nẵng',         'Miền Trung', 'normalize_text',       'TP Đà Nẵng -> Đà Nẵng'),

    (49, 'Thái Nguyên',     'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Thái Nguyên'),
    (50, 'Quảng Nam',       'Miền Trung', 'district_to_province', 'Tam Kỳ thuộc Quảng Nam'),
    (51, 'Thanh Hóa',       'Miền Trung', 'normalize_text',       'Thanh Hoá -> Thanh Hóa'),
    (55, 'Bắc Giang',       'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Bắc Giang'),
    (56, 'Bình Dương',      'Miền Nam',   'district_to_province', 'Thủ Dầu Một thuộc Bình Dương'),

    (60, 'Hà Tĩnh',         'Miền Trung', 'normalize_text',       'Tĩnh Hà Tĩnh -> Hà Tĩnh'),
    (61, 'Thanh Hóa',       'Miền Trung', 'normalize_text',       'Tĩnh Thanh Hoá -> Thanh Hóa'),
    (62, 'Hòa Bình',        'Miền Bắc',   'normalize_text',       'Tỉnh Hòa Bình. -> Hòa Bình'),
    (63, 'Điện Biên',       'Miền Bắc',   'address_to_province',  'TP Điện Biên Phủ thuộc Điện Biên'),

    (64, 'Quảng Ninh',      'Miền Bắc',   'district_to_province', 'Uông Bí thuộc Quảng Ninh'),
    (65, 'Nghệ An',         'Miền Trung', 'district_to_province', 'Vinh thuộc Nghệ An'),
    (67, 'Vĩnh Phúc',       'Miền Bắc',   'district_to_province', 'Vĩnh Yên thuộc Vĩnh Phúc'),
    (68, 'Thái Bình',       'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Thái Bình'),
    (71, 'Thanh Hóa',       'Miền Trung', 'address_to_province',  'Chuỗi địa chỉ thuộc Thanh Hóa'),
    (72, 'Hải Phòng',       'Miền Bắc',   'address_to_province',  'Chuỗi địa chỉ thuộc Hải Phòng'),
    (74, 'Quảng Bình',      'Miền Trung', 'district_to_province', 'Đồng Hới thuộc Quảng Bình')
ON CONFLICT (raw_province_id) DO UPDATE
SET
    province_name_clean = EXCLUDED.province_name_clean,
    region_clean        = EXCLUDED.region_clean,
    mapping_type        = EXCLUDED.mapping_type,
    note                = EXCLUDED.note;


-- ============================================================
-- 3. BUILD province_clean FROM raw province + correction map
--    Important:
--      - province_id is kept from raw province.
--      - Clean name/region are applied only when a correction rule exists.
--      - Otherwise, raw values are kept.
-- ============================================================

DROP TABLE IF EXISTS tnbike.province_clean CASCADE;

CREATE TABLE tnbike.province_clean AS
SELECT
    p.province_id,
    p.province_name AS province_name_raw,
    p.region        AS region_raw,

    COALESCE(m.province_name_clean, p.province_name) AS province_name_clean,
    COALESCE(m.region_clean, p.region)               AS region_clean,

    COALESCE(m.mapping_type, 'keep') AS mapping_type,
    m.note,
    p.created_at AS raw_created_at,
    NOW()        AS clean_created_at
FROM tnbike.province p
LEFT JOIN tnbike.province_correction_map m
    ON m.raw_province_id = p.province_id;

ALTER TABLE tnbike.province_clean
ADD CONSTRAINT pk_province_clean PRIMARY KEY (province_id);

CREATE INDEX IF NOT EXISTS idx_province_clean_name
ON tnbike.province_clean(province_name_clean);

CREATE INDEX IF NOT EXISTS idx_province_clean_region
ON tnbike.province_clean(region_clean);

CREATE INDEX IF NOT EXISTS idx_province_clean_mapping_type
ON tnbike.province_clean(mapping_type);


-- ============================================================
-- 4. MAP CUSTOMER WITH NULL province_id FROM ADDRESS
--    This step handles new customers added from March 2026 extraction.
--    It does NOT fabricate province_id if address has no reliable match.
--
--    Match rule:
--      - Match address against province_clean.province_name_clean.
--      - If multiple matches, choose the match appearing nearest the end
--        of address, then choose longer match.
--      - This avoids cases like "Xã Hà Nam, TP Hải Phòng"
--        being incorrectly mapped to Hà Nam instead of Hải Phòng.
-- ============================================================

WITH candidates AS (
    SELECT
        c.customer_code,
        pc.province_id,
        STRPOS(LOWER(c.address), LOWER(pc.province_name_clean)) AS match_pos,
        LENGTH(pc.province_name_clean) AS match_len
    FROM tnbike.customer c
    JOIN tnbike.province_clean pc
        ON c.address ILIKE '%' || pc.province_name_clean || '%'
    WHERE c.province_id IS NULL
      AND c.address IS NOT NULL
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_code
            ORDER BY match_pos DESC, match_len DESC
        ) AS rn
    FROM candidates
)
UPDATE tnbike.customer c
SET
    province_id = r.province_id,
    updated_at = NOW()
FROM ranked r
WHERE c.customer_code = r.customer_code
  AND r.rn = 1
  AND c.province_id IS NULL;


-- ============================================================
-- 5. DROP OLD CUSTOMER -> province FK
--    Only drops FK that truly references tnbike.province.
--    Does not use text matching, so it will not accidentally drop
--    province_clean FK on re-run.
-- ============================================================

DO $$
DECLARE
    fk_name TEXT;
BEGIN
    SELECT conname INTO fk_name
    FROM pg_constraint
    WHERE conrelid = 'tnbike.customer'::regclass
      AND contype = 'f'
      AND confrelid = 'tnbike.province'::regclass;

    IF fk_name IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE tnbike.customer DROP CONSTRAINT %I',
            fk_name
        );
    END IF;
END $$;


-- ============================================================
-- 6. ADD CUSTOMER -> province_clean FK
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_customer_province_clean'
          AND conrelid = 'tnbike.customer'::regclass
    ) THEN
        ALTER TABLE tnbike.customer
        ADD CONSTRAINT fk_customer_province_clean
        FOREIGN KEY (province_id)
        REFERENCES tnbike.province_clean(province_id);
    END IF;
END $$;


-- ============================================================
-- 7. SYNC fact_sales FROM customer + province_clean
--    fact_sales is denormalized, so geography must be refreshed
--    after customer/province standardization.
-- ============================================================

UPDATE tnbike.fact_sales f
SET
    province_id   = c.province_id,
    province_name = pc.province_name_clean,
    region        = pc.region_clean
FROM tnbike.customer c
LEFT JOIN tnbike.province_clean pc
    ON pc.province_id = c.province_id
WHERE f.customer_code = c.customer_code;


-- ============================================================
-- 8. VALIDATION QUERIES
--    These SELECT statements intentionally remain in the patch output
--    so pgAdmin/psql shows the final audit state after running.
-- ============================================================

-- 8.1 Table counts
SELECT 'province' AS table_name, COUNT(*) AS row_count FROM tnbike.province
UNION ALL
SELECT 'province_correction_map', COUNT(*) FROM tnbike.province_correction_map
UNION ALL
SELECT 'province_clean', COUNT(*) FROM tnbike.province_clean
UNION ALL
SELECT 'customer', COUNT(*) FROM tnbike.customer
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM tnbike.fact_sales;

-- 8.2 Province region distribution after cleaning
SELECT
    region_clean,
    COUNT(*) AS province_count
FROM tnbike.province_clean
GROUP BY region_clean
ORDER BY province_count DESC;

-- 8.3 Cleaned rows audit
SELECT
    province_id,
    province_name_raw,
    region_raw,
    province_name_clean,
    region_clean,
    mapping_type,
    note
FROM tnbike.province_clean
WHERE province_name_raw IS DISTINCT FROM province_name_clean
   OR region_raw IS DISTINCT FROM region_clean
ORDER BY province_id;

-- 8.4 Customer still missing province_id
SELECT
    COUNT(*) AS customers_missing_province
FROM tnbike.customer
WHERE province_id IS NULL;

-- 8.5 Customer province_id orphan check against province_clean
SELECT
    c.customer_code,
    c.customer_name,
    c.province_id
FROM tnbike.customer c
LEFT JOIN tnbike.province_clean pc
    ON pc.province_id = c.province_id
WHERE c.province_id IS NOT NULL
  AND pc.province_id IS NULL
ORDER BY c.customer_code;

-- 8.6 Current customer FK check
SELECT
    conname,
    conrelid::regclass  AS table_name,
    confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE conrelid = 'tnbike.customer'::regclass
  AND contype = 'f';

-- 8.7 fact_sales missing geography
SELECT
    COUNT(*) FILTER (WHERE province_id IS NULL)   AS fact_missing_province_id,
    COUNT(*) FILTER (WHERE province_name IS NULL) AS fact_missing_province_name,
    COUNT(*) FILTER (WHERE region IS NULL)        AS fact_missing_region
FROM tnbike.fact_sales;

-- 8.8 Remaining unresolved fact_sales geography by customer
SELECT
    f.customer_code,
    c.customer_name,
    c.address,
    COUNT(*) AS fact_rows
FROM tnbike.fact_sales f
JOIN tnbike.customer c
    ON c.customer_code = f.customer_code
WHERE f.province_id IS NULL
   OR f.province_name IS NULL
   OR f.region IS NULL
GROUP BY
    f.customer_code,
    c.customer_name,
    c.address
ORDER BY fact_rows DESC;

-- 8.9 Region summary for dashboard sanity check
SELECT
    COALESCE(region, 'Chưa xác định') AS region,
    COUNT(*) AS fact_rows,
    SUM(quantity) AS total_quantity,
    SUM(line_total) AS total_revenue
FROM tnbike.fact_sales
GROUP BY COALESCE(region, 'Chưa xác định')
ORDER BY total_revenue DESC;

COMMIT;
