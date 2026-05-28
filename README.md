# 📊 TNBike Data Analytics — Data Explorers Vòng 2 (2026)

Chào mừng các thành viên team **Data Explorers**! Đây là repository lưu trữ toàn bộ mã nguồn ETL, phân tích thống kê (EDA) và Dashboard Power BI cho vòng 2 cuộc thi Data Explorers 2026.

Tài liệu này hướng dẫn cách cài đặt môi trường, quy trình chạy pipeline làm sạch dữ liệu và phân định rõ **ai cần làm gì và để file ở đâu** để tránh xung đột code (conflict Git).

---

## 1. Tổng Quan Kỹ Thuật

| Hạng mục | Chi tiết |
|---|---|
| **Database** | PostgreSQL — `tnbike_db`, schema `tnbike` |
| **Bảng fact chính** | `tnbike.fact_sales` (denormalized, dùng cho Power BI & EDA) |
| **Ngôn ngữ xử lý** | Python 3.x (`psycopg2`, `pdfplumber`, `pandas`) |
| **Dashboard** | Power BI Desktop — kết nối trực tiếp PostgreSQL localhost |
| **Phạm vi dữ liệu** | T1–T3/2025 (lịch sử) + T1–T3/2026 (từ email hóa đơn PDF) |

---

## 2. Cấu Trúc Repository Chuẩn

> [!NOTE]
> Các thư mục đánh dấu `[Không commit]` sẽ ở trạng thái trống rỗng trên GitHub (chỉ chứa file `.gitkeep` ẩn). Mỗi thành viên khi clone repo về máy phải tự nạp dữ liệu cục bộ theo hướng dẫn bên dưới.

```text
TPT_Data-Explorers-2026/
│
├── database/                           # Quản lý SQL & Database
│   ├── 01_create_tables.sql            # DDL: Tạo schema tnbike & toàn bộ bảng
│   ├── 02_import_data.sql              # Seed: Nạp dữ liệu lịch sử T1-T3/2025
│   ├── patches/                        # Bản vá lỗi dữ liệu (chạy sau Seed)
│   │   ├── db_data_quality_patch.sql   # Vá lỗi font, màu HP/Batman, chuẩn hóa SKU
│   │   └── geo_clean_patch_final.sql   # Làm sạch tỉnh thành, seed bảng province_clean
│   └── views/                          # SQL tạo Views cho Power BI (chạy 1 lần)
│       └── powerbi_views.sql           # Gồm 4 views: v_rfm_analysis, v_bcg_matrix,
│                                       #   v_pipeline_status, v_data_quality_summary
│
├── src/                                # Mã nguồn Python chính (Production Pipeline)
│   ├── extract_validate.py             # [ETL-E] Parse email .eml + PDF hóa đơn T3/2026 → JSON thô
│   ├── normalize.py                    # [ETL-T] Chuẩn hóa màu sắc, đơn vị, map dòng xe → JSON sạch
│   ├── load_to_database.py             # [ETL-L] Nạp JSON sạch vào PostgreSQL, cập nhật fact_sales
│   ├── eda/                            # Script EDA tự động (vẽ phân phối, kiểm tra lỗi)
│   ├── models/                         # Code huấn luyện / dự báo (train.py, predict.py)
│   ├── utils/                          # Hàm tiện ích dùng chung (clean text, parse số tiền...)
│   └── __init__.py
│
├── notebooks/                          # [Không commit dữ liệu] Phân tích thử nghiệm (EDA)
│   └── .gitkeep
│
├── models/                             # [Không commit] File binary mô hình đã train (.pkl)
│
├── bi/                                 # Tài nguyên Power BI Dashboard
│   └── dax/                            # Backup các Measure DAX đã viết
│
├── docs/                               # Tài liệu thuyết minh & hướng dẫn kỹ thuật
│   ├── dashboard_powerbi_guide.md      # Hướng dẫn thiết kế 6 trang Dashboard + DAX Measures
│   ├── rfm_scoring_analysis.md         # Thuyết minh phương pháp chấm điểm RFM B2B
│   └── product_line_mapping_analysis.md # Phân tích mapping 55 SKU chưa phân loại
│
├── data/                               # [Không commit] Dữ liệu thô & đã xử lý
│   ├── raw/emails/                     # Đặt các file .eml hóa đơn T3/2026 vào đây
│   └── processed/                      # processed_data.json & processed_data_clean.json
│
└── README.md
```

---

## 3. Sơ Đồ Database (`tnbike` schema)

```
province ──────────────────────────────────────────────────────────────────┐
   ↑                                                                        │
customer (province_id FK) ────────────────────────────────────────────────┤
   ↑                                                                        │
sales_order (customer_code FK)                                              │
   ↑                                                                        │
order_line (order_id FK, product_code FK)                                   │
   ↑                                                                        │
product (line_id FK)                                                        │
   ↑                                                                        │
product_line (group_id FK) ──── product_group                              │
                                                                            │
province_clean (province_id FK) ◄──────────────────────────────────────────┘
   [Bảng chuẩn hóa tỉnh thành, tạo bởi geo_clean_patch_final.sql]

fact_sales  ← Bảng denormalized phẳng (cho Power BI & EDA, tổng hợp từ JOIN ở trên)
email_log   ← Bảng theo dõi trạng thái xử lý hóa đơn (READY_TO_INSERT, ERROR...)
```

**4 Views đã tạo sẵn cho Power BI** (`database/views/powerbi_views.sql`):
| View | Mục đích |
|---|---|
| `tnbike.v_rfm_analysis` | Chấm điểm RFM, phân 8 nhóm đại lý B2B |
| `tnbike.v_bcg_matrix` | Ma trận BCG dòng xe (100% doanh thu, gồm nhóm Chưa phân loại) |
| `tnbike.v_pipeline_status` | Thống kê trạng thái xử lý email (cho trang Vận hành) |
| `tnbike.v_data_quality_summary` | Audit nhanh lỗi dữ liệu (thiếu tỉnh, thiếu nhóm xe...) |

---

## 4. Quy Trình Chạy Pipeline Dữ Liệu (Từ A → Z)

### Bước 1: Cài đặt thư viện Python
```bash
pip install psycopg2-binary pdfplumber pandas
```

### Bước 2: Thiết lập Database & Nạp dữ liệu lịch sử
Mở DBeaver / pgAdmin, tạo database tên `tnbike_db`, sau đó chạy **lần lượt** 2 file SQL của Ban Tổ Chức:

```
1. database/01_create_tables.sql     ← Tạo toàn bộ bảng & schema tnbike
2. database/02_import_data.sql       ← Nạp dữ liệu lịch sử T1-T3/2025
```

### Bước 3: Cấu hình kết nối Database trong code Python
Mở các file trong `src/` và kiểm tra block `DB_CONFIG`:
```python
DB_CONFIG = {
    "dbname": "tnbike_db",
    "user":   "postgres",
    "password": "YOUR_PASSWORD_HERE",  # ← Thay mật khẩu PostgreSQL local của bạn
    "host":   "localhost",
    "port":   "5432",
}
```

### Bước 4: Chạy pipeline ETL tháng 3/2026
Đặt các file `.eml` hóa đơn tháng 3 vào thư mục `data/raw/emails/`, rồi chạy lần lượt 3 lệnh:
```bash
# E — Extract: Parse email + PDF hóa đơn → JSON thô
python src/extract_validate.py

# T — Transform: Chuẩn hóa màu, đơn vị, map dòng xe → JSON sạch
python src/normalize.py

# L — Load: Nạp JSON sạch vào PostgreSQL, cập nhật fact_sales
python src/load_to_database.py
```

### Bước 5: Chạy các bản vá làm sạch dữ liệu (SQL Patches)
Sau khi đã nạp đủ cả dữ liệu 2025 lẫn T3/2026, chạy 2 file vá để làm sạch toàn bộ dữ liệu trong DB một lần:

```
3. database/patches/db_data_quality_patch.sql  ← Sửa lỗi font, màu HP/Batman, chuẩn hóa SKU
4. database/patches/geo_clean_patch_final.sql  ← Làm sạch địa lý, tạo bảng province_clean
```

> [!IMPORTANT]
> Chạy `geo_clean_patch_final.sql` **sau** `db_data_quality_patch.sql`. File này tạo bảng `province_clean` mà `powerbi_views.sql` (bước tiếp theo) phụ thuộc vào.

### Bước 6: Tạo Views cho Power BI
Chạy file SQL sau trong DBeaver / pgAdmin (chỉ cần chạy 1 lần, hoặc khi có cập nhật logic):
```
5. database/views/powerbi_views.sql   ← Tạo v_rfm_analysis, v_bcg_matrix, v_pipeline_status, v_data_quality_summary
```

### Bước 7: Kết nối Power BI
1. Mở file `.pbix` trong thư mục `bi/`.
2. **Get Data → PostgreSQL** → Host: `localhost`, Database: `tnbike_db`.
3. Chọn các bảng/views cần thiết, bấm **Load**.
4. Bấm **Refresh** để cập nhật số liệu mới nhất.

> [!TIP]
> **Tóm tắt thứ tự chạy đúng:**
> `01_create` → `02_import` → `extract_validate.py` → `normalize.py` → `load_to_database.py` → `db_quality_patch` → `geo_clean_patch` → `powerbi_views`

---

## 5. Hướng Dẫn Dành Cho Từng Vai Trò

> [!IMPORTANT]
> Để tránh xung đột git, vui lòng tuân thủ quy tắc **"Làm gì — Để ở đó"**:

| Bạn đang làm gì? | Đặt file ở đâu? |
|---|---|
| Phân tích EDA, vẽ biểu đồ nháp | `notebooks/[STT]_[muc_tieu].ipynb` |
| Phát hiện lỗi dữ liệu cần vá | Thêm câu `UPDATE` vào `database/patches/db_data_quality_patch.sql` |
| Sửa lỗi địa lý tỉnh thành | Thêm vào `database/patches/geo_clean_patch_final.sql` |
| Viết thêm DAX Measure mới | Backup vào `bi/dax/measures.dax` |
| Cập nhật logic View PostgreSQL | Sửa `database/views/powerbi_views.sql` |
| Viết tài liệu, báo cáo, thuyết minh | Lưu vào `docs/` |

---

## 6. Quy Tắc Git

### Quy ước đặt tên Commit (Conventional Commits)
```
feat:   Thêm tính năng mới     (vd: feat(models): add sales forecast using xgboost)
fix:    Sửa lỗi                (vd: fix(extract): resolve pdfplumber font encoding)
docs:   Cập nhật tài liệu      (vd: docs(rfm): add technical docs for rfm scoring)
chore:  Cấu hình, dọn dẹp      (vd: chore: update .gitignore)
sql:    Thêm/sửa SQL           (vd: sql(views): add v_data_quality_summary view)
```

### Quy trình làm việc theo nhánh (Branch Workflow)

> [!WARNING]
> **Tuyệt đối KHÔNG commit trực tiếp lên nhánh `main`.** Mọi thay đổi phải thực hiện trên nhánh phụ và merge vào qua Pull Request.

```bash
# 1. Cập nhật code mới nhất
git checkout main
git pull origin main

# 2. Tạo nhánh làm việc
git checkout -b feature/ten-nhiem-vu

# 3. Code xong, stage và commit
git add [các file liên quan]
git commit -m "feat: mô tả thay đổi"

# 4. Push và tạo Pull Request trên GitHub
git push -u origin feature/ten-nhiem-vu
```

### Các nhánh hiện có
| Nhánh | Mục đích |
|---|---|
| `main` | Nhánh chính — code ổn định, sẵn sàng nộp bài |
| `fix/geo-clean-fk-check` | Sửa lỗi FK địa lý (đang active) |
| `fix/province-standardization` | Chuẩn hóa tỉnh thành nâng cao |
| `feature/pipeline-integration` | Tích hợp pipeline tự động |

---

## 7. Tài Liệu Tham Khảo

| Tài liệu | Nội dung |
|---|---|
| [`docs/dashboard_powerbi_guide.md`](docs/dashboard_powerbi_guide.md) | Hướng dẫn chi tiết 6 trang Dashboard, DAX Measures tiếng Việt, SQL Views |
| [`docs/rfm_scoring_analysis.md`](docs/rfm_scoring_analysis.md) | Thuyết minh đầy đủ phương pháp RFM B2B, ngưỡng chấm điểm, 8 phân khúc |
| [`docs/product_line_mapping_analysis.md`](docs/product_line_mapping_analysis.md) | Phân tích 55 SKU chưa phân loại (12.9% doanh thu) |


# Thong Nhat Bike - Data Explorers Vòng 2

Repository chứa toàn bộ mã nguồn, dữ liệu và báo cáo phân tích cho cuộc thi **Data Explorers - Vòng 2** (Track 1, 2, 3), xây dựng hệ thống dự báo nhu cầu sản xuất và bán hàng cho chuỗi xe đạp Thống Nhất (Q2/2026).

---

## 1. Tổng Quan Dự Án (Project Overview)
Dự án được xây dựng theo một kiến trúc **End-to-End Data Pipeline**, đảm bảo nguyên tắc:
1. **Dữ liệu thô (Raw Data)** là bất biến (immutable), nằm tại `data/raw/`.
2. **Luồng dữ liệu một chiều (One-way Pipeline)**: Đầu ra của Phase trước là đầu vào của Phase sau.
3. **Reproducibility (Khả năng tái tạo)**: Toàn bộ quá trình từ raw data đến kết quả dự báo cuối cùng có thể được chạy lại tự động chỉ bằng 1 câu lệnh.

### Các Track (Bài toán) được giải quyết:
- **Track 1:** Dự báo nhu cầu bán hàng cho từng dòng xe (SKU) theo tháng, sử dụng mô hình Machine Learning (LightGBM/XGBoost/CatBoost) kết hợp các Baseline kinh điển.
- **Track 2:** Phân bổ dự báo SKU xuống mức độ Màu sắc (Color/Variant) nhằm tối ưu quy trình sơn tĩnh điện, đồng thời phát hiện rủi ro tồn kho (Slow-moving inventory).
- **Track 3:** Phân tích hành vi đại lý (Dealer Analytics) qua mô hình RFM Scoring, dự báo xác suất phát sinh đơn hàng (Churn Risk) và đưa ra các đề xuất hành động tiếp thị cụ thể.

---

## 2. Luồng Thực Thi (End-to-End Pipeline)

Bộ máy thực thi được đặt trong thư mục `implement/` và điều phối bởi `run_end_to_end.py`. Quá trình gồm 3 giai đoạn:

* **Phase 1: Data Foundation (`phase1c`)**
  * Làm sạch và chuẩn hóa danh mục sản phẩm (Product Master Data).
  * Gom nhóm và tổng hợp doanh thu theo các chiều thời gian (Tháng/Tuần).
* **Phase 2: Feature Store (`phase2a`)**
  * Thiết kế đặc trưng (Feature Engineering): Lag 1M-12M, Động lượng (Momentum), Mã hóa chu kỳ (Cyclical Time).
  * Căn chỉnh dữ liệu (Alignment) để ghép nối chuẩn xác giữa tập Huấn luyện (Train) và tập Tương lai (Future).
* **Phase 3: Modeling & Forecasting (`phase3`)**
  * Data Audit tự động.
  * Tính toán Core Baselines và Group-Share.
  * Huấn luyện mô hình Machine Learning.
  * Phân bổ Track 2 (Color Forecast).
  * Chấm điểm và phân loại đại lý Track 3.

---

## 3. Hướng Dẫn Sử Dụng (How to Run)

Repository sử dụng 1 file điều phối duy nhất. Đứng tại thư mục gốc của project, mở terminal/powershell và chạy:

```bash
# 1. Chạy thử nghiệm (Dry-run) - Kiểm tra cấu trúc pipeline và file input mà không chạy script
python implement/run_end_to_end.py --dry-run

# 2. Chạy toàn bộ Pipeline (End-to-End) - Đòi hỏi quyền overwrite output
python implement/run_end_to_end.py --allow-modeling --allow-overwrite
```

**Lưu ý:** Flag `--allow-overwrite` là cơ chế an toàn để ngăn việc vô tình ghi đè (overwrite) các kết quả dự báo đang tốt trong thư mục `outputs/modeling/`.

---

## 4. Đầu Ra (Outputs)

Toàn bộ báo cáo và kết quả được lưu minh bạch tại thư mục `outputs/`:

* **`outputs/modeling/`**: (Single Source of Truth cho các Track)
  * `phase3_group_share_forecast_q2_2026.csv` (Dự báo an toàn Track 1)
  * `phase3c_ml_forecast_q2_2026.csv` (Dự báo Machine Learning Track 1)
  * `phase3_color_forecast_q2_2026.csv` (Track 2)
  * `phase3_dealer_priority_ranking_q2_2026.csv` (Track 3)
  * Cùng các file `.md` báo cáo tổng kết (Executive Summaries) cho từng Track.
* **`outputs/audit/`**:
  * Các báo cáo kiểm định chất lượng (Data Audit), theo dõi rò rỉ dữ liệu (Leakage check).

---

## 5. Cấu trúc Cây Thư mục (File Tree Structure)

Cấu trúc thư mục được dọn dẹp gọn gàng, chia tách rõ ràng trách nhiệm của từng component:

```text
Data_Explorers_Vong_2/
├── archive/                     # Nơi lưu trữ các scripts và artifacts cũ, nháp
│   ├── debug_notes/
│   ├── debug_scripts/
│   └── legacy_scripts/
├── data/                        # Quản lý vòng đời dữ liệu
│   ├── features/                # File ma trận đặc trưng (.parquet) cho ML
│   ├── interim/                 # Dữ liệu sạch trung gian
│   ├── metadata/                # Bảng tham chiếu (Product Map, Feature Registry)
│   └── raw/                     # [BẤT BIẾN] Chứa các CSV gốc từ Data Explorers
├── implement/                   # Mã nguồn thực thi Pipeline
│   ├── phase1_data_foundation/  # Scripts gom nhóm, làm sạch
│   ├── phase2_feature_store/    # Scripts tạo Lag, RFM, Alignment
│   ├── phase3_modeling/         # Scripts dự báo Track 1, 2, 3
│   ├── shared/                  # Config, utils dùng chung
│   └── run_end_to_end.py        # Pipeline Orchestrator (Script điều phối)
├── outputs/                     # Thành phẩm cuối cùng
│   ├── audit/                   # Báo cáo kiểm định chất lượng dữ liệu
│   └── modeling/                # Kết quả dự báo (CSVs) và báo cáo kinh doanh (MDs)
├── .gitignore                   # Thiết lập chặn các file pycache, env, catboost_info
├── requirements.txt             # Danh sách thư viện Python (Dependencies)
├── IMPLEMENTATION_BLUEPRINT.md  # Kế hoạch thiết kế hệ thống gốc
├── REPO_ARCHITECTURE.md         # Giải thích chi tiết Data Lineage và Cấu trúc
└── README.md                    # (Bạn đang đọc file này)
```

> **Tham khảo thêm:** Để tìm hiểu sâu hơn về luồng chuyển hóa dữ liệu (Data Lineage) giữa các file, vui lòng đọc [REPO_ARCHITECTURE.md](REPO_ARCHITECTURE.md).
