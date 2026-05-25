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

-- BƯỚC 4: SỬA LỖI MÀU SẮC CHO DÂN THƯỜNG (HP, BLACKPINK, BATMAN, ADJECTIVES)
UPDATE tnbike.product
SET color = CASE
    -- Trích xuất màu đúng từ tên sản phẩm đối với các dòng lỗi HP
    WHEN product_name ILIKE '%đen%' THEN 'Đen'
    WHEN product_name ILIKE '%trắng%' THEN 'Trắng'
    WHEN product_name ILIKE '%xanh da trời%' THEN 'Xanh Dương'
    WHEN product_name ILIKE '%xanh%' THEN 'Xanh'
    WHEN product_name ILIKE '%đỏ%' THEN 'Đỏ'
    WHEN product_name ILIKE '%ghi%' THEN 'Ghi'
    WHEN product_name ILIKE '%café/nâu%' THEN 'Café/Nâu'
    WHEN product_name ILIKE '%cà phê%' THEN 'Café/Nâu'
    WHEN product_name ILIKE '%hồng%' THEN 'Hồng'
    WHEN product_name ILIKE '%tím%' THEN 'Tím'
    WHEN product_name ILIKE '%vàng cánh gián%' THEN 'Nâu'
    WHEN product_name ILIKE '%vàng%' THEN 'Vàng'
    -- Đổi Blackpink sang Đen/Hồng cho chuẩn ý nghĩa màu sắc
    WHEN color = 'Blackpink' THEN 'Đen/Hồng'
    -- Các mã model xe không thể trích xuất màu sắc từ tên
    WHEN color IN ('05-26', '219-05-26', '05-27', '16-04') THEN 'Chưa xác định'
    ELSE color
END
WHERE color IN ('05-26', '219-05-26', '05-27', '16-04', 'Bat Man', 'Blackpink', 'Hp', 'Superman', 'Wonderwoman', 'Bóng', 'Đậm', 'Gián', 'Mờ', 'Quang', 'Trời');

-- BƯỚC 5: ĐỒNG BỘ TOÀN BỘ DỮ LIỆU ĐÃ LÀM SẠCH SANG BẢNG FACT_SALES
UPDATE tnbike.fact_sales AS fs
SET product_name = p.product_name,
    color = p.color,
    unit = p.unit
FROM tnbike.product AS p
WHERE fs.product_code = p.product_code;

COMMIT;

-- KIỂM TRA LẠI KẾT QUẢ ĐÃ LÀM SẠCH
SELECT color, COUNT(*) as so_dong
FROM tnbike.fact_sales
GROUP BY color
ORDER BY so_dong DESC;
