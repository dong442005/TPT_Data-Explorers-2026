# 📊 TNBike Data Analytics - Data Explorers Vòng 2

Chào mừng các thành viên team **Data Explorers**! Đây là repository lưu trữ toàn bộ mã nguồn ETL, phân tích thống kê (EDA) và dữ liệu Dashboard cho vòng 2 cuộc thi Data Explorers 2026.

Tài liệu này hướng dẫn cách cài đặt môi trường, quy trình chạy pipeline làm sạch dữ liệu và phân định rõ **ai cần làm gì và để file ở đâu** để tránh xung đột code (conflict Git).

---

## 1. Cấu Trúc Repository Chuẩn (Quy định vị trí lưu file)

Cả nhóm thống nhất lưu trữ các tệp tin mới phát sinh theo đúng cấu trúc dưới đây:

```text
tnbike-analytics-project/
├── data/                       # [KHÔNG COMMIT LÊN GIT] Chứa dữ liệu
│   ├── raw/                    # Hóa đơn gốc (.eml, .pdf), đề thi và file zip của BTC
│   └── processed/              # File dữ liệu trung gian sau khi parse (processed_data.json)
│
├── database/                   # Quản lý SQL & Database
│   ├── 01_schema.sql           # File tạo bảng ban đầu (DDL của BTC)
│   ├── 02_seed.sql             # File nạp dữ liệu lịch sử năm 2025 (Seed của BTC)
│   ├── views/                  # Chứa các SQL tạo Views (v_rfm_analysis, v_bcg_matrix,...)
│   └── patches/                # Chứa các bản vá sửa lỗi database thô
│       └── db_data_quality_patch.sql   # Vá lỗi font, màu HP/Batman, gộp màu chuẩn
│
├── notebooks/                  # Nơi làm việc của các thành viên Phân Tích (EDA)
│   ├── 01_eda_rfm_analysis.ipynb       # Thử nghiệm tính điểm RFM, vẽ phân phối
│   ├── 02_database_quality_audit.ipynb # Nhật ký audit phát hiện các lỗi dữ liệu
│   └── 03_sales_forecasting.ipynb      # Thử nghiệm huấn luyện mô hình dự báo
│
├── src/                        # Thư mục mã nguồn chính (Production Python Code)
│   ├── utils/                  # Thư mục chứa code helper (clean text, clean money...)
│   ├── extract_validate.py     # ETL - E: Parse mail & PDF hóa đơn tháng 3/2026 -> JSON
│   ├── load_to_database.py     # ETL - L: Nạp JSON vào PostgreSQL và cập nhật fact_sales
│   ├── eda/                    # File code EDA chạy tự động (eda_rfm.py)
│   └── models/                 # Code huấn luyện và chạy mô hình dự báo (train.py, predict.py)
│
├── models/                     # [KHÔNG COMMIT LÊN GIT] Lưu file binary của mô hình đã train (.pkl)
│
├── bi/                         # Thư mục lưu trữ thiết kế Dashboard
│   ├── tnbike_dashboard.pbix   # File Power BI Desktop chính
│   └── dax/
│       └── measures.dax        # File backup các câu lệnh DAX đã viết
│
└── docs/                       # Thư mục lưu báo cáo thuyết minh
    ├── dashboard_powerbi_guide.md      # Hướng dẫn thiết kế các trang Power BI
    ├── rfm_scoring_analysis.md         # Thuyết minh chấm điểm RFM
    └── final_submission_report.md      # Báo cáo 5+ Insights để nộp bài
```

---

## 2. Hướng Dẫn Dành Cho Từng Vai Trò (Teammates Workflow)

> [!IMPORTANT]
> Để tránh xung đột git, vui lòng tuân thủ quy tắc **"Làm gì - Để ở đó"**:

*   **Nếu bạn cần phân tích dữ liệu, vẽ biểu đồ nháp, hoặc audit tìm lỗi**:
    *   Hãy tạo file Jupyter Notebook đặt trong thư mục `notebooks/`. Đặt tên file theo chuẩn: `[STT]_[mục_tiêu].ipynb` (Ví dụ: `04_forecasting_experiment.ipynb`).
*   **Nếu bạn phát hiện ra lỗi dữ liệu mới trong database và cần sửa**:
    *   Không sửa chay trên database local. Hãy viết câu lệnh SQL `UPDATE` bổ sung vào tệp [database/patches/db_data_quality_patch.sql](file:///d:/NPD/V2_DataExplore/Data_Explorers_Vong_2/database/patches/db_data_quality_patch.sql) để cả nhóm cùng chạy đồng bộ.
*   **Nếu bạn viết thêm DAX Measure mới trên Power BI**:
    *   Copy công thức DAX đó và lưu lại vào tệp `bi/dax/measures.dax` để backup và cả nhóm cùng tham khảo giải thuật.
*   **Nếu bạn viết tài liệu, báo cáo hoặc làm slide thuyết trình**:
    *   Lưu trữ tất cả tài liệu, hình ảnh minh họa báo cáo vào thư mục `docs/`.

---

## 3. Quy Trình Chạy Pipeline Dữ Liệu Sạch (Từ A - Z)

Khi bắt đầu làm việc trên máy mới hoặc muốn reset lại dữ liệu sạch 100%, hãy thực hiện theo đúng 4 bước dưới đây:

### Bước 1: Cài đặt thư viện Python
Mở Terminal tại thư mục gốc của dự án và cài đặt:
```bash
pip install -r requirements.txt
```
*(Nếu chưa có file requirements.txt, hãy cài thủ công các thư viện: `psycopg2`, `pdfplumber`)*.

### Bước 2: Trích xuất dữ liệu hóa đơn tháng 3/2026
Đặt các tệp `.eml` hóa đơn tháng 3 vào đường dẫn `data/raw/emails/` (hoặc cấu hình lại `FOLDER_PATH` trong code). Sau đó chạy:
```bash
python src/extract_validate.py
```
*Script sẽ tự động sửa lỗi lệch font mã hóa tiếng Việt từ PDF và tạo ra file trung gian sạch sẽ tại `data/processed/processed_data.json`.*

### Bước 3: Khởi tạo & Làm sạch Database lịch sử
1. Chạy file SQL tạo cấu trúc bảng (`01_schema.sql`) và file nạp dữ liệu gốc 2025 (`02_seed.sql` hoặc `02_import_data.sql`) của BTC trong DBeaver/pgAdmin.
2. Mở và thực thi toàn bộ file bản vá SQL làm sạch [database/patches/db_data_quality_patch.sql](file:///d:/NPD/V2_DataExplore/Data_Explorers_Vong_2/database/patches/db_data_quality_patch.sql) để tự động chuẩn hóa viết hoa, sửa lỗi màu `HP`, sửa 18 dòng sản phẩm bị lỗi font trong dữ liệu lịch sử.

### Bước 4: Nạp dữ liệu tháng 3/2026 sạch vào Database
Chạy file nạp dữ liệu từ file JSON sạch ở Bước 2 vào PostgreSQL:
```bash
python src/load_to_database.py
```
*Dữ liệu mới sẽ tự động được đồng bộ, liên kết với các bảng danh mục đã làm sạch và đẩy vào bảng `fact_sales`.*

### Bước 5: Mở Power BI và Refresh
Mở file `bi/tnbike_dashboard.pbix`, cấu hình kết nối PostgreSQL `localhost` và bấm **Refresh** để cập nhật toàn bộ số liệu sạch lên Dashboard.

---

## 4. Quy định Git Commit

Vui lòng viết Commit Message ngắn gọn, rõ nghĩa theo chuẩn Conventional Commits để giám khảo đánh giá cao tính chuyên nghiệp của team:
*   `feat: ...` (khi viết thêm tính năng mới, ví dụ: `feat(models): add sales forecast model using xgboost`)
*   `fix: ...` (khi sửa lỗi code hoặc lỗi dữ liệu, ví dụ: `fix(extract): resolve pdfplumber font encoding issues`)
*   `docs: ...` (khi viết tài liệu thuyết minh, ví dụ: `docs(rfm): add technical docs for rfm scoring`)
*   `chore: ...` (khi cấu hình hệ thống, dọn dẹp thư mục, ví dụ: `chore: setup .gitignore`)

---

## 5. Quy Trình Phối Hợp Nhóm Trên Git (Git Collaboration Workflow)

> [!WARNING]
> *   **Repository này là phiên bản nộp chính thức cho BTC.** Repo cũ trước đây chỉ dùng để làm nháp.
> *   **Tuyệt đối KHÔNG commit trực tiếp lên nhánh `main`.** Mọi thay đổi phải được làm trên nhánh phụ (feature branch) và gộp vào qua Pull Request (PR) sau khi đã chạy kiểm thử không có lỗi.

### Quy trình 5 bước khi nhận nhiệm vụ mới:

#### Bước 1: Cập nhật code mới nhất từ nhánh `main` trước khi làm
```bash
git checkout main
git pull origin main
```

#### Bước 2: Tạo nhánh mới để làm việc
Đặt tên nhánh theo cú pháp: `feature/[tên-nhiệm-vụ]` hoặc `fix/[tên-lỗi-cần-sửa]`.
```bash
# Ví dụ: Một bạn nhận nhiệm vụ "Huấn luyện mô hình dự báo doanh thu"
git checkout -b feature/sales-forecasting
```

#### Bước 3: Thực hiện code & đặt file đúng vị trí quy định
Theo ví dụ huấn luyện mô hình dự báo doanh thu:
1.  **Phác thảo & test thử nghiệm (Notebook)**: Code nháp, vẽ đồ thị phân tích lưu vào tệp: `notebooks/03_sales_forecasting.ipynb`.
2.  **Đóng gói code huấn luyện**: Viết hàm chuẩn hóa lưu vào: `src/models/train.py` và `src/models/predict.py`.
3.  **Lưu file model checkpoint**: File binary sau khi train (như `.pkl`, `.joblib`) được lưu vào thư mục `models/` (đã cấu hình bị ẩn khỏi Git để tránh làm nặng repo).

#### Bước 4: Stage file và Commit theo chuẩn
```bash
# Chỉ add những file code/notebook cần thiết
git add notebooks/03_sales_forecasting.ipynb src/models/

# Commit với thông điệp rõ nghĩa (Conventional Commit)
git commit -m "feat(models): train baseline sales forecasting model using XGBoost"
```

#### Bước 5: Đẩy nhánh lên GitHub và tạo Pull Request (PR)
```bash
git push -u origin feature/sales-forecasting
```
*Sau khi push, truy cập link repository trên GitHub, chọn **Create Pull Request**, tag nhóm vào review chéo và nhấn **Merge** vào nhánh `main` sau khi tất cả cùng đồng ý.*

