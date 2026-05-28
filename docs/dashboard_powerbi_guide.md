# 📊 Tài Liệu Đặc Tả & Thiết Kế Power BI Dashboard (Hạng mục B)
## Đội thi: Data Explorers 2026 | Thống Nhất Bike

Tài liệu này trình bày chi tiết về phương pháp luận thiết kế, các quyết định xử lý dữ liệu, công thức DAX và 5 phát hiện kinh doanh (Business Insights) quan trọng được trích xuất từ hệ thống Power BI Dashboard của đội Data Explorers.

---

## 1. KIỂM ĐỊNH TÍNH TOÀN VẸN DỮ LIỆU (DATA AUDIT)

> [!IMPORTANT]
> Qua quá trình phân tích Exploratory Data Analysis (EDA), đội thi phát hiện dữ liệu lịch sử cung cấp có đặc thù phân mảnh về mặt thời gian. Dữ liệu thực tế phân bố trong **6 tháng** (T1-T3/2025 và T1-T3/2026), có khoảng trống (gap) từ T4 đến T12/2025.

### Phân bổ dòng chảy dữ liệu (Data Distribution)

| Năm | Tháng | Số đơn | Sản lượng | Doanh thu | Số Đại lý Active | Tăng trưởng MoM |
|---|---|---|---|---|---|---|
| 2025 | T1 | 61 | 1,837 | 3.20 tỷ | 46 | — |
| 2025 | T2 | 185 | 5,030 | 6.34 tỷ | 141 | +98.2% |
| 2025 | T3 | 447 | 14,609 | 18.58 tỷ | 242 | +193.2% |
| 2026 | T1 | 482 | 12,541 | 21.14 tỷ | 290 | +13.7%* |
| 2026 | T2 | 452 | 12,522 | 19.39 tỷ | 268 | -8.3% |
| 2026 | T3 | **1,132** | **25,607** | **40.80 tỷ** | **394** | **+110.4%** |
| **TỔNG** | | **2,759** | **72,146** | **109.45 tỷ** | **798** | |

*(Ghi chú: MoM T1/2026 so với T3/2025 do thiếu dữ liệu T4-T12/2025).*

**Quyết định Thiết kế:** Trong Dashboard, các biểu đồ theo chuỗi thời gian (Time-series) liên tục sẽ sử dụng Clustered Bar Chart thay vì Line Chart để phản ánh trung thực khoảng trống dữ liệu, tránh gây hiểu lầm cho Ban Giám đốc về xu hướng liền mạch. Các so sánh cùng kỳ (YoY) chỉ áp dụng nghiêm ngặt cho Quý 1.

---

## 2. PHÁT HIỆN & XỬ LÝ BẤT THƯỜNG DỮ LIỆU (DATA QUALITY ANOMALIES)

Trong quá trình ETL, hệ thống ghi nhận các bất thường về cấu trúc dữ liệu và đã có phương án xử lý (Workarounds) trực tiếp trong Power BI và SQL Views.

| Vấn đề phát hiện | Quy mô ảnh hưởng | Quyết định xử lý Kỹ thuật |
|---|---|---|
| **90 SKU thiếu phân loại (Missing Product Line/Group)** | Chiếm 23% doanh thu (25.28 tỷ), 18% sản lượng (13,019 xe) | Khởi tạo nhóm `Chưa phân loại` trong DAX để bảo toàn 100% doanh thu tổng. |
| **Bất cân xứng Vùng miền (Regional Imbalance)** | Miền Nam chỉ có 4 đại lý (0.5%), Miền Bắc chiếm 72.6% | Giữ nguyên dữ liệu gốc, chuyển hóa thành Business Insight về tiềm năng mở rộng thị trường. |
| **Dữ liệu màu sắc không đồng nhất** | Ghi nhận sự phân mảnh giữa "đen" và "Đen" | Áp dụng hàm `INITCAP` trong SQL Patch và `Text.Proper` trong Power Query. |
| **Thiếu thông tin Địa lý khách hàng** | 97 khách hàng (5.88 tỷ doanh thu) không có `province_id` | Định danh nhóm `Chưa xác định` trên Bản đồ nhiệt (Heatmap). |

---

## 3. THIẾT KẾ CƠ SỞ DỮ LIỆU & SQL VIEWS (BACKEND LOGIC)

Để tối ưu hóa hiệu năng render của Power BI, các tính toán phức tạp đã được đẩy xuống tầng Database (PostgreSQL) thông qua các SQL Views chuyên dụng.

### 3.1. Mô hình Chấm điểm B2B RFM (`v_rfm_analysis`)
Thang điểm RFM được tùy chỉnh riêng cho **đặc thù bán sỉ (B2B)**, không sử dụng hàm phân vị `NTILE` tiêu chuẩn mà thiết lập các ngưỡng (thresholds) bám sát thực tế kinh doanh:
- Thêm phân khúc **`Big Spender`**: Đại lý có tần suất mua thấp nhưng giá trị mỗi đơn hàng cực cao (đặc trưng của việc nhập sỉ theo quý).
- **Quy tắc phân loại:** 
  - `Champions`: R >= 4, F >= 4, M >= 4 (Ưu tiên bảo vệ)
  - `At Risk`: R <= 2, F >= 3, M >= 3 (Rủi ro mất khách sỉ)

### 3.2. Ma trận Tỷ trọng Sản phẩm BCG (`v_bcg_matrix`)
Giải quyết bài toán phân tích danh mục đầu tư (Portfolio Analysis):
- **Xử lý Outliers:** Áp dụng trung vị `PERCENTILE_CONT(0.5)` thay vì `AVG` để xác định ngưỡng thị phần, tránh việc một dòng xe bán quá chạy (Xe New 26) làm sai lệch tiêu chuẩn của toàn bộ danh mục.
- **Phân tách Xe Mới:** Tách riêng nhóm `New Launch` cho các dòng xe chỉ có doanh thu 2026, tránh hệ thống phân loại nhầm vào nhóm `Dogs` do thiếu dữ liệu tăng trưởng YoY.

---

## 4. CHỈ SỐ ĐO LƯỜNG DAX (DAX MEASURES)

Hệ thống sử dụng các biểu thức DAX tối ưu hóa ngữ cảnh lọc (Filter Context):

```dax
// Tăng trưởng MoM (Month-over-Month)
% Tăng Trưởng DT MoM = 
VAR cur = SUM('tnbike fact_sales'[line_total])
VAR prev = CALCULATE(SUM('tnbike fact_sales'[line_total]), DATEADD('tnbike fact_sales'[order_date], -1, MONTH))
RETURN DIVIDE(cur - prev, ABS(prev))

// Tăng trưởng Q1 YoY (Year-over-Year)
Doanh Thu Q1 YoY = 
VAR cur_q1 = CALCULATE([Tổng Doanh Thu], 'tnbike fact_sales'[fiscal_year]=2026, 'tnbike fact_sales'[fiscal_quarter]=1)
VAR prev_q1 = CALCULATE([Tổng Doanh Thu], 'tnbike fact_sales'[fiscal_year]=2025, 'tnbike fact_sales'[fiscal_quarter]=1)
RETURN DIVIDE(cur_q1 - prev_q1, ABS(prev_q1))

// Pareto - Tính tỷ trọng đóng góp của Top 20% Đại lý
Tỷ Trọng Doanh Thu Top 20% =
VAR top_n_count = ROUNDUP(COUNTROWS(VALUES('tnbike fact_sales'[customer_code])) * 0.2, 0)
VAR top_dealers = TOPN(top_n_count, 
    SUMMARIZE(ALL('tnbike fact_sales'), 'tnbike fact_sales'[customer_code], "rev", [Tổng Doanh Thu]), 
    [rev], DESC)
VAR top_rev = SUMX(top_dealers, [rev])
RETURN DIVIDE(top_rev, CALCULATE([Tổng Doanh Thu], ALL('tnbike fact_sales'[customer_code])))
```

---

## 5. CẤU TRÚC 6 TRANG BÁO CÁO (DASHBOARD LAYOUT)

Dashboard được thiết kế theo nguyên tắc *Top-down Analytical Workflow* (Từ tổng quan đến chi tiết):

1. **Executive Overview (Tổng quan Quản trị):** Cung cấp góc nhìn toàn cảnh về Sức khỏe Doanh nghiệp (109.4 tỷ DT). Tích hợp phễu vận hành ETL thể hiện tỷ lệ xử lý dữ liệu thành công 100%.
2. **Time Analysis (Phân tích Thời gian):** Làm rõ chu kỳ bán hàng. Điểm nhấn: Quý 1/2026 tăng trưởng đột phá +189.2% so với cùng kỳ.
3. **Product & BCG (Phân tích Sản phẩm):** Trực quan hóa ma trận BCG dạng Scatter Plot. Nhận diện các dòng xe "Ngôi sao" (Xe New 26, Xe New 24).
4. **Dealer RFM (Phân tích Đại lý):** Cảnh báo sớm rủi ro (Churn Risk). Phân tích hiệu ứng Pareto: Top 20% đại lý mang lại phần lớn doanh thu.
5. **Geographic (Phân tích Vùng miền):** Đánh giá rủi ro tập trung địa lý (Concentration Risk). Phân bổ mật độ theo 63 tỉnh thành.
6. **Pipeline Operations (Giám sát Hệ thống):** Dành cho đội ngũ IT Data, theo dõi tình trạng xử lý của 1,132 luồng email hóa đơn T3/2026.

---

## 6. 7 INSIGHTS CHIẾN LƯỢC TỪ DỮ LIỆU (BUSINESS INSIGHTS)

Từ việc đào sâu vào dữ liệu qua các góc độ Thời gian, Sản phẩm, Đại lý và Địa lý, đội thi đề xuất 7 nhận định chiến lược mang tính hành động cao:

### 🕒 Phân Tích Thời Gian

**Insight 1 — Hiệu ứng mùa vụ Q1 tái diễn và ngày càng mạnh hơn**
> 📊 **Phát hiện:** Dashboard so sánh Q1/2026 vs Q1/2025 cho thấy doanh thu tháng 3 tăng đột biến so với tháng 2 trong cả hai năm — biên độ tăng ước tính +90–120% theo chu kỳ. Ribbon chart xác nhận nhóm xe City/Phổ thông dẫn đầu dịch chuyển thứ hạng trong giai đoạn này.
> 💡 **Ý nghĩa:** Đây không phải tăng trưởng ngẫu nhiên — mà là hiệu ứng mùa vụ có tính chu kỳ (tựu trường, Tết xong). Nếu doanh nghiệp không chuẩn bị trước tồn kho từ tháng 1, sẽ bị thiếu hàng đúng đỉnh cầu, mất doanh thu vào tay đối thủ.
> ✅ **Khuyến nghị:** Lập kế hoạch sản xuất & nhập hàng cho nhóm xe phổ thông trước tháng 1 hàng năm, dự trữ tối thiểu +30% so với tháng 2 cùng kỳ. Đặt cảnh báo tự động trên dashboard khi tồn kho xuống dưới ngưỡng an toàn vào tuần đầu tháng 2.

**Insight 2 — Tháng 2 là "đáy mùa vụ" hằng năm — cơ hội kích cầu bị bỏ lỡ**
> 📊 **Phát hiện:** Heatmap doanh thu cho thấy tháng 2 là ô tối nhất trong toàn bộ ma trận (thấp nhất trong năm), lặp lại cả 2025 lẫn 2026. Tốc độ tăng trưởng MoM (tháng 2→3) là mức nhảy lớn nhất trong năm — chứng tỏ cầu tiềm năng đã tích lũy sẵn nhưng chưa có kích thích.
> 💡 **Ý nghĩa:** Tháng 2 thấp chủ yếu do tâm lý sau Tết, không phải do thiếu cầu thực sự. Các đại lý cũng trì hoãn đặt hàng. Đây là khoảng trống chính sách — nếu có chương trình kích cầu đúng lúc, có thể "kéo sớm" doanh thu tháng 3 vào tháng 2.
> ✅ **Khuyến nghị:** Triển khai chương trình chiết khấu đặt hàng sớm tháng 2 (early order discount) cho đại lý: đặt trong tháng 2, nhận hàng tháng 3 — giúp doanh nghiệp dự báo cầu chính xác hơn và đại lý được giá tốt hơn. Dự kiến san phẳng đáy mùa vụ 15–25%.

### 🚲 Phân Tích Sản Phẩm

**Insight 3 — Tập trung SKU nguy hiểm: 1 dòng xe chiếm tỷ trọng quá lớn**
> 📊 **Phát hiện:** Chỉ số "% Top 1 Dòng xe" trên dashboard sản phẩm và biểu đồ donut cho thấy dòng xe dẫn đầu chiếm tỷ trọng doanh thu vượt trội so với các dòng còn lại. Ma trận BCG xác nhận chỉ có 1–2 dòng xe ở góc "Star", phần lớn còn lại là "Cash Cow" hoặc "Question Mark".
> 💡 **Ý nghĩa:** Rủi ro danh mục sản phẩm cao: nếu dòng xe chủ lực gặp sự cố (đứt chuỗi cung ứng, đối thủ ra mẫu cạnh tranh, thay đổi thị hiếu), doanh thu toàn công ty sụt giảm nghiêm trọng ngay trong quý tiếp theo. Doanh nghiệp đang "đặt cược" quá nhiều vào 1 SKU.
> ✅ **Khuyến nghị:** Đặt KPI tối đa hóa danh mục: không để 1 dòng xe chiếm >35% doanh thu. Phân bổ ngân sách marketing để đẩy 2–3 dòng xe "Question Mark" trong BCG lên "Star" trong vòng 2 quý. Đồng thời xây dựng kịch bản dự phòng (contingency plan) nếu dòng chủ lực giảm >20%.

**Insight 4 — Màu sắc không đồng đều theo vùng: Đặt hàng sai màu = hàng tồn**
> 📊 **Phát hiện:** Biểu đồ "Top 4 màu sắc theo nhóm xe" kết hợp với phân tích địa lý cho thấy sở thích màu sắc không đồng nhất giữa các vùng. Một số màu có tỷ trọng cao ở Miền Nam nhưng rất thấp ở Miền Bắc, và ngược lại — gây ra mất cân bằng tồn kho khi phân phối đồng đều.
> 💡 **Ý nghĩa:** Chính sách giao hàng "một màu cho tất cả" dẫn đến tồn kho chậm luân chuyển tại những vùng không ưa màu đó, đồng thời thiếu hàng màu ưa chuộng ở vùng khác. Đây là nguồn gốc của vốn bị chôn vào hàng tồn không cần thiết.
> ✅ **Khuyến nghị:** Xây dựng bản đồ sở thích màu theo vùng từ dữ liệu lịch sử và cập nhật vào kế hoạch sản xuất theo quý. Đặt hàng màu sắc theo tỉnh/vùng thay vì theo tổng quốc. Áp dụng thí điểm cho Q2/2026 với 3 tỉnh có doanh thu cao nhất.

### 🏪 Phân Tích Đại Lý

**Insight 5 — Concentration Risk: Top 20% đại lý nắm giữ phần lớn doanh thu**
> 📊 **Phát hiện:** Chỉ số "Tỷ trọng doanh thu Top 20%" đại lý trên dashboard cho thấy quy luật Pareto lệch mạnh — nhóm nhỏ đại lý lớn đóng góp tỷ trọng doanh thu không cân xứng. RFM scatter chart xác nhận nhóm "Champions" chỉ chiếm thiểu số nhưng monetary rất cao.
> 💡 **Ý nghĩa:** Rủi ro tập trung kênh phân phối: nếu 1 đại lý lớn rời bỏ hoặc chuyển sang nhà cung cấp khác, doanh thu có thể giảm 5–10% ngay lập tức. Trong bối cảnh 702 đại lý nhưng phân bổ không đều, mạng lưới hiện tại mỏng manh hơn con số tuyệt đối cho thấy.
> ✅ **Khuyến nghị:** Thiết lập chương trình retention cho nhóm Champions và Loyal (theo RFM): ưu tiên chính sách giá, hỗ trợ trưng bày, thăm viếng định kỳ. Song song, đặt KPI tuyển dụng đại lý mới tại các tỉnh dưới trung bình — mục tiêu giảm tỷ trọng top 20% xuống dưới 60% trong 2 quý.

**Insight 6 — Đại lý có độ phủ sản phẩm thấp: Tiềm năng cross-sell bị bỏ ngỏ**
> 📊 **Phát hiện:** Bảng "Độ phủ sản phẩm theo đại lý" cho thấy nhiều đại lý chỉ đặt 1–2 dòng xe dù doanh nghiệp có 5 nhóm sản phẩm. Nhóm đại lý có số dòng xe trung bình/đơn thấp tập trung nhiều ở phân khúc RFM "At Risk" và "Potential Loyalists".
> 💡 **Ý nghĩa:** Đây là doanh thu tiềm năng chưa khai thác: nếu mỗi đại lý "1 dòng xe" thêm được 1 dòng xe thứ 2, doanh thu trên đại lý đó tăng ngay 50–100% mà không cần tuyển thêm đại lý mới — hiệu quả vốn cao hơn nhiều so với mở rộng kênh.
> ✅ **Khuyến nghị:** Tạo chương trình "Mở rộng danh mục" cho đại lý độ phủ thấp: chiết khấu 3–5% khi đặt lần đầu dòng xe mới, kèm hỗ trợ trưng bày. Sales team ưu tiên tiếp cận đại lý có doanh thu đơn cao nhưng chỉ mua 1–2 SKU — đây là nhóm có ROI cao nhất cho hoạt động upsell.

### 🗺 Phân Tích Địa Lý

**Insight 7 — Tỉnh "tiềm năng ẩn": Dân số lớn nhưng doanh thu thấp bất thường**
> 📊 **Phát hiện:** So sánh Q1/2025 vs Q1/2026 theo vùng và bản đồ treemap cho thấy một số tỉnh nằm trong vùng tăng trưởng mạnh nhưng doanh thu tuyệt đối vẫn thấp — gợi ý đây là vùng chưa có đại lý phủ hoặc đại lý hiện tại năng lực thấp, không phải vì thị trường yếu.
> 💡 **Ý nghĩa:** Phân bổ nguồn lực bán hàng theo doanh thu hiện tại sẽ bỏ lỡ các thị trường đang hình thành. Các tỉnh có tốc độ tăng trưởng cao nhưng nền thấp thường là nơi đối thủ chưa đặt chân — cơ hội first-mover advantage còn nguyên.
> ✅ **Khuyến nghị:** Lập danh sách ưu tiên tuyển đại lý mới dựa trên 2 tiêu chí: (1) tốc độ tăng trưởng địa lý >15% YoY và (2) doanh thu/tỉnh dưới 50% mức trung bình vùng. Phân bổ ngân sách thị trường mới cho Q3/2026, tập trung vào 3–5 tỉnh tiềm năng ưu tiên cao nhất.
