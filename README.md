# 📊 TNBike Data Analytics — Data Explorers Vòng 2 (2026)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1.svg?logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811.svg?logo=powerbi&logoColor=black)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-XGBoost_|_CatBoost-FF6F00.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)

Đây là repository chính thức của đội thi **Data Explorers** tham dự Vòng 2 cuộc thi Data Explorers 2026. Dự án tập trung giải quyết bài toán tối ưu hóa chuỗi cung ứng, dự báo bán hàng và phân tích hành vi đại lý cho chuỗi xe đạp TNBike thông qua một **Hệ sinh thái Dữ liệu Toàn diện (End-to-End Data Pipeline)**.

Tài liệu này cung cấp cái nhìn bao quát về kiến trúc hệ thống, các luồng thuật toán cốt lõi, và hướng dẫn chi tiết để Ban Tổ Chức, Ban Giám Khảo có thể thiết lập môi trường và tái tạo kết quả một cách dễ dàng.

---

## 🌟 Điểm Nổi Bật của Giải Pháp (Key Highlights)

- **Tự động hóa ETL 100%:** Trích xuất, chuẩn hóa và nạp (Load) dữ liệu từ hàng ngàn hóa đơn định dạng PDF/Email hoàn toàn tự động vào CSDL. Xử lý triệt để các ngoại lệ như lỗi font chữ, sai tên sản phẩm, địa danh bị sai lệch.
- **Hệ thống Dự báo Machine Learning Tiên tiến (Track 1 & 2):** Xây dựng Pipeline Dự báo (từ Feature Store đến Modeling) sử dụng các thuật toán Gradient Boosting (XGBoost, CatBoost). Dự báo chính xác nhu cầu bán hàng tới cấp độ Dòng xe (SKU) và phân bổ theo Màu sắc (Variant), trực tiếp giải quyết bài toán tối ưu dây chuyền sơn tĩnh điện và quản lý tồn kho.
- **Phân tích Cấp độ Đại lý chuyên sâu (Track 3):** Áp dụng mô hình RFM đặc thù cho B2B, thiết lập ma trận sức khỏe đại lý, dự báo rủi ro rời bỏ (Churn Risk) và đưa ra chiến lược phân bổ nguồn lực Marketing.
- **Trợ lý Kinh doanh AI (LLM Chatbot):** Đột phá với giao diện Chatbot bằng Streamlit cho phép Ban Giám Đốc truy vấn linh hoạt cơ sở dữ liệu và lấy thông tin chi tiết (Insights) trực tiếp bằng Tiếng Việt tự nhiên.
- **Báo cáo BI & Kỹ thuật Chuẩn mực:** Tích hợp hệ thống 6 trang Power BI Dashboard tương tác thời gian thực. Toàn bộ thiết kế kỹ thuật, phương pháp luận, và kiểm định rò rỉ dữ liệu (Data Leakage) được tự động kết xuất thành **Technical Report** theo chuẩn học thuật (LaTeX).

---

## 📖 Mục Lục
1. [Kiến Trúc Hệ Thống (System Architecture)](#1-kiến-trúc-hệ-thống-system-architecture)
2. [Cấu Trúc Dự Án (Project Structure)](#2-cấu-trúc-dự-án-project-structure)
3. [Sơ Đồ Cơ Sở Dữ Liệu (Database Schema)](#3-sơ-đồ-cơ-sở-dữ-liệu-database-schema)
4. [Hệ Thống Dự Báo Machine Learning](#4-hệ-thống-dự-báo-machine-learning-track-1-2-3)
5. [Trợ Lý Kinh Doanh AI](#5-trợ-lý-kinh-doanh-ai-llm-chatbot)
6. [Hệ Thống Dashboard Quản Trị (Power BI)](#6-hệ-thống-dashboard-quản-trị-power-bi)
7. [Báo Cáo Kỹ Thuật (Technical Report)](#7-báo-cáo-kỹ-thuật-technical-report)
8. [Hướng Dẫn Cài Đặt & Vận Hành](#8-hướng-dẫn-cài-đặt--vận-hành-getting-started)
9. [Quy Trình Phát Triển (Workflow)](#9-quy-trình-phát-triển-development-workflow)
10. [Tài Liệu Tham Khảo](#10-tài-liệu-tham-khảo--đầu-ra-báo-cáo)

---

## 1. Kiến Trúc Hệ Thống (System Architecture)

Dự án tuân theo kiến trúc luồng dữ liệu một chiều (One-way Data Flow), đảm bảo dữ liệu thô (Raw) luôn bất biến và mọi bước biến đổi đều có thể theo dõi (Lineage).

| Lớp (Layer) | Công nghệ sử dụng | Chức năng chính |
|---|---|---|
| **Data Ingestion (ETL)** | Python (`pdfplumber`, `pandas`) | Đọc file `.eml`, PDF hóa đơn, parse thông tin cấu trúc, làm sạch, mapping dữ liệu rác. |
| **Data Storage (DWH)** | PostgreSQL | Lưu trữ lược đồ Relational (Snowflake schema) và Bảng Fact phẳng (Denormalized) cho BI. |
| **Feature Store & ML** | Python (`scikit-learn`, `xgboost`) | Feature Engineering (Lag, Momentum, RFM), xử lý Data Leakage, Train và Predict. |
| **Business Intelligence** | Power BI | Kết nối DirectQuery/Import từ DB, xây dựng 6 trang Dashboard trực quan. |
| **AI Assistant** | Streamlit, LLM APIs | Giao diện Chatbot chuyển ngữ Tự nhiên sang SQL để Query Database. |

---

## 2. Cấu Trúc Dự Án (Project Structure)

> [!NOTE]
> Để tuân thủ các quy tắc bảo mật và tối ưu hóa không gian, một số thư mục chứa dữ liệu thô hoặc file binary (đánh dấu `[Không commit]`) sẽ không có sẵn trực tiếp trên kho lưu trữ. Vui lòng chạy luồng Pipeline để khởi tạo tự động.

```text
TPT_Data-Explorers-2026/
│
├── app.py                              # Giao diện Frontend Streamlit cho LLM Chatbot
├── README.md                           # Tài liệu tổng quan dự án
│
├── database/                           # Quản lý cấu trúc và bản vá SQL
│   ├── 01_create_tables.sql            # DDL: Tạo schema tnbike & toàn bộ bảng
│   ├── 02_import_data.sql              # Seed: Nạp dữ liệu lịch sử T1-T3/2025
│   ├── patches/                        # Các bản vá lỗi dữ liệu (sửa font, chuẩn hóa Tỉnh/Thành)
│   └── views/                          # SQL định nghĩa Views cho Power BI
│
├── src/                                # Mã nguồn Python (Core Pipeline)
│   ├── extract_validate.py             # [ETL-E] Trích xuất dữ liệu từ PDF/Email
│   ├── normalize.py                    # [ETL-T] Chuẩn hóa và Mapping danh mục
│   ├── load_to_database.py             # [ETL-L] Nạp dữ liệu sạch vào PostgreSQL
│   ├── business_assistant.py           # Backend lõi của Chatbot AI
│   ├── models/                         # [Cốt lõi] Mã nguồn Machine Learning & Feature Store
│   ├── eda/                            # Các Script kiểm tra phân phối dữ liệu
│   └── utils/                          # Các hàm tiện ích dùng chung
│
├── outputs/                            # Kết quả sinh tự động từ ML Pipeline
│   ├── audit/                          # Báo cáo kiểm định chất lượng & Data Leakage
│   └── modeling/                       # File dự báo (CSV) & Báo cáo quản trị (Markdown)
│
├── docs/                               # Tài liệu học thuật & kỹ thuật
│   ├── reports/                        # Nơi chứa Báo cáo Kỹ thuật PDF (Technical Report)
│   ├── forecasting/                    # Các tài liệu phân tích sâu về dự báo
│   ├── dashboard_powerbi_guide.md      # Thiết kế và DAX cho Power BI
│   └── rfm_scoring_analysis.md         # Luận chứng phương pháp chấm điểm RFM
│
├── bi/                                 # File Power BI (`.pbix`) & file lưu trữ DAX
│   └── dax/
│       └── TPT_Dashboard_28_5 (4).pbix # File Power BI Dashboard chính thức
├── notebooks/                          # [Không commit] Phân tích thử nghiệm (EDA)
├── models/                             # [Không commit] File lưu trữ trọng số mô hình (.pkl)
└── data/                               # [Không commit] Dữ liệu thô (`raw/`) và sạch (`processed/`)
```

---

## 3. Sơ Đồ Cơ Sở Dữ Liệu (Database Schema)

Dữ liệu được tổ chức tại schema `tnbike` trong PostgreSQL. Bảng trung tâm là `fact_sales` - được thiết kế phẳng hóa (denormalized) để tối ưu truy vấn cho Power BI và Machine Learning.

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

**Các SQL Views đã tối ưu hóa cho BI (`database/views/powerbi_views.sql`):**
| View | Mục đích |
|---|---|
| `tnbike.v_rfm_analysis` | Chấm điểm RFM, phân 8 nhóm đại lý B2B |
| `tnbike.v_bcg_matrix` | Ma trận BCG dòng xe (100% doanh thu, gồm nhóm Chưa phân loại) |
| `tnbike.v_pipeline_status` | Thống kê trạng thái xử lý email (cho trang Vận hành) |
| `tnbike.v_data_quality_summary` | Audit nhanh lỗi dữ liệu (thiếu tỉnh, thiếu nhóm xe...) |

---

## 4. Hệ Thống Dự Báo Machine Learning (Track 1, 2, 3)

Phần này chứa toàn bộ mã nguồn, dữ liệu và báo cáo phân tích xây dựng hệ thống dự báo nhu cầu sản xuất và bán hàng cho chuỗi xe đạp Thống Nhất (Q2/2026).

### 4.1. Tổng Quan Dự Án ML (Project Overview)
**Các Track (Bài toán) được giải quyết:**
- **Track 1:** Dự báo nhu cầu bán hàng cho từng dòng xe (SKU) theo tháng, sử dụng mô hình Machine Learning (LightGBM/XGBoost/CatBoost) kết hợp các Baseline kinh điển.
- **Track 2:** Phân bổ dự báo SKU xuống mức độ Màu sắc (Color/Variant) nhằm tối ưu quy trình sơn tĩnh điện, đồng thời phát hiện rủi ro tồn kho (Slow-moving inventory).
- **Track 3:** Phân tích hành vi đại lý (Dealer Analytics) qua mô hình RFM Scoring, dự báo xác suất phát sinh đơn hàng (Churn Risk) và đưa ra các đề xuất hành động tiếp thị cụ thể.

### 4.2. Luồng Thực Thi (End-to-End Pipeline)
Bộ máy thực thi được đặt trong thư mục `src/models/forecasting/` và điều phối bởi `run_end_to_end.py`. Quá trình gồm 3 giai đoạn:
* **Phase 1: Data Foundation (`phase1c`)**: Làm sạch và chuẩn hóa danh mục sản phẩm. Tổng hợp doanh thu theo các chiều thời gian.
* **Phase 2: Feature Store (`phase2a`)**: Thiết kế đặc trưng (Feature Engineering): Lag 1M-12M, Động lượng (Momentum), Mã hóa chu kỳ. Căn chỉnh dữ liệu (Alignment) để ghép nối chuẩn xác giữa tập Huấn luyện (Train) và tập Tương lai (Future).
* **Phase 3: Modeling & Forecasting (`phase3`)**: Audit chất lượng tự động, tính toán Baselines, huấn luyện Machine Learning, phân bổ Track 2, và tính điểm rủi ro rời bỏ đại lý Track 3.

### 4.3. Cấu trúc Cây Thư mục Machine Learning
Cấu trúc thư mục được dọn dẹp gọn gàng, chia tách rõ ràng trách nhiệm của từng component:
```text
src/models/forecasting/          # Mã nguồn thực thi Pipeline Dự Báo
├── phase1_data_foundation/      # Scripts gom nhóm, làm sạch
├── phase2_feature_store/        # Scripts tạo Lag, RFM, Alignment
├── phase3_modeling/             # Scripts dự báo Track 1, 2, 3
├── shared/                      # Config, utils dùng chung
└── run_end_to_end.py            # Pipeline Orchestrator (Script điều phối)
```

---

## 5. Trợ Lý Kinh Doanh AI (LLM Chatbot)

Dự án có tích hợp một ứng dụng Chatbot AI đóng vai trò như một **Trợ lý Phân tích Dữ liệu (Data Query Engine)** dành cho cấp quản lý. Thay vì viết SQL phức tạp, người dùng có thể đặt câu hỏi bằng ngôn ngữ tự nhiên (Tiếng Việt) và AI sẽ tự động truy xuất cơ sở dữ liệu để trả lời.

**Thành phần chính:**
- `app.py`: Chứa giao diện người dùng (Frontend) được xây dựng bằng **Streamlit**, cung cấp giao diện chat tương tác.
- `src/business_assistant.py`: Lõi xử lý LLM (Backend) - phụ trách biên dịch câu hỏi tự nhiên thành truy vấn SQL chuẩn xác, thực thi trên PostgreSQL và tóm tắt kết quả.

---

## 6. Hệ Thống Dashboard Quản Trị (Power BI)

Hệ thống Dashboard được xây dựng trên Power BI, trực tiếp truy vấn dữ liệu từ PostgreSQL (DirectQuery/Import). Hệ thống gồm **6 trang báo cáo chuyên sâu** nhằm cung cấp cái nhìn toàn cảnh 360 độ về sức khỏe doanh nghiệp:

1. **Executive Overview (Tổng quan):** Theo dõi tức thời KPI doanh thu, sản lượng, số lượng đại lý và tỷ lệ tăng trưởng (MoM, YoY). Trực quan hóa phễu xử lý dữ liệu.
2. **Time Analysis (Phân tích Thời gian):** Đánh giá tính mùa vụ, biến động doanh thu theo quý/tháng.
3. **Product & BCG Matrix (Phân tích Sản phẩm):** Theo dõi hiệu quả của 265 SKU, sử dụng **Ma trận BCG** để phân loại dòng xe (Stars, Cash Cows, Dogs, Question Marks) dựa trên thị phần và tốc độ tăng trưởng.
4. **Dealer RFM (Phân tích Đại lý):** Trực quan hóa điểm số RFM, nhận diện đại lý có nguy cơ rời bỏ (Churn Risk), đại lý trung thành (Loyal) và nhóm VIP (Champions).
5. **Geographic (Phân tích Địa lý):** Bản đồ nhiệt phân bổ doanh thu theo tỉnh thành, làm nổi bật rủi ro tập trung doanh thu (Concentration Risk).
6. **Pipeline Operations (Vận hành Dữ liệu):** Theo dõi phễu xử lý dữ liệu ETL từ Email đến Database với tỷ lệ thành công 100%.

> 📊 **File Dashboard chính thức:** [`bi/dax/TPT_Dashboard_28_5 (4).pbix`](bi/dax/TPT_Dashboard_28_5%20(4).pbix)
> 💡 **Hướng dẫn đọc Dashboard & DAX:** Xem tại [`docs/dashboard_powerbi_guide.md`](docs/dashboard_powerbi_guide.md).

---

## 7. Báo Cáo Kỹ Thuật (Technical Report)

Dự án đính kèm một **Báo Cáo Kỹ Thuật chuẩn học thuật (Technical Report)** được tự động sinh ra dưới dạng PDF bằng LaTeX. Báo cáo này bao quát TOÀN BỘ tư duy phân tích của đội thi, bao gồm:

- **Data Quality & Lineage:** Minh bạch hóa nguồn dữ liệu, các vấn đề chất lượng (Data Quality Issues) và cách xử lý triệt để thông qua SQL Patches.
- **Thiết kế Feature Store:** Giải thích công thức toán học và logic kinh doanh đằng sau các biến số (Lag, Momentum, Cyclical Features).
- **Data Leakage Prevention:** Các chiến lược kỹ thuật ngăn chặn rò rỉ dữ liệu (Data Leakage) nghiêm ngặt để đảm bảo mô hình phản ánh đúng thực tế.
- **Đánh giá Mô hình (Model Evaluation):** Báo cáo so sánh hiệu năng của XGBoost, CatBoost và Baseline (thông qua MAPE, RMSE).
- **Chiến lược Kinh doanh:** Từ Data đến Insight — Đưa ra các quyết định hành động thực tiễn (Data-driven decisions) từ mô hình dự báo và hệ thống phân khúc đại lý.

> 📄 **Link tải báo cáo:** [`docs/reports/technical_report/technical_report_en.pdf`](docs/reports/technical_report/technical_report_en.pdf)

---

## 8. Hướng Dẫn Cài Đặt & Vận Hành (Getting Started)

Quy trình dưới đây hướng dẫn tái tạo lại kết quả của dự án từ con số không.

### Bước 1: Môi trường & Database
Cài đặt thư viện: `pip install psycopg2-binary pdfplumber pandas scikit-learn xgboost streamlit`
Tạo database `tnbike_db` trên PostgreSQL local.

### Bước 2: Nạp dữ liệu cơ sở
Chạy lần lượt 2 file SQL trong công cụ như DBeaver/pgAdmin:
1. `database/01_create_tables.sql` (Tạo cấu trúc)
2. `database/02_import_data.sql` (Nạp dữ liệu lịch sử)

Cấu hình mật khẩu DB tại block `DB_CONFIG` trong các mã nguồn Python (`src/load_to_database.py`, v.v.).

### Bước 3: Chạy ETL Pipeline (Trích xuất Hóa đơn T3/2026)
Đặt các hóa đơn `.eml` vào thư mục `data/raw/emails/`. Chạy:
```bash
python src/extract_validate.py  # [E] Extract
python src/normalize.py         # [T] Transform
python src/load_to_database.py  # [L] Load
```

### Bước 4: Chạy SQL Patches làm sạch số liệu
```bash
# Trong DBeaver / pgAdmin, chạy lần lượt:
3. database/patches/db_data_quality_patch.sql  # Sửa lỗi font, màu sắc
4. database/patches/geo_clean_patch_final.sql  # Làm sạch địa lý, tạo bảng province_clean
```
> [!IMPORTANT]
> Chạy `geo_clean_patch_final.sql` **sau** `db_data_quality_patch.sql`. File này tạo bảng `province_clean` mà các Views BI phụ thuộc vào.

### Bước 5: Tạo Views cho Power BI & Kết nối BI
- Chạy file `database/views/powerbi_views.sql` trong DBeaver/pgAdmin.
- Mở file Dashboard chính thức tại `bi/dax/TPT_Dashboard_28_5 (4).pbix`, thiết lập Host: `localhost`, Database: `tnbike_db`, và bấm **Refresh**.

### Bước 6: Chạy Pipeline Machine Learning (End-to-End)
```bash
# Chạy thử nghiệm (Dry-run) kiểm tra cấu trúc
python src/models/forecasting/run_end_to_end.py --dry-run

# Chạy toàn bộ Pipeline thực tế (huấn luyện và dự báo)
python src/models/forecasting/run_end_to_end.py --allow-modeling --allow-overwrite
```

### Bước 7: Khởi chạy Trợ lý AI (Chatbot)
```bash
streamlit run app.py
```
*(Trình duyệt sẽ tự động mở tại địa chỉ `http://localhost:8501`)*

---

## 9. Quy Trình Phát Triển (Development Workflow)

> [!IMPORTANT]
> **Tổ Chức Không Gian Làm Việc:** Đội thi phân chia trách nhiệm rành mạch: EDA ở `notebooks/`, vá lỗi Data ở `database/patches/`, logic BI ở `bi/dax/`, và tài liệu học thuật ở `docs/`.

Để đảm bảo tính nhất quán và chất lượng mã nguồn, đội thi đã áp dụng nghiêm ngặt các tiêu chuẩn trong công nghệ phần mềm:

- **Chiến lược phân nhánh:** Nhánh `main` luôn được giữ ở trạng thái ổn định nhất (Production-ready). Các tính năng mới phát triển độc lập trên các nhánh phụ (ví dụ: `feature/pipeline-integration`, `fix/geo-clean-fk-check`) và chỉ được hợp nhất qua Pull Request sau khi qua kiểm duyệt.
- **Quy ước đặt tên Commit (Conventional Commits):**
  - `feat:`: Phát triển tính năng mới
  - `fix:`: Sửa lỗi hệ thống
  - `docs:`: Cập nhật tài liệu
  - `chore:`: Cấu hình, dọn dẹp
  - `sql:`: Thay đổi cấu trúc CSDL

---

## 10. Tài Liệu Tham Khảo & Đầu Ra Báo Cáo

Tất cả các kết quả và chứng minh khoa học được tự động kết xuất minh bạch:
- 📄 **Báo Cáo Kỹ Thuật Chính Thức:** [`docs/reports/technical_report_en.pdf`](docs/reports/technical_report/technical_report_en.pdf) (Thuyết minh phương pháp luận thiết kế, rò rỉ dữ liệu, kết quả).
- 📊 **Kết Quả Dự Báo (Outputs):** `outputs/modeling/` (Chứa CSV điểm RFM, phân bổ màu sắc, dự báo SKU).
- 📈 **Báo Cáo Kiểm Định Dữ Liệu (Audit):** `outputs/audit/`
- 📑 **Hướng Dẫn Power BI:** [`docs/dashboard_powerbi_guide.md`](docs/dashboard_powerbi_guide.md)
- 🧠 **Phân Tích B2B RFM:** [`docs/rfm_scoring_analysis.md`](docs/rfm_scoring_analysis.md)
- 🗺️ **Phân Tích Mapping SKU:** [`docs/product_line_mapping_analysis.md`](docs/product_line_mapping_analysis.md)
- 📐 **Kiến Trúc Data Lineage:** [`REPO_ARCHITECTURE.md`](REPO_ARCHITECTURE.md)
