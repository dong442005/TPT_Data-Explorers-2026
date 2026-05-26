# 📊 TNBike Data Analytics - Data Explorers Vòng 2

Chào mừng các thành viên team **Data Explorers**! Đây là repository lưu trữ toàn bộ mã nguồn ETL, phân tích thống kê (EDA) và dữ liệu Dashboard cho vòng 2 cuộc thi Data Explorers 2026.

Tài liệu này hướng dẫn cách cài đặt môi trường, quy trình chạy pipeline làm sạch dữ liệu và phân định rõ **ai cần làm gì và để file ở đâu** để tránh xung đột code (conflict Git).

---

## 1. Cấu Trúc Repository Chuẩn (Quy định vị trí lưu file)

Cả nhóm thống nhất lưu trữ các tệp tin mới phát sinh theo đúng cấu trúc dưới đây. 

> [!NOTE]
> Các thư mục đánh dấu `[Không commit]` sẽ ở trạng thái trống rỗng trên GitHub (chỉ chứa file `.gitkeep` ẩn). Mỗi thành viên khi clone repo về máy phải tự nạp dữ liệu cục bộ theo hướng dẫn bên dưới.

```text
tnbike-analytics-project/
├── data/                       # [Không commit] Chứa dữ liệu
│   ├── raw/                    # [Không commit] Chứa tệp zip của BTC
│   │   └── emails/             # [Không commit] Bạn cần tự giải nén các file .eml hóa đơn vào đây
│   └── processed/              # [Không commit] Chứa file processed_data.json và processed_data_clean.json
│
├── database/                   # Quản lý SQL & Database
│   ├── 01_create_tables.sql    # File tạo bảng ban đầu (DDL của BTC)
│   ├── 02_import_data.sql      # File nạp dữ liệu lịch sử năm 2025 (Seed của BTC)
│   ├── views/                  # Chứa các SQL tạo Views (v_rfm_analysis, v_bcg_matrix,...)
│   └── patches/                # Chứa các bản vá sửa lỗi database thô
│       ├── db_data_quality_patch.sql   # Vá lỗi font, màu HP/Batman, gộp màu chuẩn
│       └── geo_clean_patch.sql         # Làm sạch địa lý tỉnh thành, map vùng miền
│
├── notebooks/                  # Nơi làm việc của các thành viên Phân Tích (EDA)
│   ├── 01_eda_rfm_analysis.ipynb       # Thử nghiệm tính điểm RFM, vẽ phân phối
│   ├── 02_database_quality_audit.ipynb # Nhật ký audit phát hiện các lỗi dữ liệu
│   └── 03_sales_forecasting.ipynb      # Thử nghiệm huấn luyện mô hình dự báo
│
├── src/                        # Thư mục mã nguồn chính (Production Python Code)
│   ├── utils/                  # Thư mục chứa code helper (clean text, clean money...)
│   ├── extract_validate.py     # ETL - E: Parse mail & PDF hóa đơn tháng 3/2026 -> JSON
│   ├── normalize.py            # ETL - T: Chuẩn hóa màu sắc, đơn vị, map dòng xe trên JSON
│   ├── load_to_database.py     # ETL - L: Nạp JSON sạch vào PostgreSQL và cập nhật fact_sales
│   ├── eda/                    # File code EDA chạy tự động (eda_rfm.py)
│   └── models/                 # Code huấn luyện và chạy mô hình dự báo (train.py, predict.py)
│
├── models/                     # [Không commit] Lưu file binary của mô hình đã train (.pkl)
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
    *   Không sửa chay trên database local. Hãy viết câu lệnh SQL `UPDATE` bổ sung vào tệp [database/patches/db_data_quality_patch.sql](file:///d:/NPD/V2_DataExplore/TPT_Data-Explorers-2026/database/patches/db_data_quality_patch.sql) hoặc [database/patches/geo_clean_patch.sql](file:///d:/NPD/V2_DataExplore/TPT_Data-Explorers-2026/database/patches/geo_clean_patch.sql) để cả nhóm cùng chạy đồng bộ.
*   **Nếu bạn viết thêm DAX Measure mới trên Power BI**:
    *   Copy công thức DAX đó và lưu lại vào tệp `bi/dax/measures.dax` để backup và cả nhóm cùng tham khảo giải thuật.
*   **Nếu bạn viết tài liệu, báo cáo hoặc làm slide thuyết trình**:
    *   Lưu trữ tất cả tài liệu, hình ảnh minh họa báo cáo vào thư mục `docs/`.

---

## 3. Quy Trình Chạy Pipeline Dữ Liệu Sạch (Từ A - Z)

Khi bắt đầu làm việc trên máy mới hoặc muốn reset lại dữ liệu sạch 100%, hãy thực hiện theo đúng 7 bước dưới đây:

### Bước 1: Cài đặt thư viện Python
Mở Terminal tại thư mục gốc của dự án và cài đặt các thư viện:
*(Cài thủ công các thư viện: `psycopg2`, `pdfplumber`, `pandas`)*.

### Bước 2: Trích xuất dữ liệu hóa đơn tháng 3/2026
Đặt các tệp `.eml` hóa đơn tháng 3 vào đường dẫn `data/raw/emails/` (hoặc cấu hình lại `FOLDER_PATH` trong code). Sau đó chạy:
```bash
python src/extract_validate.py
```
*Script sẽ tự động sửa lỗi lệch font mã hóa tiếng Việt từ PDF và tạo ra file trung gian tại `data/processed/processed_data.json`.*

### Bước 3: Chuẩn hóa dữ liệu thô bằng Python
Chạy script chuẩn hóa để tự động làm sạch màu sắc (sửa lỗi màu Cam), đơn vị tính và ánh xạ mã dòng xe:
```bash
python src/normalize.py
```
*Script sẽ kết nối trực tiếp database lấy dòng sản phẩm hoạt động và xuất ra file JSON sạch tại `data/processed/processed_data_clean.json`.*

### Bước 4: Khởi tạo Database lịch sử
1. Chạy file SQL tạo cấu trúc bảng (`01_create_tables.sql`) và file nạp dữ liệu gốc 2025 (`02_import_data.sql`) của BTC trong DBeaver/pgAdmin.

### Bước 5: Thực thi các bản vá sửa lỗi Database (SQL Patches)
1. Chạy bản vá làm sạch SKU lịch sử: thực thi file [database/patches/db_data_quality_patch.sql](file:///d:/NPD/V2_DataExplore/TPT_Data-Explorers-2026/database/patches/db_data_quality_patch.sql) để tự động chuẩn hóa viết hoa, sửa lỗi màu `HP`, sửa 18 dòng sản phẩm bị lỗi font trong dữ liệu lịch sử.
2. Chạy bản vá làm sạch địa lý: thực thi file [database/patches/geo_clean_patch.sql](file:///d:/NPD/V2_DataExplore/TPT_Data-Explorers-2026/database/patches/geo_clean_patch.sql) để seed bảng mapping và đồng bộ hóa thông tin tỉnh thành sạch cho `customer` và `fact_sales`.

### Bước 6: Nạp dữ liệu tháng 3/2026 sạch vào Database
Chạy file nạp dữ liệu từ file JSON sạch đã được chuẩn hóa ở Bước 3 vào PostgreSQL:
```bash
python src/load_to_database.py
```
*Dữ liệu mới sẽ tự động được đồng bộ, liên kết với các bảng danh mục đã làm sạch và đẩy vào bảng `fact_sales`.*

### Bước 7: Mở Power BI và Refresh
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

---

## 6. Hướng Dẫn Tự Setup Chi Tiết Cho Teammates Mới (First-time Local Setup Guide)

Khi một thành viên mới clone dự án từ GitHub về máy cá nhân, một số thư mục chứa dữ liệu và mô hình sẽ bị trống hoàn toàn (do đã được định nghĩa trong `.gitignore`). Hãy làm theo các bước dưới đây để tự thiết lập môi trường chạy cục bộ:

### Bước 1: Chuẩn bị dữ liệu hóa đơn thô (Raw Emails)
1. Tải tệp zip đề bài của BTC về máy: `Đề thi và Dữ liệu-20260501T154831Z-3-001.zip`.
2. Mở tệp zip, đi vào thư mục con và giải nén tệp `Emails & Files.zip`.
3. Kéo toàn bộ các file `.eml` (hóa đơn tháng 3) thả vào thư mục trống **`data/raw/emails/`** trong dự án của bạn.

### Bước 2: Thiết lập kết nối Cơ sở dữ liệu (PostgreSQL)
1. Mở phần mềm PostgreSQL Client (pgAdmin 4 hoặc DBeaver).
2. Tạo một database mới tên là `tnbike_db` (hoặc tên tùy chọn của bạn).
3. Mở và chạy lần lượt 4 tệp SQL theo đúng thứ tự:
   *   📄 **`database/01_create_tables.sql`**: Tạo các bảng trống.
   *   📄 **`database/02_import_data.sql`**: Nạp dữ liệu lịch sử năm 2025.
   *   📄 **`database/patches/db_data_quality_patch.sql`**: Sửa lỗi thô dữ liệu lịch sử và chuẩn hóa màu sắc.
   *   📄 **`database/patches/geo_clean_patch.sql`**: Sửa lỗi địa lý, gộp vùng miền và đồng bộ dữ liệu khách hàng.

### Bước 3: Cấu hình thông tin đăng nhập Database trong Code
Mở file `src/load_to_database.py` (và các file SQL patch khác), chỉnh sửa lại cấu hình kết nối `DB_CONFIG` ở phần đầu file cho đúng với thông tin đăng nhập PostgreSQL local của máy bạn:
```python
DB_CONFIG = {
    "dbname": "tnbike_db",
    "user": "postgres",
    "password": "YOUR_LOCAL_PASSWORD_HERE",  # Thay mật khẩu máy của bạn vào đây
    "host": "localhost",
    "port": "5432",
}
```

### Bước 4: Chạy Pipeline để hoàn tất dữ liệu
Mở Terminal của VS Code tại thư mục dự án và chạy lần lượt 3 lệnh sau:
```bash
# 1. Trích xuất dữ liệu hóa đơn mới tháng 3/2026 thành file JSON thô
python src/extract_validate.py

# 2. Chuẩn hóa màu sắc, dòng sản phẩm trên JSON để ra file JSON sạch
python src/normalize.py

# 3. Nạp dữ liệu tháng 3 đã làm sạch vào database PostgreSQL
python src/load_to_database.py
```

*Lúc này, cơ sở dữ liệu trên máy của bạn đã được cập nhật đầy đủ và sạch đẹp 100% giống các thành viên khác.*
