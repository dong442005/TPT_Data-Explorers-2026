# 🔍 Review: 10 Raw CSV Files vs Plan Hiện tại

> **Mục tiêu**: Đối chiếu 10 file CSV mới từ PostgreSQL với toàn bộ kế hoạch từ Phase 0 đến Phase 1B, tìm ra những gì cần điều chỉnh trước khi tiếp tục Phase 2+.

---

## 📦 Inventory 10 Files Mới

| # | File | Rows | Cols | Mô tả |
|---|---|---:|---:|---|
| 1 | `customer.csv` | 798 | 9 | Danh sách đại lý — **có cột `customer_tier`** 🆕 |
| 2 | `email_log.csv` | — | — | Log quét email |
| 3 | `fact_sales.csv` | 25,754 | **25** | Giao dịch — **có cột `base_color`** 🆕 (trước đó chỉ biết 24 cột) |
| 4 | `order_line.csv` | 25,754 | 8 | Chi tiết dòng đơn hàng |
| 5 | `product.csv` | 265 | 8 | Danh mục sản phẩm — **55 SKU NULL `line_id`** ⚠️ |
| 6 | `product_group.csv` | 5 | 4 | 5 nhóm SP — có cột `description` |
| 7 | `product_line.csv` | 77 | 4 | 77 dòng SP — mapping `line_id → group_code` |
| 8 | `product_price.csv` | 1,016 | 6 | **Bảng giá theo ngày** — 247 SKU, 196 SKU có nhiều mức giá 🚨 |
| 9 | `province_clean.csv` | 75 | 9 | Mapping tỉnh đã chuẩn hóa — 39 tỉnh sạch, 3 vùng miền |
| 10 | `sales_order.csv` | 2,759 | 13 | Đơn hàng — có `invoice_symbol`, `invoice_number` |

---

## 🚨 Phát hiện #1: `product_price.csv` — Bảng giá KHÔNG phải giá niêm yết cố định

Đây là phát hiện quan trọng nhất, vì nó **giải đáp triệt để** câu hỏi "tại sao unit_price dao động lớn".

### Thực trạng
- **1,016 bản ghi giá** cho 247 SKU → trung bình **~4 mức giá/SKU**
- 196/247 SKU có **nhiều hơn 1 mức giá**
- SKU dao động nhiều nhất: **13 mức giá khác nhau** (ví dụ SKU `331002008000`: từ 1,250,000đ đến 2,768,519đ)
- **Tất cả `effective_to` = NaN** → Schema thiết kế cho giá theo thời kỳ nhưng chưa implement end-date
- Mỗi `effective_from` thực chất là **ngày giao dịch** → đây là **giá trên hóa đơn** (invoice price), không phải giá niêm yết

### So sánh product_price vs fact_sales.unit_price
| Chỉ số | Giá trị |
|---|---|
| Giao dịch khớp được với product_price | 20,391 / 25,754 |
| GD mà unit_price == list_price (sai lệch < 0.1%) | **4,353** (21%) |
| GD mà unit_price ≠ list_price | **16,038** (79%) |
| Trung bình sai lệch | -4.5% (thực tế thường THẤP hơn bảng giá) |
| Sai lệch max | -72.9% đến +268.5% |

### Kết luận
> `unit_price` trong fact_sales và product_price đều là **giá trên hóa đơn** (đã bao gồm phí phân bổ, VAT, chiết khấu). Bảng `product_price` KHÔNG chứa giá niêm yết (list price) gốc thuần túy.

### Impact lên Plan
- ❌ **Cần bỏ ý định dùng `product_price` làm "giá chuẩn"** để so sánh với giá giao dịch
- ✅ Vẫn dùng được `median_unit_price` ở mức tháng trong `fact_sales_monthly.parquet` như khuyến nghị trước đó
- ✅ Có thể dùng `product_price` để tính **price volatility** (biến động giá) — feature hữu ích cho model

---

## 🚨 Phát hiện #2: `customer.csv` — Cột `customer_tier` mới

### Thực trạng
- 798 đại lý, có cột **`customer_tier`** mà trước đó chưa biết
- Có thêm: `tax_code`, `address`, `province_id`, `is_active`

### Impact lên Plan
- 🔴 **Track 3 (Dealer Analysis)**: Cần tích hợp `customer_tier` vào phân tích RFM. Hiện tại RFM 8 segments dùng manual thresholds mà chưa cross-reference với tier chính thức từ DB
- 🔴 **Feature Engineering**: `customer_tier` có thể dùng làm feature cho dealer-level features (ví dụ: `n_premium_dealers`, `premium_dealer_share`)
- ⚠️ Cần kiểm tra: `customer_tier` có bao nhiêu giá trị (STANDARD, PREMIUM, VIP...)?

---

## ⚠️ Phát hiện #3: Unmapped SKUs — 55 vs 90

### Thực trạng
- `product.csv` cho thấy **55 SKU có `line_id` = NaN** (chưa được gán dòng sản phẩm)
- Nhưng Phase 1B báo cáo **90 SKU bị NULL `group_code/line_name/group_name`** trong `fact_sales`

### Giải thích
- Bảng `fact_sales` là kết quả JOIN giữa `product → product_line → product_group`
- Nếu `product.line_id` = NaN → JOIN thất bại → `line_name`, `group_code`, `group_name` đều thành NULL
- Con số 90 trong fact_sales có thể bao gồm cả các SKU mà `line_id` có giá trị nhưng trỏ đến `product_line` record không tồn tại
- **Số gốc chính xác là 55 SKU unmapped** tại tầng product

### Impact lên Plan
- ✅ Có thể **mapping thủ công** 55 SKU này dựa vào `product_name` và `color` (tên xe thường chứa tên dòng)
- ✅ File `product_line.csv` (77 dòng) cung cấp mapping `line_id → line_name → group_code` đầy đủ để fix

---

## 🆕 Phát hiện #4: Cột `base_color` trong fact_sales

### Thực trạng
- `fact_sales.csv` có **25 cột** (trước đó khi query từ DB chỉ lấy 24 cột — thiếu `base_color`)
- `base_color` là **màu đã chuẩn hóa** (ví dụ: "Xanh Dương", "Đỏ", "Nâu") thay vì màu gốc chi tiết ("Coban", "Đỏ Tươi", "Café/Nâu")

### Impact lên Plan
- ✅ **Track 2 (Color/Group Forecast)**: Dùng `base_color` thay vì `color` để aggregate, giảm cardinality
- ✅ Feature Engineering: `base_color` có thể dùng cho Target Encoding ở mức màu

---

## 🆕 Phát hiện #5: `province_clean.csv` — Data Quality đã được xử lý

### Thực trạng
- 75 bản ghi mapping, 39 tỉnh sạch, 3 vùng miền (Bắc/Trung/Nam)
- Các loại mapping đã xử lý:
  | Loại | Số lượng | Ví dụ |
  |---|---|---|
  | `keep` (giữ nguyên) | 35 | Hà Nội → Hà Nội |
  | `district_to_province` | 16 | Chí Linh → Hải Dương |
  | `address_to_province` | 11 | "Cường Tráng - An Thịnh - Lương Tài - Bắc Ninh" → Bắc Ninh |
  | `normalize_text` | 9 | Chuẩn hóa dấu/chính tả |
  | `fix_typo` | 4 | Sửa lỗi đánh máy |

### Impact lên Plan
- ✅ **Nên dùng `province_name_clean` và `region_clean`** thay vì `province_name` và `region` từ fact_sales cho các feature regional
- ⚠️ Cần check: fact_sales.province_id có match 100% với province_clean.province_id không?

---

## 🆕 Phát hiện #6: `sales_order.csv` — Thông tin Hóa đơn

### Thực trạng
- 2,759 đơn hàng
- Có `invoice_symbol` và `invoice_number` trên **100%** đơn hàng
- Có `total_amount`, `total_quantity`, `line_count` per order

### Impact lên Plan
- ✅ **Component A (ETL Pipeline — 25% điểm thi)**: Có thể dùng để validate kết quả extract từ PDF
- ✅ Feature Engineering: `line_count` (số dòng sản phẩm trong đơn) có thể biến thành feature `avg_items_per_order` — phản ánh mức độ đa dạng đặt hàng của đại lý

---

## 🔄 Tổng hợp: Những gì CẦN XEM LẠI trước Phase 2

### 🔴 BẮT BUỘC SỬA (Blockers)

| # | Vấn đề | Hành động |
|---|---|---|
| 1 | **55 Unmapped SKUs** cần mapping vào product_line/group | Viết script mapping dựa trên `product_name` pattern → gán `line_id`, `group_code` |
| 2 | **`base_color` bị thiếu** trong `build_phase1b.py` query | Thêm `base_color` vào monthly/weekly aggregation |
| 3 | **`customer_tier` chưa được tích hợp** | Merge `customer_tier` vào fact_sales trước khi aggregate |

### 🟡 NÊN SỬA (Cải thiện chất lượng)

| # | Vấn đề | Hành động |
|---|---|---|
| 4 | Province dùng raw thay vì clean | Dùng `province_clean.csv` để replace `province_name`/`region` trong pipeline |
| 5 | RFM segments chưa cross-reference `customer_tier` | Phân tích overlap giữa 8 RFM segments và customer_tier |
| 6 | Price feature dùng `avg_unit_price` | Đổi sang `median_unit_price` hoặc `implied_price = revenue/quantity` |

### 🟢 BỔ SUNG (Features mới từ data mới)

| # | Feature mới | Nguồn |
|---|---|---|
| 7 | `price_volatility` — biến động giá theo SKU | `product_price.csv` |
| 8 | `avg_items_per_order` — trung bình dòng/đơn | `sales_order.line_count` |
| 9 | `base_color` aggregation cho Track 2 | `fact_sales.base_color` |
| 10 | `customer_tier` features | `customer.customer_tier` |

### ✅ KHÔNG CẦN SỬA (Vẫn đúng)

- Block A/B structure và gap rule → Vẫn đúng
- Phase 1B aggregation numbers (925 monthly, 2642 weekly) → Quantity/Revenue khớp 100%
- RFM 8 segments logic → Vẫn hợp lệ (bổ sung tier, không thay thế)
- Modeling strategy (Group-Share Proportional + LightGBM) → Vẫn đúng
- Leakage prevention rules → Vẫn đúng

---

## ❓ Câu hỏi mở cần quyết định

1. **`customer_tier` có bao nhiêu giá trị?** Nếu chỉ có 1 giá trị (STANDARD) thì không có giá trị phân loại. Cần kiểm tra.
2. **55 unmapped SKUs có nên mapping thủ công không?** Hay gán tất cả vào nhóm "UNMAPPED" rồi để model tự học?
3. **Có nên rebuild Phase 1B** (chạy lại `build_phase1b.py` với `base_color` + `customer_tier` + `province_clean`) hay chỉ bổ sung ở Phase 2?
4. **Pipeline nên chạy từ CSV hay PostgreSQL?** Bây giờ đã có đủ 10 file CSV, pipeline có thể hoàn toàn portable mà không cần kết nối DB.
