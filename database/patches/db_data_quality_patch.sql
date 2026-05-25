-- ====================================================================
-- SCRIPT: db_data_quality_patch.sql
-- MỤC TIÊU: Làm sạch toàn diện lỗi chất lượng dữ liệu của Database TNBike
--          trước khi kết nối với Power BI.
-- VẤN ĐỀ XỬ LÝ:
--   1. Chuẩn hóa chữ hoa/thường cột color (đen/Đen -> Đen).
--   2. Sửa lỗi font của 18 dòng sản phẩm mới do pdfplumber trích xuất lỗi.
--   3. Sửa lỗi nhầm màu sắc (BLACKPINK, Batman, Wonderwoman, HP,...)
--   4. Gộp các tính từ đơn độc thành màu chuẩn (Mờ, Bóng, Trời -> Đen, Xanh Dương,...).
--   5. Đồng bộ toàn bộ dữ liệu làm sạch sang bảng fact_sales.
-- ====================================================================

-- BƯỚC 1: ĐẶT SCHEMA HOẠT ĐỘNG
SET search_path TO tnbike, public;

BEGIN;

-- BƯỚC 1b: THÊM CỘT MÀU CƠ BẢN (BASE_COLOR) NẾU CHƯA CÓ
ALTER TABLE tnbike.product ADD COLUMN IF NOT EXISTS base_color VARCHAR(60);
ALTER TABLE tnbike.fact_sales ADD COLUMN IF NOT EXISTS base_color VARCHAR(60);

-- BƯỚC 2: CHUẨN HÓA VIẾT HOA CHỮ ĐẦU CHO TOÀN BỘ MÀU SẮC ĐANG CÓ
UPDATE tnbike.product
SET color = INITCAP(LOWER(color))
WHERE color IS NOT NULL;

-- BƯỚC 3: SỬA LỖI MÀU SẮC & LỖI FONT CỦA 18 SẢN PHẨM MỚI (TỪ EMAIL THÁNG 3)
UPDATE tnbike.product
SET product_name = CASE product_code
    WHEN '1010130010100000' THEN 'Xe đạp Thống Nhất REX Xanh ngọc'
    WHEN '000219002001000'  THEN 'Xe đạp Thống Nhất GN 2.0 700C đen'
    WHEN '000218003022001'  THEN 'Xe đạp Thống Nhất GN 06-27 2.0 Pro Shimano'
    WHEN '1000400050040003' THEN 'Xe đạp Thống Nhất MTB SPD 27.5 17 đỏ DA'
    WHEN '000225002004003'  THEN 'Xe đạp Thống Nhất New 26 đỏ DA Acrylic'
    WHEN 'TP0099.0000570'   THEN 'Xe đạp Thống Nhất Unite 26'
    WHEN 'TP0099.0000571'   THEN 'Xe đạp Thống Nhất Unite 27.5'
    WHEN '156.01.12.0003'   THEN 'Xe đạp Thống Nhất Unite 20'
    WHEN 'TP0022.02.16.00'  THEN 'Xe đạp Thống Nhất TE 16-02'
    WHEN '1010020000220000' THEN 'Xe đạp Thống Nhất GRX AT 27.5 2.0 15 Xanh'
    WHEN '000306002022000'  THEN 'Xe đạp Thống Nhất MTB 20-05 S xanh'
    WHEN 'TP0099.0000567'   THEN 'Xe đạp Thống Nhất SLX 26-01'
    WHEN 'TP0023.02.25.00'  THEN 'Xe đạp Thống Nhất Nam'
    WHEN 'TP0017.06.27.04'  THEN 'Xe đạp Thống Nhất The Flash 27-01'
    WHEN 'TP0099.0000568'   THEN 'Xe đạp Thống Nhất SLX 27.5-01'
    WHEN 'TP0022.03.16.00'  THEN 'Xe đạp Thống Nhất TE 16-03'
    WHEN '000216002022009'  THEN 'Xe đạp Thống Nhất GN 06 24 D xanh DA Báo'
    WHEN 'TP0016.05.24.01'  THEN 'Xe đạp Thống Nhất GN 05-24'
    ELSE product_name
END,
color = CASE product_code
    WHEN '1010130010100000' THEN 'Xanh Ngọc'
    WHEN '000219002001000'  THEN 'Đen'
    WHEN '000218003022001'  THEN 'Xanh'
    WHEN '1000400050040003' THEN 'Đỏ'
    WHEN '000225002004003'  THEN 'Đỏ'
    WHEN '1010020000220000' THEN 'Xanh'
    WHEN '000306002022000'  THEN 'Xanh'
    WHEN '000216002022009'  THEN 'Xanh'
    ELSE color
END,
unit = 'Chiếc'
WHERE product_code IN (
    '1010130010100000', '000219002001000', '000218003022001', '1000400050040003',
    '000225002004003', 'TP0099.0000570', 'TP0099.0000571', '156.01.12.0003',
    'TP0022.02.16.00', '1010020000220000', '000306002022000', 'TP0099.0000567',
    'TP0023.02.25.00', 'TP0017.06.27.04', 'TP0099.0000568', 'TP0022.03.16.00',
    '000216002022009', 'TP0016.05.24.01'
);

-- BƯỚC 4: SỬA LỖI MÀU SẮC CHO CÁC SKU BỊ LỖI (MÃ XE, TÊN NHÂN VẬT, MÔ TẢ CHẤT LIỆU, MÀU TEM)
UPDATE tnbike.product
SET color = CASE product_code
    -- 1. Mã model xe (không có màu trong tên)
    WHEN '000214004000000' THEN 'Chưa xác định' -- GN 05-26
    WHEN '000207004000000' THEN 'Chưa xác định' -- 219-05-26
    WHEN '000215004000000' THEN 'Chưa xác định' -- GN 05-27
    WHEN '000114002000000' THEN 'Chưa xác định' -- TE 16-04

    -- 2. Tên nhân vật / BLACKPINK
    WHEN '000132002001001' THEN 'Đen'         -- GN 2.0 20 đen - Bat man
    WHEN '000218004009001' THEN 'Đen/Hồng'    -- GN 06-27 2.0 Pro BLACKPINK
    WHEN '000132002022001' THEN 'Xanh'        -- GN 2.0 20 xanh - Superman
    WHEN '000132002003001' THEN 'Đỏ'          -- GN 2.0 20 đỏ - Wonderwoman

    -- 3. Thương hiệu HP
    WHEN '000225002002001' THEN 'Trắng'       -- New 26 Trắng DA HP
    WHEN '000225002007001' THEN 'Xanh'        -- New 26 Xanh DA HP
    WHEN '000225002004001' THEN 'Đỏ'          -- New 26 màu đỏ DA HP
    WHEN '000225002015001' THEN 'Café/Nâu'    -- New 26 Café/nâu DA HP
    WHEN '000333002001003' THEN 'Đen'         -- Super 26 S đen DA HP
    WHEN '000333002022003' THEN 'Xanh'        -- Super 26 S xanh DA HP
    WHEN '000333002008003' THEN 'Ghi'         -- Super 26 S ghi DA HP

    -- 4. Tính từ đơn độc / Trạng thái màu sắc
    WHEN '000413002001000' THEN 'Đen'         -- Highway 27.5 Đen bóng
    WHEN '000324000180000' THEN 'Đen'         -- MTB 26-05_2023 Đen mờ
    WHEN '000413002018000' THEN 'Đen'         -- Highway 27.5 Đen mờ
    WHEN '000122002009001' THEN 'Hồng'        -- Bubbles 20 Hồng dạ quang
    WHEN '000122002024000' THEN 'Tím'         -- Bubbles 20 Tím dạ quang
    WHEN '000406002004000' THEN 'Đỏ'          -- nam 0209 đỏ đậm
    WHEN '000407002019000' THEN 'Nâu'         -- nữ 0209 Base vàng cánh gián
    -- Các trường hợp 'trời' -> Xanh Dương
    WHEN '000314002020000' THEN 'Xanh Dương'   -- MTB 24-04 Tem Xanh da trời
    WHEN '1000300050200000' THEN 'Xanh Dương'  -- MTB SPD 27.5 (xanh da trời)
    WHEN '1000310050200000' THEN 'Xanh Dương'  -- Road RPD 700C Xanh da trời
    WHEN '000304002020000' THEN 'Xanh Dương'   -- MTB 20-04 Tem Xanh da trời
    WHEN '1000320050200000' THEN 'Xanh Dương'  -- Road RPD 700C V5 Xanh da trời
    WHEN '000104002020000' THEN 'Xanh Dương'   -- Tom & Jerry 14 Xanh da trời
    WHEN '000303002020000' THEN 'Xanh Dương'   -- MTB 20-03 Tem Xanh da trời

    -- 5. Lỗi màu tem lấn át hoặc chứa chữ Tem
    WHEN '000231003005001' THEN 'Đen'         -- M2601 Shimano Đen (tem cam)
    WHEN '000231003002001' THEN 'Trắng'       -- M2601 Shimano Trắng (tem tím)
    WHEN '000231003022001' THEN 'Xanh'        -- M2601 Shimano Xanh (tem trắng)
    WHEN '000231003023001' THEN 'Đen'         -- M2601 Shimano Đen (tem xanh)
    WHEN '000231003023000' THEN 'Đen'         -- M2601 Đen Tem Xanh
    WHEN '000231003005000' THEN 'Đen'         -- M2601 Đen Tem cam
    -- Các trường hợp khác chỉ có 'Tem cam', 'Tem đỏ' thì chuẩn hóa thành màu chính
    WHEN '000314002005000' THEN 'Cam'         -- MTB 24-04 Tem cam
    WHEN '000304002004000' THEN 'Đỏ'          -- MTB 20-04 Tem đỏ
    WHEN '000329002005000' THEN 'Cam'         -- MTB 26-07 Tem cam
    WHEN '000329002004001' THEN 'Đỏ'          -- MTB 26-07 Tem đỏ
    WHEN '000303002005000' THEN 'Cam'         -- MTB 20-03 Tem cam
    WHEN '000303002004000' THEN 'Đỏ'          -- MTB 20-03 Tem đỏ
    WHEN '000304002005000' THEN 'Cam'         -- MTB 20-04 Tem cam
    ELSE color
END
WHERE product_code IN (
    '000214004000000', '000207004000000', '000215004000000', '000114002000000',
    '000132002001001', '000218004009001', '000132002022001', '000132002003001',
    '000225002002001', '000225002007001', '000225002004001', '000225002015001',
    '000333002001003', '000333002022003', '000333002008003', '000413002001000',
    '000324000180000', '000413002018000', '000122002009001', '000122002024000',
    '000406002004000', '000407002019000', '000314002020000', '1000300050200000',
    '1000310050200000', '000304002020000', '1000320050200000', '000104002020000',
    '000303002020000', '000231003005001', '000231003002001', '000231003022001',
    '000231003023001', '000231003023000', '000231003005000', '000314002005000',
    '000304002004000', '000329002005000', '000329002004001', '000303002005000',
    '000303002004000', '000304002005000'
);

-- BƯỚC 4b: ĐIỀN CỘT MÀU CƠ BẢN (BASE_COLOR) DỰA TRÊN MÀU CHI TIẾT (COLOR)
UPDATE tnbike.product
SET base_color = CASE
    WHEN color IN ('Đen') THEN 'Đen'
    WHEN color IN ('Đen/Hồng') THEN 'Đen/Hồng'
    WHEN color IN ('Đỏ', 'Đỏ Đun', 'Đỏ Tươi') THEN 'Đỏ'
    WHEN color IN ('Xanh Dương', 'Coban', 'Xanh Santorini', 'Xanh Nước Biển', 'Pastel Xanh') THEN 'Xanh Dương'
    WHEN color IN ('Xanh Lá', 'Rêu') THEN 'Xanh Lá'
    WHEN color IN ('Xanh Ngọc', 'Ngọc', 'Xanh Mint', 'Mint') THEN 'Xanh Ngọc/Mint'
    WHEN color IN ('Xanh', 'Xanh Tím') THEN 'Xanh'
    WHEN color IN ('Ghi') THEN 'Ghi'
    WHEN color IN ('Hồng') THEN 'Hồng'
    WHEN color IN ('Vàng', 'Chanh') THEN 'Vàng'
    WHEN color IN ('Cam') THEN 'Cam'
    WHEN color IN ('Trắng') THEN 'Trắng'
    WHEN color IN ('Nâu', 'Café/Nâu') THEN 'Nâu'
    WHEN color IN ('Kem') THEN 'Kem'
    WHEN color IN ('Be') THEN 'Be'
    WHEN color = 'Chưa xác định' THEN 'Chưa xác định'
    ELSE color
END;

-- BƯỚC 5: ĐỒNG BỘ TOÀN BỘ DỮ LIỆU ĐÃ LÀM SẠCH SANG BẢNG FACT_SALES
UPDATE tnbike.fact_sales AS fs
SET product_name = p.product_name,
    color = p.color,
    base_color = p.base_color
FROM tnbike.product AS p
WHERE fs.product_code = p.product_code;

COMMIT;

-- KIỂM TRA LẠI KẾT QUẢ ĐÃ LÀM SẠCH
SELECT color, COUNT(*) as so_dong
FROM tnbike.fact_sales
GROUP BY color
ORDER BY so_dong DESC;
