# Báo Cáo Chuyên Sâu: Phương Pháp Luận Xử Lý Dữ Liệu (Data Processing Methodology)

Báo cáo này tổng hợp toàn bộ hiện trạng dữ liệu thô (Raw Data) mà đội thi tiếp nhận, cùng với các kỹ thuật và quyết định xử lý dữ liệu (Data Engineering) được áp dụng xuyên suốt từ tầng Python (ETL) đến tầng Cơ sở dữ liệu (PostgreSQL) và Power BI.

---

## 1. TÌNH TRẠNG DỮ LIỆU THÔ (THE RAW DATA CONDITION)

Qua quá trình trích xuất và phân tích (EDA), hệ thống dữ liệu gốc của doanh nghiệp bộc lộ 4 nhóm vấn đề nghiêm trọng, đe dọa trực tiếp đến tính chính xác của các mô hình dự báo và báo cáo quản trị:

1.  **Nhiễu cấu trúc phi cấu trúc (Unstructured Noise):** Dữ liệu hóa đơn đến từ các file PDF/Email bị lỗi font chữ nghiêm trọng khi parse (ví dụ: chữ *Xe đạp Thống Nhất* bị biến dạng thành *xennpthnngnhnt*, *xenngthnngnhnt*).
2.  **Mất đồng bộ phân loại sản phẩm (SKU Misclassification):** Ghi nhận 90 mã sản phẩm (chiếm 23% tổng doanh thu) hoàn toàn không có thông tin nhóm xe (`line_id`), biến chúng thành "điểm mù" trong ma trận sản phẩm.
3.  **Dữ liệu rác về màu sắc (Color Noise):** Trường màu sắc bị gõ tùy tiện (đen/Đen), bị dính liền với tên nhân vật bản quyền (Batman, Wonderwoman, BLACKPINK) hoặc thương hiệu (HP), gây ra sự phân mảnh giả tạo về biến thể sản phẩm (Variants).
4.  **Khuyết thiếu dữ liệu địa lý (Missing Geolocation):** Nhiều khách hàng không được nhập Tỉnh/Thành phố (`province_id` = NULL), địa danh bị gõ sai chính tả (Hà Nộ, Thanh Hoá) hoặc bị gán nhầm cấp Huyện lên Tỉnh (Hạ Long, Uông Bí).

---

## 2. KỸ THUẬT XỬ LÝ TẠI TẦNG PYTHON (ETL PIPELINE)

Tại lớp ứng dụng Python, dữ liệu được trích xuất và biến đổi trước khi nạp vào kho dữ liệu.

### 2.1. Trích xuất thông minh (Smart Extraction - `extract_validate.py`)
*   **Kỹ thuật:** Sử dụng thư viện `pdfplumber` kết hợp với Biểu thức chính quy nâng cao (Advanced RegEx).
*   **Xử lý:** 
    *   Bóc tách song song cả nội dung Email (để lấy số điện thoại, MST, ngày tháng) và bảng biểu trong file đính kèm PDF (để lấy từng dòng sản phẩm, đơn giá).
    *   **Cơ chế Validation/Audit:** Script tự động đối chiếu chéo (Cross-validation) giữa Tổng tiền tính toán từ các dòng (Calc Total), Tổng tiền ghi trên PDF (PDF Total) và Tổng tiền trên Email. Nếu độ lệch > 10 VNĐ, hệ thống kích hoạt cờ cảnh báo (Warning flag) thay vì sập toàn bộ luồng.

### 2.2. Xử lý ngôn ngữ tự nhiên cơ bản (Text Normalization - `normalize.py`)
*   **Kỹ thuật:** Flatten JSON, String Cleansing và Dynamic DB Mapping.
*   **Xử lý:**
    *   **Lọc nhiễu:** Xây dựng danh sách "từ vựng nhiễu" do lỗi PDF (vd: `xennpthnngnhnt`) và loại bỏ hoàn toàn chúng khỏi chuỗi văn bản bằng vòng lặp thay thế.
    *   **Ánh xạ động (Dynamic Mapping):** Thay vì hard-code danh mục, script kết nối trực tiếp vào PostgreSQL để kéo danh mục `product_line` mới nhất. Sau đó dùng thuật toán so khớp chuỗi (Sub-string matching) để tự động điền `line_id` cho các sản phẩm dựa trên tên.

---

## 3. KỸ THUẬT XỬ LÝ TẠI TẦNG CƠ SỞ DỮ LIỆU (SQL PATCHES)

Thay vì dùng Python Pandas xử lý toàn bộ, các logic làm sạch dữ liệu lớn được đẩy xuống tầng Database (ELT) thông qua các bản vá (Patches) để tận dụng sức mạnh tính toán của PostgreSQL.

### 3.1. Vá lỗi Chất lượng Dữ liệu Sản phẩm (`db_data_quality_patch.sql`)
*   **Kỹ thuật:** Data Imputation thông qua `CASE WHEN` và `ILIKE`.
*   **Xử lý:**
    *   **Chuẩn hóa String:** Dùng hàm `INITCAP(LOWER(color))` để đồng bộ chữ hoa/thường cho hàng ngàn dòng dữ liệu trong 1 milisecond.
    *   **Feature Engineering (Màu cơ bản):** Phân tích ngữ nghĩa để gộp các màu nhiễu vào chung một phân loại gốc (`base_color`). Ví dụ: các màu *Xanh Santorini, Coban, Xanh Nước Biển, Trời* đều được ép về *Xanh Dương*.
    *   **Pattern Matching:** Dùng hàm `ILIKE '%...%'` để quét chuỗi tên xe, nhận diện các keyword cốt lõi (vd: *Super Man 16*, *Bubbles 20*) và khôi phục thành công `line_id` cho 90 SKU mồ côi.

### 3.2. Chữa lành Dữ liệu Địa lý (`geo_clean_patch_final.sql`)
*   **Kỹ thuật:** Text Pattern Searching (`STRPOS`, `ILIKE`) và thiết kế bảo toàn dữ liệu (Non-destructive Design).
*   **Xử lý:**
    *   **Bảo vệ Dữ liệu gốc:** Không thực hiện lệnh `UPDATE/DELETE` trực tiếp lên bảng Tỉnh thành gốc. Thay vào đó, tạo một bảng trung gian `province_correction_map` chứa bộ từ điển map (ví dụ: gán *Hội An* thuộc về *Quảng Nam*).
    *   **Data Recovery (Cứu dữ liệu NULL):** Đối với các khách hàng bị thiếu `province_id`, script sử dụng kỹ thuật *Sub-string Position Matching* (`STRPOS`) để dò tìm tên Tỉnh bị kẹp ẩn bên trong chuỗi địa chỉ thô dài thòng của khách hàng, lấy vị trí khớp sâu nhất (để tránh nhầm lẫn) và gán ngược lại ID. Bẻ khóa ngoại (FK) trỏ sang bảng sạch.

---

## 4. KỸ THUẬT XỬ LÝ TẠI TẦNG BI / ANALYTICS

Lớp cuối cùng bảo vệ tính đúng đắn của dữ liệu trước khi trình bày cho Ban Giám Đốc.

*   **Xử lý Outlier (Ngoại lai):** Trong ma trận BCG, việc sử dụng hàm `AVERAGE` sẽ bị bóp méo bởi các dòng xe bán quá khủng (như Xe New 26). Đội thi đã áp dụng hàm `PERCENTILE_CONT(0.5)` (Trung vị - Median) trong DAX để thiết lập trục tọa độ, giúp phân loại danh mục đầu tư chính xác hơn.
*   **Phân khúc hóa B2B (RFM Customization):** Can thiệp bằng tay vào logic phân chia Quartile của mô hình RFM, thiết lập điểm trần (Threshold) phù hợp với chu kỳ mua sỉ của doanh nghiệp (tạo ra nhóm *Big Spender* chuyên mua ít nhưng giá trị cao).

> [!TIP]
> **Tóm tắt:** Bằng việc phân lớp xử lý nhiều tầng (Python lo cấu trúc JSON/Nhiễu font -> SQL lo liên kết quan hệ và làm sạch diện rộng -> BI lo Outlier), đội thi đã thiết lập được một Data Pipeline cực kỳ vững chắc, không chỉ dọn rác mà còn khôi phục 100% dòng chảy dữ liệu lên Dashboard.
