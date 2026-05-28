# Business & Data Domain Specification
## Thống Nhất Bike — B2B Bicycle Distribution Analytics Platform
### Data Explorers 2026 | Internal Technical Document v1.0

---

## 1. Executive Summary

Thống Nhất Bike (TNBike) là nhà sản xuất và phân phối xe đạp B2B hoạt động trên toàn lãnh thổ Việt Nam thông qua mạng lưới **702 đại lý** phân bổ tại **63 tỉnh thành**. Danh mục sản phẩm bao gồm **247 SKU** thuộc **5 nhóm sản phẩm chính**, từ xe phổ thông cho người lớn đến xe trẻ em có bản quyền IP quốc tế (Batman, Superman, Powerpuff Girls).

**Phạm vi dữ liệu hiện có:**

| Thuộc tính | Giá trị |
|---|---|
| Giai đoạn | 01/2025 → 02/2026 (14 tháng) |
| Tổng dòng giao dịch | 17,031 rows (`fact_sales`) |
| Đại lý (Customers) | 702 |
| SKU (Products) | 247 |
| Nhóm sản phẩm | 5 groups, ~68 product lines |
| Vùng địa lý | 3 miền (Bắc / Trung / Nam) |
| Database | PostgreSQL 14+ (Schema `tnbike`) |

**Mục tiêu cuộc thi:**
1. Pipeline tự động xử lý đơn hàng từ email/PDF
2. Dashboard phân tích kinh doanh đa chiều
3. Dự báo nhu cầu (Demand Forecasting) Q2/2026
4. Đề xuất chiến lược kinh doanh dựa trên dữ liệu

> [!IMPORTANT]
> Đây là bài toán **B2B Demand Forecasting** — dự báo đơn đặt hàng của đại lý, KHÔNG phải dự báo nhu cầu người tiêu dùng cuối cùng. Sự phân biệt này chi phối toàn bộ kiến trúc feature engineering, xử lý outlier và lựa chọn mô hình.

---

## 2. Business Model of Thống Nhất Bike

### 2.1 Mô hình Phân phối

```
┌──────────────────┐
│   NHÀ MÁY SẢN   │
│   XUẤT TNBike    │
│ (Manufacturer)   │
└────────┬─────────┘
         │
         │  Bán sỉ (Wholesale)
         │  Đơn vị: Lô / Chiếc
         │  Thanh toán: Công nợ B2B
         ▼
┌──────────────────┐
│  702 ĐẠI LÝ     │
│  (Dealers)       │
│  B2B Customers   │
│  - Cty TNHH      │
│  - Cửa hàng      │
│  - Hộ KD cá thể  │
└────────┬─────────┘
         │
         │  Bán lẻ (Retail)
         │  Không nằm trong database
         ▼
┌──────────────────┐
│ NGƯỜI TIÊU DÙNG  │
│ (End Consumer)   │
│ Không có data    │
└──────────────────┘
```

### 2.2 Đặc điểm Cốt lõi của Mô hình B2B

| Đặc điểm | Ý nghĩa cho Data Team |
|---|---|
| **Đại lý mua theo lô** | Đơn hàng có giá trị lớn nhưng tần suất thưa (lumpy demand). Không smooth như retail |
| **Chiết khấu theo khối lượng** | `unit_price` thay đổi theo lượng mua → Đơn giá trong `order_line` ≠ Giá list trong `product_price` |
| **Hành vi ôm hàng (Forward Buying)** | Đại lý có thể mua trước lượng lớn khi dự kiến tăng giá hoặc chạy KM → Tạo đỉnh ảo (false peak) |
| **Mùa vụ bị lệch pha** | Đại lý đặt hàng TRƯỚC mùa bán lẻ 1-2 tháng (Lead time effect) |
| **Công nợ & Hạn mức tín dụng** | Không có trong DB nhưng có thể ảnh hưởng đến khả năng đặt hàng |
| **Phân tầng đại lý** | Cột `customer_tier` (STANDARD / KEY / VIP) — Ảnh hưởng đến quy mô đơn hàng |

### 2.3 Chuỗi Giá trị (Value Chain)

```
Nguyên liệu → Sản xuất → Thành phẩm → Kho → Phân phối → Đại lý → Người dùng
                                        ↑                    ↑
                                   Dữ liệu tồn kho     Dữ liệu bán hàng
                                   (Không có)           (CÓ - Database)
```

> [!NOTE]
> Database chỉ capture được **một khúc** của chuỗi giá trị: từ kho nhà máy → đại lý. Không có dữ liệu tồn kho (inventory), chi phí sản xuất (COGS), hay doanh số bán lẻ (sell-through) của đại lý.

---

## 3. Sales & Distribution Workflow

### 3.1 Quy trình Đặt hàng Thực tế

```
[1] Đại lý gửi yêu cầu đặt hàng
    (Qua email, điện thoại, hoặc nhân viên kinh doanh)
         │
         ▼
[2] Bộ phận Kinh doanh xác nhận đơn hàng
    → Kiểm tra hàng tồn, giá bán, chính sách chiết khấu
         │
         ▼
[3] Xuất hóa đơn bán hàng (Invoice)
    → Sinh chứng từ: BH25.XXXX / BH26.XXXX
    → Ký hiệu hóa đơn: C25TTN / C26TTN
         │
         ▼
[4] Giao hàng & Xuất kho
         │
         ▼
[5] Ghi nhận vào hệ thống ERP
    → Dữ liệu chảy vào sales_order + order_line
         │
         ▼
[6] Tổng hợp vào bảng phân tích
    → fact_sales (Denormalized flat table)
```

### 3.2 Mapping Workflow → Database Tables

| Bước Workflow | Bảng Database | Ghi chú |
|---|---|---|
| Đại lý đặt hàng | `customer` | Thông tin đại lý, mã số thuế, tỉnh thành |
| Tạo chứng từ bán hàng | `sales_order` | Header: ngày, số chứng từ, tổng tiền |
| Chi tiết dòng hàng hóa | `order_line` | Detail: từng SKU × SL × Đơn giá |
| Ghi nhận sản phẩm | `product` → `product_line` → `product_group` | Hierarchy 3 cấp |
| Phân tích | `fact_sales` | JOIN sẵn mọi chiều, phục vụ BI/ML |
| Lịch sử giá | `product_price` | Giá list theo thời kỳ (effective_from → effective_to) |

---

## 4. Product Hierarchy & Product Semantics

### 4.1 Cấu trúc Phân cấp

```
Product Group (5)          ← Cấp 1: Phân loại kinh doanh
    └── Product Line (~68) ← Cấp 3: Dòng xe (model)
        └── SKU (247)      ← Cấp 4: Mã hàng cụ thể (model + màu sắc)
```

### 4.2 Chi tiết 5 Nhóm Sản phẩm

| Group Code | Tên Nhóm | Mô tả | Đối tượng KH | Phân khúc giá |
|---|---|---|---|---|
| `CITYBIKE_P` | Xe phổ thông | Xe đạp cho người lớn: GN, New, 219, LD, M, MTB 24/26 | Đại chúng, đi lại hàng ngày | Thấp - Trung bình |
| `KIDBIKE_1` | Xe trẻ em nhóm 1 | Bánh 16-20 inch: GN 06 20, MTB 20, Neo, TE 16, Puppy | Trẻ 6-12 tuổi | Trung bình |
| `KIDBIKE_2` | Xe trẻ em nhóm 2 | Bánh 12-16 inch: Bunny, Love, Spaceboy, Robot, IP DC/CN | Trẻ 3-6 tuổi | Trung bình - Cao (IP) |
| `SPORTBIKE_S` | Xe thể thao thép | Khung thép: MTB 24-04, MTB 26-07, Highway, M2601, Super | Thanh thiếu niên, vận động | Trung bình |
| `SPORTBIKE_A` | Xe thể thao nhôm | Khung nhôm cao cấp: MTB SPD 27.5, GRX, Road RPD 700C, Touring | Người chơi thể thao | Cao |

### 4.3 Semantics Quan trọng của Product Code

| Pattern | Ý nghĩa | Ví dụ |
|---|---|---|
| `000XXXXXXX` | Mã ERP truyền thống | `000217003001000` = GN 06-26 2.0 Đen |
| `10XXXXXXXXX` | Mã ERP mới (16 ký tự) | `1000300050010000` = MTB SPD 27.5 Đen |
| Hậu tố `001`, `002` | Biến thể (variant) của cùng model | `000225002002001` = New 26 Trắng DA HP |
| `line_id = NULL` | SKU chưa được map vào danh mục | ~30 SKU bị thiếu mapping |

### 4.4 Đặc điểm Màu sắc

Một dòng xe (product_line) thường có **3-6 biến thể màu sắc**. Phân bổ màu có tính xu hướng thời trang:
- **Màu phổ biến nhất:** Đen, Hồng, Xanh dương, Coban, Cam
- **Màu xu hướng mới:** Xanh mint, Kem, Xanh Santorini, Café/nâu
- **Nhóm IP bản quyền:** Màu cố định theo nhân vật (Batman=Ghi, Superman=Xanh, Powerpuff Girls=Hồng/Tím)

> [!TIP]
> Khi dự báo theo màu sắc, cần hiểu rằng **cùng một model xe, màu khác nhau có demand rất khác nhau**. Ví dụ: New 26 Hồng bán chạy hơn New 26 Coban ở miền Nam nhưng ngược lại ở miền Bắc.

---

## 5. Dealer/Customer Behavior in B2B Model

### 5.1 Phân loại Hành vi Đại lý

| Phân khúc | Đặc điểm | Tần suất đặt hàng | Quy mô đơn |
|---|---|---|---|
| **Heavy Hitters (Top 5%)** | Đại lý lớn, chuỗi cửa hàng | Hàng tháng | 50-200+ chiếc/đơn |
| **Regular (60%)** | Cửa hàng xe đạp trung bình | 2-4 lần/quý | 10-50 chiếc/đơn |
| **Occasional (25%)** | Hộ kinh doanh nhỏ | 1-2 lần/quý | 5-20 chiếc/đơn |
| **Dormant/Churn (10%)** | Không đặt hàng >3 tháng | 0 | 0 |

### 5.2 Hành vi Đặt hàng Đặc thù B2B

```
Hành vi Đại lý trong năm:

T1  T2  T3  T4  T5  T6  T7  T8  T9  T10 T11 T12
 ▓▓  ▓   ░   ░   ▓   ▓▓  ▓▓▓ ▓▓▓ ▓▓  ▓   ░   ▓▓
 │              │       │           │           │
 Tết            Thiếu   Back-to-   Giảm mùa    Cuối năm
 (Quà tặng)    nhi 1/6  school     mưa         Ôm hàng
                        T7-T9
```

### 5.3 Relationship: Dealer ↔ Seasonality ↔ Product ↔ Region

```
                    ┌─────────────────┐
                    │   SEASONALITY   │
                    │  (Mùa vụ)       │
                    └───────┬─────────┘
                            │ Chi phối
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌────────────┐ ┌──────────────┐
    │   DEALER     │ │  PRODUCT   │ │   REGION     │
    │  Behavior    │ │  Demand    │ │  Pattern     │
    └──────┬───────┘ └─────┬──────┘ └──────┬───────┘
           │               │               │
           │  Tương tác    │  Tương tác     │
           └───────┬───────┘               │
                   │                       │
                   └───────────────────────┘
                       Cross-effects

Ví dụ cụ thể:
- Đại lý miền NAM mua xe KIDBIKE_2 (IP) nhiều hơn vào T5-T6 (1/6)
- Đại lý miền BẮC mua xe CITYBIKE_P nhiều vào T8-T9 (Tựu trường)
- Đại lý vùng ngoại thành mua CITYBIKE_P (xe phổ thông) quanh năm
- Đại lý đô thị HCM/HN mua SPORTBIKE_A (xe thể thao nhôm) theo trend
```

---

## 6. Seasonality & Demand Characteristics

### 6.1 Các Driver Mùa vụ Chính

| Mùa | Tháng | Nhóm SP bị ảnh hưởng | Loại ảnh hưởng |
|---|---|---|---|
| **Tết Nguyên Đán** | T1-T2 | KIDBIKE_1, KIDBIKE_2 | Đỉnh quà tặng |
| **Quốc tế Thiếu nhi** | T5-T6 | KIDBIKE_1, KIDBIKE_2 | Đỉnh quà tặng |
| **Tựu trường (Back-to-school)** | T7-T9 | KIDBIKE_1, CITYBIKE_P | Đỉnh vụ lớn nhất |
| **Mùa mưa miền Nam** | T5-T11 | SPORTBIKE_A, SPORTBIKE_S | Sụt giảm (xe thể thao) |
| **Mùa đông miền Bắc** | T11-T1 | Tất cả | Sụt giảm nhẹ |
| **Cuối năm (Year-end)** | T11-T12 | Tất cả | Ôm hàng đại lý cho Tết |

### 6.2 Đặc điểm Chuỗi Thời gian

| Đặc điểm | Mô tả | Hệ quả cho Modeling |
|---|---|---|
| **Lumpy demand** | Đơn hàng B2B không đều, có đỉnh/đáy bất thường | Cần Winsorize thay vì xóa Outlier |
| **Short history** | Chỉ có 14 tháng (01/2025 – 02/2026) | Không đủ data cho `lag_12`; Cần Global Model |
| **Sparse matrix** | SKU × Dealer × Month: hầu hết = 0 | Modeling ở mức SKU×Month, không phải SKU×Dealer×Month |
| **Price sensitivity** | Giá thay đổi → Đại lý đổi hành vi | Price features cần lagged để tránh leakage |
| **Lead-time effect** | Đại lý mua trước mùa 1-2 tháng | Dự báo demand của đại lý ≠ demand của người tiêu dùng |

---

## 7. Revenue Structure & Pricing Logic

### 7.1 Cơ cấu Giá

```
Giá Niêm yết (product_price.unit_price)
    │
    ├── Chiết khấu theo khối lượng
    ├── Chiết khấu theo kênh (KEY/VIP dealer)
    ├── Chương trình khuyến mãi (seasonal promotion)
    │
    ▼
Giá Giao dịch Thực tế (order_line.unit_price)
    │
    × quantity
    │
    ▼
Thành tiền (order_line.line_total)
```

### 7.2 Bảng `product_price` — Lịch sử Giá List

| Cột | Ý nghĩa Business |
|---|---|
| `unit_price` | Giá niêm yết (chưa VAT), đơn vị VND |
| `effective_from` | Ngày bắt đầu áp dụng giá mới |
| `effective_to` | Ngày kết thúc (NULL = đang áp dụng) |

**Insight quan trọng:** 196/247 SKU (79%) có nhiều hơn 1 mức giá lịch sử → Giá thay đổi thường xuyên. Điều này tạo ra cơ hội phân tích **Price Elasticity** (độ co giãn cầu theo giá).

### 7.3 Chênh lệch Giá List vs. Giá Giao dịch

```
Giá giao dịch (order_line.unit_price) thường ≤ Giá list (product_price.unit_price)

Khoảng chênh lệch chính:
- Đại lý VIP: Giảm 5-15% so với giá list
- Đại lý KEY: Giảm 3-8%
- Đại lý STANDARD: Gần sát giá list
- Mua lô lớn (>50 chiếc): Chiết khấu thêm 2-5%
```

> [!WARNING]
> Khi xây dựng feature `price`, PHẢI dùng `order_line.unit_price` (giá giao dịch thực tế), không dùng `product_price.unit_price` (giá niêm yết). Giá niêm yết chỉ nên dùng để phân tích biến động giá chính sách của nhà máy.

---

## 8. Database Architecture Overview

### 8.1 Kiến trúc Tổng quan

```
┌─────────────────────────────────────────────────────────┐
│                    SCHEMA: tnbike                        │
│                                                         │
│  ┌─── DIMENSION TABLES ──────────────────────────────┐ │
│  │                                                    │ │
│  │  product_group ──► product_line ──► product        │ │
│  │       (5)              (~68)          (247)         │ │
│  │                                       │            │ │
│  │  province ──► customer            product_price    │ │
│  │    (63)        (702)              (Lịch sử giá)    │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─── TRANSACTION TABLES ────────────────────────────┐ │
│  │                                                    │ │
│  │  sales_order ──► order_line                        │ │
│  │  (Header)         (Detail)                         │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─── ANALYTICS LAYER ───────────────────────────────┐ │
│  │                                                    │ │
│  │  fact_sales (Denormalized flat table)              │ │
│  │  ├── v_monthly_by_group                           │ │
│  │  ├── v_customer_period                            │ │
│  │  ├── v_sku_monthly                                │ │
│  │  └── v_customer_activity                          │ │
│  │                                                    │ │
│  │  email_log (Pipeline audit trail)                 │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Tính năng Kỹ thuật Đáng chú ý

| Tính năng | Bảng | Chi tiết |
|---|---|---|
| **Generated columns** | `sales_order` | `fiscal_year`, `fiscal_month`, `fiscal_quarter` tự tính từ `order_date` |
| **Trigger auto-update** | `order_line` → `sales_order` | Tự cập nhật `total_amount`, `total_quantity`, `line_count` khi insert/update/delete dòng hàng |
| **Denormalized fact** | `fact_sales` | JOIN sẵn tất cả dimension → Query nhanh, không cần JOIN lúc phân tích |
| **Redundant so_number** | `order_line` | Lưu thừa `so_number` để tránh JOIN khi query |
| **Price history** | `product_price` | `effective_to = NULL` nghĩa là giá đang còn hiệu lực |

---

## 9. Fact Table vs Dimension Tables

### 9.1 Bảng Fact (Giao dịch)

| Bảng | Grain (Độ chi tiết) | Business Role | Use Cases |
|---|---|---|---|
| `fact_sales` | 1 dòng = 1 SKU trong 1 chứng từ | Analytics hub chính | Dashboard, Forecasting, ML, KPI |
| `sales_order` | 1 dòng = 1 chứng từ bán hàng (header) | OLTP header | Tracking đơn hàng, Revenue tổng |
| `order_line` | 1 dòng = 1 SKU × SL × Giá (detail) | OLTP detail | Chi tiết giao dịch, Price analysis |
| `email_log` | 1 dòng = 1 email đã xử lý | Pipeline audit | Monitoring pipeline ETL |

### 9.2 Bảng Dimension (Danh mục)

| Bảng | Cardinality | Type | Business Role | Analytics Use Cases |
|---|---|---|---|---|
| `product_group` | 5 | Slowly Changing | Nhóm SP cấp 1 | Group-level forecasting, Portfolio analysis |
| `product_line` | ~68 | Slowly Changing | Dòng xe (model) | Model-level trend, Product mix analysis |
| `product` | 247 | Slowly Changing | SKU cụ thể | SKU forecasting, Color analysis |
| `product_price` | N (Time-varying) | Type 2 SCD | Lịch sử giá | Price elasticity, Pricing strategy |
| `customer` | 702 | Slowly Changing | Đại lý | RFM, Churn, Segmentation |
| `province` | 63 | Static | Tỉnh thành | Regional analytics, Geo distribution |

### 9.3 Ý nghĩa Business của Từng Bảng

| Bảng | Ý nghĩa Business | Câu hỏi kinh doanh mà bảng này trả lời |
|---|---|---|
| `product_group` | Phân loại danh mục kinh doanh cấp chiến lược | "Nhóm nào đóng góp doanh thu lớn nhất?" |
| `product_line` | Xác định dòng xe — đơn vị quản lý sản phẩm | "Dòng xe nào đang tăng trưởng/suy giảm?" |
| `product` | SKU bán hàng — đơn vị nhỏ nhất quản lý tồn kho | "Sản phẩm nào cần sản xuất thêm/giảm?" |
| `product_price` | Chính sách giá theo thời kỳ | "Đợt tăng giá gần nhất ảnh hưởng demand ra sao?" |
| `customer` | Hồ sơ đại lý — Đối tượng kinh doanh B2B | "Đại lý nào đang giảm hoạt động?" |
| `province` | Phân vùng địa lý | "Vùng nào có tiềm năng tăng trưởng?" |
| `sales_order` | Bằng chứng giao dịch pháp lý (hóa đơn) | "Có bao nhiêu đơn hàng trong tháng?" |
| `order_line` | Chi tiết hàng hóa giao dịch | "Giá bán thực tế cho đại lý X là bao nhiêu?" |
| `fact_sales` | Bảng phẳng phục vụ phân tích nhanh | Tất cả các câu hỏi analytics |

---

## 10. Important Analytical Views

### 10.1 Views Có sẵn

| View | Grain | Mục đích Phân tích | Phục vụ cho |
|---|---|---|---|
| `v_monthly_by_group` | Group × Month | Trend analysis, Seasonality detection | Dashboard, Forecasting (Group-level) |
| `v_customer_period` | Customer × Quarter | RFM, Churn detection, Customer lifetime | CRM, Segmentation |
| `v_sku_monthly` | SKU × Color × Month | Variant trend, Color popularity | SKU Forecasting, Product analysis |
| `v_customer_activity` | Customer (lifetime) | Churn signal, Active/Inactive detection | Sales priority, Re-engagement |

### 10.2 Views Cần Bổ sung

| View đề xuất | Grain | Lý do cần |
|---|---|---|
| `v_sku_monthly_agg` | SKU × Month (no color split) | **Bảng modeling chính cho forecasting** — Cần aggregate thêm `n_dealers`, `n_provinces`, price stats |
| `v_group_monthly_agg` | Group × Month | Middle-out reconciliation |
| `v_dealer_sku_monthly` | Dealer × SKU × Month | Tính Dealer-level features rồi roll-up lên SKU |
| `v_region_monthly` | Region × Month | Regional demand pattern |
| `v_price_change_log` | SKU × Price change event | Phân tích tác động thay đổi giá |

---

## 11. Core Business KPIs

### 11.1 KPIs Cấp Chiến lược (C-Level)

| KPI | Công thức | Tần suất | Target |
|---|---|---|---|
| **Tổng Doanh thu** | `SUM(line_total)` | Monthly | Tăng trưởng MoM > 0% |
| **Tổng Sản lượng** | `SUM(quantity)` | Monthly | Tăng trưởng QoQ > 0% |
| **Doanh thu Trung bình/Đơn** | `SUM(line_total) / COUNT(DISTINCT so_number)` | Monthly | Duy trì hoặc tăng |
| **Tỷ lệ Đại lý Hoạt động** | `COUNT(DISTINCT active_dealers) / COUNT(DISTINCT all_dealers)` | Monthly | > 60% |
| **Tỷ trọng Nhóm SP** | `Revenue_GroupX / Total_Revenue` | Quarterly | Cân bằng danh mục |

### 11.2 KPIs Cấp Vận hành (Operations)

| KPI | Công thức | Insight |
|---|---|---|
| **Số SKU Bán chạy (Active SKUs)** | SKU có `quantity > 0` trong tháng | Breadth of assortment |
| **Số Đại lý Mới** | Đại lý có `first_order_date` trong tháng | Network expansion |
| **Tần suất Đặt hàng TB/Đại lý** | `COUNT(orders) / COUNT(DISTINCT active_dealers)` | Dealer engagement |
| **Sản lượng TB/Đại lý** | `SUM(quantity) / COUNT(DISTINCT active_dealers)` | Dealer productivity |
| **% SKU Zero-Sales** | SKU không có giao dịch trong tháng / Tổng SKU | Dead stock risk |

### 11.3 KPIs Nâng cao (Ngoài đề bài)

| KPI | Công thức | Ý nghĩa |
|---|---|---|
| **Revenue Concentration (HHI)** | Chỉ số Herfindahl-Hirschman trên revenue per dealer | Đo rủi ro tập trung doanh thu vào ít đại lý |
| **Product Penetration Rate** | Số tỉnh có bán SKU X / Tổng 63 tỉnh | Mức độ phủ địa lý của từng sản phẩm |
| **Cross-sell Index** | Số nhóm SP khác nhau mà 1 đại lý mua | Đo chiều sâu quan hệ kinh doanh |
| **Price Realization Rate** | `AVG(order_line.unit_price) / product_price.unit_price` | Mức chiết khấu thực tế so với giá niêm yết |
| **Order Velocity** | Khoảng cách trung bình (ngày) giữa 2 đơn hàng liên tiếp | Early warning cho churn |
| **Weighted MAPE (Forecast KPI)** | `Σ|Actual - Predicted| / Σ|Actual|` | Thước đo accuracy chính cho forecasting |

---

## 12. Time-series Forecasting Considerations

### 12.1 Các Giả định Cần Validate TRƯỚC khi Modeling

| # | Giả định | Cách Validate | Rủi ro nếu Sai |
|---|---|---|---|
| 1 | **Demand có tính mùa vụ lặp lại** | Decompose time series, kiểm tra monthly pattern | Seasonal features vô nghĩa |
| 2 | **Lịch sử 14 tháng đủ để học pattern** | So sánh Seasonal Naive vs. Random Naive | Nếu Seasonal Naive thua → Không có mùa vụ rõ |
| 3 | **Demand tại mức SKU×Month đủ ổn định** | Kiểm tra hệ số CV (std/mean) cho từng SKU | CV > 1.5 → SKU quá noisy, cần aggregate lên Group |
| 4 | **Giá không thay đổi đột ngột trong Q2/2026** | Kiểm tra lịch sử tần suất thay đổi giá | Nếu có price shock → Model sẽ dự báo sai lớn |
| 5 | **Không có sản phẩm mới ra mắt trong Q2** | Kiểm tra với team Product | SKU mới = cold-start, cần xử lý riêng |
| 6 | **Mạng lưới đại lý ổn định** | Kiểm tra tỷ lệ churn/new dealer | Nếu biến động lớn → Feature `n_dealers` dự báo sai |

### 12.2 Các Leading Indicators cho Forecasting

| Indicator | Tín hiệu | Lead Time | Cách đưa vào Model |
|---|---|---|---|
| **Biến động số đại lý active** | Nhiều đại lý hơn = demand tăng | 1-2 tháng | `n_active_dealers_lag1` |
| **Xu hướng giá** | Giá tăng → Đại lý ôm hàng trước | 1 tháng | `price_change_pct_lag1` |
| **Momentum nhóm sản phẩm** | Group tăng → SKU trong group cũng tăng | 1 tháng | `group_total_qty_lag1` |
| **Tốc độ đặt hàng gần nhất** | Tần suất order tăng = demand tăng | 2-4 tuần | `n_transactions_lag1` |
| **Tỷ lệ đại lý quay lại (Repeat rate)** | Cao = demand bền vững | 1 tháng | `pct_repeat_dealers_lag1` |

### 12.3 Multi-step Forecasting Strategy

```
Tình huống: Dự báo 3 tháng tiếp theo (T4, T5, T6/2026)
Dữ liệu cuối cùng đã biết: T3/2026 (nếu pipeline ETL đã chạy xong)

Chiến lược DIRECT (Khuyến nghị):

  Model h=1: Dự báo T4/2026
    Features: lag_1 (T3), lag_2 (T2), lag_3 (T1), roll_mean_3 (T1-T3)

  Model h=2: Dự báo T5/2026
    Features: lag_2 (T3), lag_3 (T2), lag_4 (T1), roll_mean_3 (T1-T3)

  Model h=3: Dự báo T6/2026
    Features: lag_3 (T3), lag_4 (T2), lag_5 (T1), roll_mean_3 (T1-T3)

Lưu ý: lag_1 KHÔNG có sẵn cho h=2 và h=3 → Đây là lý do phải dùng Direct thay vì Recursive.
```

---

## 13. Potential ML Problems

| # | Bài toán ML | Loại | Input | Output | Business Value |
|---|---|---|---|---|---|
| 1 | **Demand Forecasting (SKU-level)** | Regression / Time Series | Lag, rolling, seasonal, hierarchy features | `quantity` dự kiến cho T4-T6/2026 | Kế hoạch sản xuất, tồn kho |
| 2 | **Dealer Churn Prediction** | Binary Classification | RFM features, order frequency, recency | Xác suất đại lý ngừng đặt hàng | Re-engagement campaigns |
| 3 | **Dealer Next-Order Prediction** | Binary Classification | Recency, frequency, monetary, SKU diversity | Xác suất đặt hàng trong 30 ngày | Ưu tiên tiếp thị |
| 4 | **Product Recommendation** | Collaborative Filtering | Ma trận Dealer × SKU × Quantity | Top-N SKU phù hợp cho từng đại lý | Cross-selling |
| 5 | **Price Elasticity Estimation** | Causal Inference / Regression | Price changes, quantity response | Hệ số co giãn cầu theo giá | Chiến lược pricing |
| 6 | **Anomaly Detection** | Unsupervised | Transaction patterns, price deviations | Giao dịch bất thường | Phòng ngừa gian lận |
| 7 | **Customer Lifetime Value (CLV)** | Regression | Lịch sử mua hàng, tenure, frequency | Giá trị dự kiến trong 12 tháng tới | Phân bổ nguồn lực sales |
| 8 | **SKU Clustering** | Unsupervised | Demand profile, price, seasonality | Nhóm SKU có hành vi tương tự | Cold-start handling |

---

## 14. Churn / RFM / Segmentation Opportunities

### 14.1 RFM Framework cho Đại lý

| Chiều | Cách tính | Business Meaning |
|---|---|---|
| **R**ecency | `CURRENT_DATE - MAX(order_date)` | Đại lý có đặt hàng gần đây không? |
| **F**requency | `COUNT(DISTINCT so_number)` trong 6 tháng gần nhất | Đại lý đặt hàng thường xuyên không? |
| **M**onetary | `SUM(line_total)` trong 6 tháng gần nhất | Đại lý chi tiêu bao nhiêu? |

### 14.2 Phân đoạn Đại lý (Segmentation Matrix)

| Segment | R | F | M | Hành động |
|---|---|---|---|---|
| **Champions** | Cao | Cao | Cao | Giữ chân, ưu đãi VIP |
| **Loyal** | Cao | Cao | TB | Tăng giá trị đơn hàng |
| **Potential** | Cao | TB | TB | Nurturing, Cross-sell |
| **New** | Cao | Thấp | Thấp | Onboarding, Khuyến mãi lần đầu |
| **At Risk** | TB | TB-Cao | TB-Cao | Liên hệ ngay, ưu đãi win-back |
| **Hibernating** | Thấp | Thấp | Thấp | Campaign re-engagement |
| **Lost** | Rất thấp | Thấp | Bất kỳ | Phân tích nguyên nhân, loại khỏi active list |

### 14.3 Churn Definition cho B2B Bike

> [!IMPORTANT]
> Trong B2B xe đạp, **chu kỳ đặt hàng tự nhiên** có thể kéo dài 2-3 tháng (đại lý nhỏ chỉ đặt 4 lần/năm). Do đó, ngưỡng churn KHÔNG nên đặt ở 30 ngày (như retail) mà nên ở **90 ngày không có đơn hàng** mới được coi là tín hiệu churn.

---

## 15. Important Data Quality Issues

| # | Vấn đề | Bảng | Mức độ | Hành động |
|---|---|---|---|---|
| 1 | **~30 SKU có `line_id = NULL`** | `product` | ⚠️ Trung bình | Impute qua tên sản phẩm hoặc gán "UNKNOWN_LINE" |
| 2 | **Một số dealer thiếu `province_id`** | `customer` | ⚠️ Trung bình | Lookup từ địa chỉ hoặc gán "UNKNOWN" |
| 3 | **Dữ liệu T3/2026 từ email/PDF** | Pipeline ETL | 🔴 Cao | Validate chéo trước khi dùng làm `lag_1` cho forecasting |
| 4 | **`line_total` có thể ≠ `quantity × unit_price`** | `order_line` | ⚠️ Trung bình | Business rule: cho phép sai số ±1% (do làm tròn VND) |
| 5 | **Duplicate transactions** | `order_line` | ⚠️ Trung bình | Dedup theo `(order_id, product_code)` nếu phát hiện |
| 6 | **Đơn vị tính không nhất quán** | `product` | 🟡 Thấp | 1 SKU có `unit = 'Ngày'` thay vì 'Chiếc' → Data entry error |
| 7 | **Mã màu không chuẩn hóa** | `product.color` | ⚠️ Trung bình | Cùng màu có nhiều cách ghi: "đen" vs "Đen" vs "Đen bóng" vs "Đen mờ" |
| 8 | **SKU mới chưa có lịch sử giá** | `product_price` | 🟡 Thấp | Một số SKU mới từ email T3/2026 chưa có entry trong product_price |

---

## 16. Risks & Modeling Pitfalls

### 16.1 Feature Leakage Risks

| Feature nguy hiểm | Loại Leakage | Giải pháp |
|---|---|---|
| `unit_price` của tháng hiện tại | **Target Leakage** — Giá giao dịch phản ánh volume discount | Dùng `avg_price_lag1` |
| `n_dealers` của tháng hiện tại | **Temporal Leakage** — Không biết trước số đại lý sẽ mua | Dùng `n_dealers_lag1` |
| `n_transactions` của tháng hiện tại | **Temporal Leakage** | Dùng `n_transactions_lag1` |
| Rolling stats bao gồm tháng t | **Subtle Leakage** — `rolling(3).mean()` bao gồm tháng hiện tại | Bắt buộc `shift(1)` trước rolling |
| Target encoding trên full data | **Train-Test Leakage** | fit() CHỈ trên Train, transform() frozen cho Val/Test |
| Random KFold cho Time Series | **Temporal Leakage** — Tương lai lọt vào training | Dùng `TimeSeriesSplit` hoặc Expanding Window |

### 16.2 Modeling Pitfalls

| Pitfall | Hậu quả | Phòng tránh |
|---|---|---|
| **Dùng `lag_12` với 14 tháng data** | Mất 12 tháng đầu → Chỉ còn 2 dòng/SKU | Bỏ `lag_12` ở mức SKU, thay bằng `seasonal_index` |
| **Train Individual Model per SKU** | 14 dòng vs 50 features → 100% Overfit | Train Global Model (gom 247 SKU) |
| **Bỏ qua Zero-Sales Imputation** | Lag bị lệch, mô hình không biết SKU "ế" | Điền 0 cho tháng sau `first_sale_date` không có giao dịch |
| **Xóa outlier B2B (đơn sỉ lớn)** | Mất thông tin demand thật | Winsorize thay vì delete |
| **Recursive multi-step forecast** | Error accumulation qua 3 bước | Direct method: train 3 model riêng cho h=1,2,3 |
| **Đánh giá model bằng Random Split** | Val score ảo, Test score nát | Temporal split: Train→2025, Val→Q1/2026, Test→Q2/2026 |
| **Forecast tại Dealer×SKU level** | Ma trận quá sparse (702×247×3 ≈ 520K, >99% = 0) | Forecast ở SKU×Month, disaggregate xuống nếu cần |

---

## 17. Suggested Feature Families

### 17.1 Bảng Tổng hợp Feature Families

| Family | Số Features | Data Source | Leakage Risk | Priority |
|---|---|---|---|---|
| **Time** | ~11 | Calendar | ✅ Safe | P0 |
| **Lag** | ~10 | `fact_sales` aggregated | ✅ Safe (shifted) | P0 |
| **Rolling** | ~9 | `fact_sales` aggregated | ⚠️ Cần shift(1) | P0 |
| **Trend/Momentum** | ~6 | Derived from Lag/Rolling | ✅ Safe | P1 |
| **Seasonality** | ~6 | Train-only computation | ⚠️ Fit on Train only | P1 |
| **Hierarchy** | ~8 | Group/Line aggregations | ✅ Safe (lagged) | P1 |
| **Dealer** | ~7 | `customer` + `fact_sales` | ⚠️ Must be lagged | P2 |
| **Pricing** | ~7 | `order_line` + `product_price` | 🔴 High risk | P2 |
| **Regional** | ~6 | `province` + `fact_sales` | ✅ Safe (lagged) | P2 |
| **Lifecycle** | ~6 | Derived from first_sale_date | ✅ Safe | P2 |
| **Churn** | ~5 | Derived from Lag features | ✅ Safe | P3 |
| **Color** | ~5 | `product.color` + `fact_sales` | ⚠️ Train-only for ranks | P3 |
| **Interaction** | ~6 | Cross-feature combinations | Depends on components | P3 |
| **Encoding** | ~5 | Target/Label encoding | 🔴 High risk | P1 |

### 17.2 Top 10 "Quick Win" Features (Code ngay lập tức)

| Rank | Feature | Family | Tại sao Impact cao |
|---|---|---|---|
| 1 | `total_quantity_lag_1` | Lag | Tín hiệu demand gần nhất, predictor mạnh nhất |
| 2 | `total_quantity_roll_mean_3` | Rolling | Smoothed signal, giảm nhiễu đơn hàng lumpy |
| 3 | `month` / `month_sin` / `month_cos` | Time | Bắt mùa vụ (Tết, 1/6, Back-to-school) |
| 4 | `group_total_qty_lag1` | Hierarchy | Context: nhóm SP mẹ đang tăng/giảm? |
| 5 | `seasonal_index` | Seasonality | Hệ số mùa vụ theo SKU×Month |
| 6 | `n_active_dealers_lag1` | Dealer | Breadth of distribution = leading indicator |
| 7 | `momentum_1m` | Momentum | Phát hiện gia tốc hoặc giảm tốc |
| 8 | `avg_price_lag1` | Pricing | Mức giá ảnh hưởng elasticity |
| 9 | `months_since_launch` | Lifecycle | Phân biệt sản phẩm mới vs. cũ |
| 10 | `total_quantity_lag_3` | Lag | Xu hướng quý gần nhất |

---

## 18. Recommended Analytical Directions

### 18.1 Cho Dashboard (BI Analyst)

| Direction | Câu hỏi cần trả lời | Biểu đồ |
|---|---|---|
| **Revenue Trend** | Doanh thu tăng hay giảm? Tốc độ? | Line chart MoM/QoQ |
| **Product Mix** | Nhóm nào đang chiếm tỷ trọng lớn nhất? | Stacked bar / Treemap |
| **Regional Heatmap** | Vùng nào bán mạnh? Vùng nào yếu? | Choropleth map 63 tỉnh |
| **Top/Bottom SKU** | SKU bán chạy vs. SKU ế | Pareto chart (80/20) |
| **Dealer Activity** | Bao nhiêu đại lý active/churn? | Funnel / Cohort chart |
| **Price Impact** | Đợt tăng giá ảnh hưởng demand thế nào? | Before/After comparison |
| **Seasonal Pattern** | Pattern nào lặp lại hàng năm? | Seasonal decomposition |

### 18.2 Cho Forecasting (Data Scientist)

| Direction | Approach | Expected Impact |
|---|---|---|
| **Segment-based modeling** | Train model riêng cho High/Medium/Low volume SKU | +5-10% accuracy |
| **Hierarchical Reconciliation** | MinT/Bottom-up/Middle-out cho multi-level consistency | Coherent forecasts |
| **Feature selection (Boruta/SHAP)** | Giữ 15-20 features tinh túy từ 50+ candidates | Giảm overfit |
| **Ensemble** | LightGBM (0.4) + XGBoost (0.3) + CatBoost (0.3) | +3-5% accuracy |
| **Cold-start handling** | Analogy-based forecast cho SKU mới | Coverage 100% SKU |

### 18.3 Cho Chiến lược (Business Stakeholder)

| Direction | Insight cần tạo | Action |
|---|---|---|
| **BCG Matrix** | Phân loại 5 nhóm SP: Star / Cash Cow / Dog / Question Mark | Portfolio rebalancing |
| **Dealer Lifecycle** | Hành trình đại lý từ New → Active → Declining → Churn | Trigger-based campaigns |
| **Geographic Whitespace** | Tỉnh nào chưa có đại lý nhưng có tiềm năng | Expansion strategy |
| **Price Optimization** | Mức giá nào tối ưu revenue (Price × Volume) | Pricing committee input |

---

## 19. Business Hypotheses Worth Testing

### 19.1 Hypotheses về Demand

| # | Giả thuyết | Cách Test | Data cần |
|---|---|---|---|
| H1 | **Xe trẻ em (KIDBIKE) có 2 đỉnh mùa: Tết + 1/6** | Decompose monthly demand cho KIDBIKE_1, KIDBIKE_2 | `v_monthly_by_group` |
| H2 | **Xe thể thao nhôm (SPORTBIKE_A) bán chạy hơn ở đô thị lớn** | So sánh revenue share theo region cho SPORTBIKE_A | `fact_sales` WHERE `group_code = 'SPORTBIKE_A'` GROUP BY `region` |
| H3 | **Đại lý ôm hàng trước mỗi đợt tăng giá** | Event study: quantity spike 1-2 tháng trước `effective_from` | `product_price` JOIN `fact_sales` |
| H4 | **80% doanh thu đến từ 20% SKU (Pareto)** | Cumulative revenue distribution | `fact_sales` GROUP BY `product_code` |
| H5 | **Xe IP bản quyền (Batman, Superman) có demand ổn định hơn xe thường** | So sánh CV (coefficient of variation) giữa IP vs non-IP SKU | `fact_sales` + product metadata |

### 19.2 Hypotheses về Dealer Behavior

| # | Giả thuyết | Cách Test | Data cần |
|---|---|---|---|
| H6 | **Đại lý VIP có tần suất đặt hàng cao hơn 3x so với STANDARD** | Trung bình orders/tháng theo `customer_tier` | `sales_order` JOIN `customer` |
| H7 | **Đại lý ngừng hoạt động >90 ngày có xác suất quay lại <10%** | Survival analysis trên cohort đại lý dormant | `v_customer_activity` |
| H8 | **Đại lý mới (first order <6 tháng) có tỷ lệ churn 40%** | Cohort retention analysis | `customer` + `sales_order` |
| H9 | **Đại lý miền Nam đặt hàng đều đặn hơn miền Bắc** | So sánh `order_interval_std` theo region | `sales_order` JOIN `customer` JOIN `province` |

### 19.3 Hypotheses về Pricing

| # | Giả thuyết | Cách Test | Data cần |
|---|---|---|---|
| H10 | **Tăng giá 5% → Giảm quantity 8-12% (Elastic demand)** | Regression: Δquantity ~ Δprice, controlling for seasonality | `fact_sales` + `product_price` |
| H11 | **Chênh lệch giá giao dịch vs giá list lớn hơn ở đại lý VIP** | `1 - AVG(order_unit_price) / AVG(list_price)` by tier | `order_line` JOIN `product_price` JOIN `customer` |

---

## 20. Final Recommendations for Data Team

### 20.1 Ưu tiên Triển khai (theo tuần)

```
TUẦN 1 — NỀN MÓNG
├── [1] Validate dữ liệu T3/2026 từ pipeline ETL (Hạng mục A)
├── [2] Tạo các Materialized Views bổ sung (v_sku_monthly_agg)
├── [3] Clean data: Fix NULL line_id, normalize color names
├── [4] Zero-sales imputation cho time series
└── [5] Baseline model: Seasonal Naïve + LightGBM với Quick Win features

TUẦN 2 — CORE FEATURES & MODELS
├── [6] Full Lag + Rolling + Seasonality features
├── [7] Temporal CV validation (Expanding Window)
├── [8] Train XGBoost + CatBoost
├── [9] Dashboard MVP: Revenue trend, Product mix, Regional heatmap
└── [10] RFM segmentation cho đại lý

TUẦN 3 — ADVANCED
├── [11] Dealer-level features + Pricing features
├── [12] Lifecycle + Momentum + Churn features
├── [13] Hyperparameter tuning (Optuna)
├── [14] Ensemble: Weighted average LGB+XGB+CB
└── [15] Dealer Churn Classifier (Câu hỏi 3 đề thi)

TUẦN 4 — POLISH & DELIVERY
├── [16] Hierarchical Reconciliation (Middle-out)
├── [17] Error Analysis & Edge case handling
├── [18] LLM integration cho Business Insights (Điểm cộng)
├── [19] Final Dashboard + Technical Report
└── [20] Submission optimization
```

### 20.2 Nguyên tắc Vàng

1. **Temporal integrity first.** Mọi feature phải tuân thủ nguyên tắc "không nhìn tương lai". Nghi ngờ → Dùng `shift(1)`.
2. **Global Model over Local Model.** 14 tháng data quá ngắn cho individual SKU model. Gom 247 SKU lại train chung.
3. **Validate before you model.** Kiểm tra 6 giả định ở mục 12.1 trước khi viết dòng code đầu tiên.
4. **Start simple, iterate fast.** Seasonal Naïve baseline → Quick Win LightGBM → Full features → Ensemble.
5. **Business context = Competitive advantage.** Hiểu rằng đại lý mua trước mùa, hiểu price elasticity, hiểu chu kỳ B2B — đây là thứ phân biệt giữa model tốt và model tuyệt vời.

---

*Document Version: 1.0 | Created: 23/05/2026 | Schema: tnbike (PostgreSQL 14+)*
*Designed for Data Explorers 2026 — Thống Nhất Bike B2B Demand Forecasting*
