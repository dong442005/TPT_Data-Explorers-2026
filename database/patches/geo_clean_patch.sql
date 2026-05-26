BEGIN;

-- ============================================================
-- 1. XÓA CÁC VIEW GEO CŨ KHÔNG DÙNG NỮA
-- ============================================================

DROP VIEW IF EXISTS tnbike.v_geo_mapping_audit CASCADE;
DROP VIEW IF EXISTS tnbike.v_region_sales_clean CASCADE;
DROP VIEW IF EXISTS tnbike.v_province_sales_clean CASCADE;
DROP VIEW IF EXISTS tnbike.v_fact_sales_geo_clean CASCADE;
DROP VIEW IF EXISTS tnbike.v_fact_sales_model CASCADE;
DROP VIEW IF EXISTS tnbike.dim_province_clean CASCADE;

-- ============================================================
-- 2. TẠO BẢNG province_alias_map VÀ SEED DỮ LIỆU
-- ============================================================

CREATE TABLE IF NOT EXISTS tnbike.province_alias_map (
    raw_province_id INTEGER PRIMARY KEY REFERENCES tnbike.province(province_id),
    province_name_clean VARCHAR(100) NOT NULL,
    region_clean VARCHAR(50) NOT NULL,
    mapping_type VARCHAR(50) DEFAULT 'CORRECTION',
    note TEXT
);

-- Seed mapping data cho tất cả 75 tỉnh thành thô
INSERT INTO tnbike.province_alias_map (raw_province_id, province_name_clean, region_clean, mapping_type, note) VALUES
  (1, 'Bắc Giang', 'Miền Bắc', 'EXACT', NULL),
  (2, 'Bắc Kạn', 'Miền Bắc', 'EXACT', NULL),
  (3, 'Bắc Ninh', 'Miền Bắc', 'EXACT', NULL),
  (4, 'Cao Bằng', 'Miền Bắc', 'EXACT', NULL),
  (5, 'Hải Dương', 'Miền Bắc', 'CITY_TO_PROVINCE', 'Chí Linh thuộc Hải Dương'),
  (6, 'Bắc Ninh', 'Miền Bắc', 'ADDRESS_PARSE', 'Cường Tráng - An Thịnh - Lương Tài - Bắc Ninh'),
  (7, 'Hòa Bình', 'Miền Bắc', 'CORRECTION', 'Hoà Bình -> Hòa Bình'),
  (8, 'Hà Giang', 'Miền Bắc', 'EXACT', NULL),
  (9, 'Hà Nam', 'Miền Bắc', 'EXACT', NULL),
  (10, 'Hà Nội', 'Miền Bắc', 'CORRECTION', 'Hà Nộ -> Hà Nội'),
  (11, 'Hà Nội', 'Miền Bắc', 'EXACT', NULL),
  (12, 'Hà Tĩnh', 'Miền Trung', 'EXACT', NULL),
  (13, 'Hòa Bình', 'Miền Bắc', 'EXACT', NULL),
  (14, 'Hưng Yên', 'Miền Bắc', 'EXACT', NULL),
  (15, 'Hưng Yên', 'Miền Bắc', 'CORRECTION', 'Hưng Yên trùng lặp'),
  (16, 'Hưng Yên', 'Miền Bắc', 'CORRECTION', 'Hưng yên -> Hưng Yên'),
  (17, 'Quảng Ninh', 'Miền Bắc', 'CITY_TO_PROVINCE', 'Hạ Long thuộc Quảng Ninh'),
  (18, 'Hải Dương', 'Miền Bắc', 'CORRECTION', 'Hải Dươn -> Hải Dương'),
  (19, 'Hải Dương', 'Miền Bắc', 'EXACT', NULL),
  (20, 'Hải Phòng', 'Miền Bắc', 'EXACT', NULL),
  (21, 'Quảng Nam', 'Miền Trung', 'CITY_TO_PROVINCE', 'Hội An thuộc Quảng Nam'),
  (22, 'Thanh Hóa', 'Miền Trung', 'ADDRESS_PARSE', 'Khu 2- thị trấn Kim Tân- Thạch Thành - Thanh Hóa'),
  (23, 'Hải Dương', 'Miền Bắc', 'ADDRESS_PARSE', 'Khu 6 – TT Gia Lộc – Huyện Gia Lộc – Hải Dương'),
  (24, 'Lào Cai', 'Miền Bắc', 'EXACT', NULL),
  (25, 'Thanh Hóa', 'Miền Trung', 'ADDRESS_PARSE', 'Lê Hoàn - Thị trấn Thọ Xuân - Huyện Thọ Xuân - Thanh Hoá'),
  (26, 'Lạng Sơn', 'Miền Bắc', 'EXACT', NULL),
  (27, 'Nam Định', 'Miền Bắc', 'EXACT', NULL),
  (28, 'Nghệ An', 'Miền Trung', 'CORRECTION', 'Nghệ A -> Nghệ An'),
  (29, 'Nghệ An', 'Miền Trung', 'EXACT', NULL),
  (30, 'Ninh Bình', 'Miền Bắc', 'EXACT', NULL),
  (31, 'Bình Thuận', 'Miền Nam', 'CITY_TO_PROVINCE', 'Phan Thiết thuộc Bình Thuận'),
  (32, 'Kiên Giang', 'Miền Nam', 'CITY_TO_PROVINCE', 'Phú Quốc thuộc Kiên Giang'),
  (33, 'Phú Thọ', 'Miền Bắc', 'EXACT', NULL),
  (34, 'Thanh Hóa', 'Miền Trung', 'ADDRESS_PARSE', 'Phố Kiểu - Yên Trường - Yên Định - Thanh Hoá'),
  (35, 'Hà Nam', 'Miền Bắc', 'CITY_TO_PROVINCE', 'Phủ Lý thuộc Hà Nam'),
  (36, 'Quảng Nam', 'Miền Trung', 'EXACT', NULL),
  (37, 'Quảng Ngãi', 'Miền Trung', 'EXACT', NULL),
  (38, 'Quảng Ninh', 'Miền Bắc', 'EXACT', NULL),
  (39, 'Quảng Ninh', 'Miền Bắc', 'CORRECTION', 'Quảng NinhSố -> Quảng Ninh'),
  (40, 'Quảng Trị', 'Miền Trung', 'EXACT', NULL),
  (41, 'Sơn La', 'Miền Bắc', 'EXACT', NULL),
  (42, 'Thanh Hóa', 'Miền Trung', 'CITY_TO_PROVINCE', 'Sầm Sơn thuộc Thanh Hóa'),
  (43, 'Thừa Thiên Huế', 'Miền Trung', 'CITY_TO_PROVINCE', 'TP Huế thuộc Thừa Thiên Huế'),
  (44, 'Hưng Yên', 'Miền Bắc', 'CITY_TO_PROVINCE', 'TP Hưng Yên -> Hưng Yên'),
  (45, 'Hải Dương', 'Miền Bắc', 'CITY_TO_PROVINCE', 'TP Hải Dương -> Hải Dương'),
  (46, 'Hải Phòng', 'Miền Bắc', 'CITY_TO_PROVINCE', 'TP Hải Phòng -> Hải Phòng'),
  (47, 'Đà Nẵng', 'Miền Trung', 'CITY_TO_PROVINCE', 'TP Đà Nẵng -> Đà Nẵng'),
  (48, 'Hồ Chí Minh', 'Miền Nam', 'CORRECTION', 'TP. Hồ Chí Minh -> Hồ Chí Minh'),
  (49, 'Thái Nguyên', 'Miền Bắc', 'ADDRESS_PARSE', 'TT Hương Sơn- Phú Bình- Thái Nguyên'),
  (50, 'Quảng Nam', 'Miền Trung', 'CITY_TO_PROVINCE', 'Tam Kỳ thuộc Quảng Nam'),
  (51, 'Thanh Hóa', 'Miền Trung', 'CORRECTION', 'Thanh Hoá -> Thanh Hóa'),
  (52, 'Thanh Hóa', 'Miền Trung', 'EXACT', NULL),
  (53, 'Thái Bình', 'Miền Bắc', 'EXACT', NULL),
  (54, 'Thái Nguyên', 'Miền Bắc', 'EXACT', NULL),
  (55, 'Bắc Giang', 'Miền Bắc', 'ADDRESS_PARSE', 'Thân Nhân Trung - TT Bích Động - Việt Yên - Bắc Giang'),
  (56, 'Bình Dương', 'Miền Nam', 'CITY_TO_PROVINCE', 'Thủ Dầu Một thuộc Bình Dương'),
  (57, 'Thừa Thiên Huế', 'Miền Trung', 'EXACT', NULL),
  (58, 'Tuyên Quang', 'Miền Bắc', 'EXACT', NULL),
  (59, 'Thái Bình', 'Miền Bắc', 'ADDRESS_PARSE', 'Tây Bình Cách - Xã Đông Xá - Huyện Đông Hưng - Thái Bình.'),
  (60, 'Hà Tĩnh', 'Miền Trung', 'CORRECTION', 'Tĩnh Hà Tĩnh -> Hà Tĩnh'),
  (61, 'Thanh Hóa', 'Miền Trung', 'CORRECTION', 'Tĩnh Thanh Hoá -> Thanh Hóa'),
  (62, 'Hòa Bình', 'Miền Bắc', 'CORRECTION', 'Tỉnh Hòa Bình. -> Hòa Bình'),
  (63, 'Điện Biên', 'Miền Bắc', 'ADDRESS_PARSE', 'Tổ 1 - Phường Mường Thanh - TP Điện Biên Phủ'),
  (64, 'Quảng Ninh', 'Miền Bắc', 'CITY_TO_PROVINCE', 'Uông Bí thuộc Quảng Ninh'),
  (65, 'Nghệ An', 'Miền Trung', 'CITY_TO_PROVINCE', 'Vinh thuộc Nghệ An'),
  (66, 'Vĩnh Phúc', 'Miền Bắc', 'EXACT', NULL),
  (67, 'Vĩnh Phúc', 'Miền Bắc', 'CITY_TO_PROVINCE', 'Vĩnh Yên thuộc Vĩnh Phúc'),
  (68, 'Thái Bình', 'Miền Bắc', 'ADDRESS_PARSE', 'phố số 6 - Thị trấn Diêm Điền - Huyện Thái Thụy - Thái Bình.'),
  (69, 'Điện Biên', 'Miền Bắc', 'EXACT', NULL),
  (70, 'Đà Nẵng', 'Miền Trung', 'EXACT', NULL),
  (71, 'Thanh Hóa', 'Miền Trung', 'ADDRESS_PARSE', 'Đường Nguyễn Trải - P Ba Đình TP Thanh Hoá'),
  (72, 'Hải Phòng', 'Miền Bắc', 'ADDRESS_PARSE', 'Đường Trang Quan - Xã An Đồng - Huyện An Dương - Hải Phòng.'),
  (73, 'Đắk Lắk', 'Miền Trung', 'EXACT', NULL),
  (74, 'Quảng Bình', 'Miền Trung', 'CITY_TO_PROVINCE', 'Đồng Hới thuộc Quảng Bình'),
  (75, 'Đồng Nai', 'Miền Nam', 'EXACT', NULL)
ON CONFLICT (raw_province_id) DO UPDATE 
SET province_name_clean = EXCLUDED.province_name_clean,
    region_clean = EXCLUDED.region_clean,
    mapping_type = EXCLUDED.mapping_type,
    note = EXCLUDED.note;

-- Ràng buộc khóa ngoại nếu chưa tồn tại
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_province_alias_raw'
          AND conrelid = 'tnbike.province_alias_map'::regclass
    ) THEN
        ALTER TABLE tnbike.province_alias_map
        ADD CONSTRAINT fk_province_alias_raw
        FOREIGN KEY (raw_province_id)
        REFERENCES tnbike.province(province_id);
    END IF;
END $$;

-- ============================================================
-- 3. TẠO BẢNG province_clean
-- ============================================================

DROP TABLE IF EXISTS tnbike.province_clean CASCADE;

CREATE TABLE tnbike.province_clean AS
SELECT
    p.province_id,
    p.province_name AS province_name_raw,
    p.region AS region_raw,
    m.province_name_clean,
    m.region_clean,
    m.mapping_type,
    m.note,
    p.created_at AS raw_created_at,
    NOW() AS clean_created_at
FROM tnbike.province p
LEFT JOIN tnbike.province_alias_map m
    ON p.province_id = m.raw_province_id;

-- Thêm PK và FK cho province_clean
ALTER TABLE tnbike.province_clean
ADD CONSTRAINT pk_province_clean
PRIMARY KEY (province_id);

ALTER TABLE tnbike.province_clean
ADD CONSTRAINT fk_province_clean_raw
FOREIGN KEY (province_id)
REFERENCES tnbike.province(province_id);

-- ============================================================
-- 4. CẬP NHẬT customer theo province_clean
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
-- 5. XÓA FK CŨ customer -> province nếu muốn ERD chỉ dùng province_clean
-- ============================================================

DO $$
DECLARE
    old_fk_name TEXT;
BEGIN
    SELECT conname INTO old_fk_name
    FROM pg_constraint
    WHERE conrelid = 'tnbike.customer'::regclass
      AND contype = 'f'
      AND pg_get_constraintdef(oid) ILIKE '%REFERENCES tnbike.province%';

    IF old_fk_name IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE tnbike.customer DROP CONSTRAINT %I',
            old_fk_name
        );
    END IF;
END $$;

-- ============================================================
-- 6. CẬP NHẬT fact_sales dùng province_clean
-- ============================================================

UPDATE tnbike.fact_sales AS f
SET
    province_name = pc.province_name_clean,
    region = pc.region_clean
FROM tnbike.province_clean AS pc
WHERE f.province_id = pc.province_id;

-- Gắn giá trị "Chưa xác định" cho các dòng không có province_id
UPDATE tnbike.fact_sales
SET
    province_name = 'Chưa xác định',
    region = 'Chưa xác định'
WHERE province_id IS NULL;

-- ============================================================
-- 7. THÊM FK fact_sales -> province_clean
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_fact_sales_province_clean'
          AND conrelid = 'tnbike.fact_sales'::regclass
    ) THEN
        ALTER TABLE tnbike.fact_sales
        ADD CONSTRAINT fk_fact_sales_province_clean
        FOREIGN KEY (province_id)
        REFERENCES tnbike.province_clean(province_id);
    END IF;
END $$;

COMMIT;
