# 📊 Phân Tích Product → Line_ID Mapping (Cập nhật theo Business Rule)

> **Business Rule mới:** Không tạo `product_line` mới. Chỉ map những sản phẩm mà BTC **đã từng map biến thể tương tự** trong quá khứ (tại file import gốc), HOẶC những sản phẩm **chắc chắn đúng 100%**. Còn lại bắt buộc để `NULL`.

---

## 1. Đối Chiếu Dữ Liệu Gốc Của BTC (02_import_data.sql)

Để đảm bảo tính toàn vẹn, tôi đã quét lại toàn bộ dữ liệu import ban đầu của BTC. Kết quả cho thấy BTC đã **rất khắt khe** trong việc phân loại và cố tình để `NULL` rất nhiều sản phẩm không nằm chính xác trong catalog:

| Pattern / Dòng xe | Số SP trong import | Hành động của BTC lúc import | Phân tích Business |
|-------------------|-------------------|-----------------------------|--------------------|
| **Bubbles 20** | 4 SP | Đã map 2 SP vào `Xe Neo 20-02 Bubble`, để NULL 2 SP. | **✅ Đã có tiền lệ.** Việc BTC map 50% cho thấy "Bubbles 20" chính xác là alias của "Neo 20-02 Bubble". Việc sót 2 SP là lỗi data, ta **có thể map**. |
| **SK 20 / SK 24** | 6 SP | **Để NULL toàn bộ 100%.** | **❌ Không có tiền lệ.** Dù có thể là viết tắt của "Super", nhưng BTC cố tình không map. Chúng ta không được phép tự suy diễn SK = Super. |
| **Batwheels 12/16** | 5 SP | **Để NULL toàn bộ 100%.** | **❌ Không có tiền lệ.** Batwheels là series khác với Batman. Dù cùng IP DC, BTC không gộp chung. Chúng ta phải tôn trọng và để NULL. |
| **CPD 700C** | 4 SP | **Để NULL toàn bộ 100%.** | **❌ Không có tiền lệ.** Không được phép gộp CPD vào RPD. |
| **GRX 2.0 (ko có AT)** | 2 SP | **Để NULL 100%.** (Chỉ map GRX AT 27,5) | **❌ Không có tiền lệ.** Phiên bản GRX 2.0 thường khác với GRX AT 27,5_2.0. Phải để NULL. |
| **Super 26 S** | 4 SP | **Để NULL 100%.** (Chỉ map Super 26 thường)| **❌ Không có tiền lệ.** Chữ "S" thể hiện phiên bản khác. Phải để NULL. |
| **RPD 700C V5** | 3 SP | **Để NULL 100%.** (Chỉ map RPD thường) | **❌ Không có tiền lệ.** Phiên bản V5 BTC không gộp vào dòng thường. Phải để NULL. |
| **GN 2.0 700C** | 6 SP | **Để NULL 100%.** | **❌ Không có tiền lệ.** |
| **We Bare Bears** | 5 SP | **Để NULL 100%.** | **❌ Không có tiền lệ.** |

---

## 2. Đánh Giá Lại Các Mapping Rules Hiện Tại (Trong file SQL patch)

Dựa trên rule mới, chúng ta phải **loại bỏ (rollback)** các mapping suy diễn và chỉ giữ lại những mapping thỏa mãn 1 trong 2 điều kiện:
1. Trùng tên 100% (chắc chắn đúng).
2. BTC đã từng map biến thể tương tự.

### 🔴 Các Rules PHẢI BỎ (Trả về NULL)
Đây là các rule trước đây ta gộp vào vì thấy "gần giống", nhưng đối chiếu lại thì BTC đã từ chối gộp lúc import:

1. `SK 24` → KHÔNG map vào Super 24 (Trả về NULL)
2. `SK 20` → KHÔNG map vào TE Super 20 (Trả về NULL)
3. `Batwheels 16 / 12` → KHÔNG map vào Batman (Trả về NULL)
4. `CPD 700C` → KHÔNG map vào RPD 700C (Trả về NULL)
5. `GRX 2.0 / GRX 27.5` → KHÔNG map vào GRX AT 27,5_2.0 (Nếu thiếu chữ AT thì để NULL)
6. `Super 26 S` → KHÔNG map vào Super 26 (Trả về NULL)
7. `RPD 700C V5` → KHÔNG map vào RPD 700C (Trả về NULL)

### 🟢 Các Rules ĐƯỢC GIỮ LẠI (Chắc chắn đúng / Đã có tiền lệ)
1. `Bubbles 20` → Map vào **Neo 20-02 Bubble** (✅ Tiền lệ: BTC đã map 2/4 SP này)
2. `The Flash` / `FLASH` → Map vào **Xe FLASH (IP - Bản quyền)** (✅ Trùng 100% bản chất)
3. Các sản phẩm có đuôi "DA HP" (Ví dụ: `New 26 Trắng DA HP`) → Map vào dòng chính (✅ Tiền lệ: BTC đã map `New 26 DA HP` vào `Xe New 26`)
4. Các dòng có cấu trúc tên trùng khớp hoàn toàn: `GN 06-27 2.0 Pro Shimano`, `Super 26` (thường), `Super 24` (thường), `New 26`, `New 24`, `LD 24-02`, v.v...

---

## 3. Tác Động Lên Dashboard Sau Khi Siết Chặt Logic

Nếu chúng ta sửa lại SQL Patch theo logic khắt khe này, số lượng sản phẩm `NULL` sẽ **tăng lên** so với trước đó (từ 28 SP lên khoảng 65 SP).

### Nhóm "Chưa phân loại" (NULL) trên Dashboard sẽ bao gồm:
1. **Các dòng xe mới chưa có trong catalog:** GN 2.0 700C, MS 27.5, Unite, REX, SLX 27.5.
2. **Các IP bản quyền chưa có dòng riêng:** We Bare Bears, Tom & Jerry, Batwheels.
3. **Các phiên bản (version) khác:** CPD 700C, Super 26 S, RPD 700C V5, SK 20/24, GRX 2.0.

### Đánh giá tác động Business:
- **Nhược điểm:** Tỷ trọng doanh thu của nhóm "Chưa phân loại" sẽ tăng từ ~2.7% lên khoảng **4-5%**.
- **Ưu điểm CỰC KỲ LỚN:** **Dữ liệu hoàn toàn sạch và trung thực.** Ban lãnh đạo khi nhìn vào dashboard sẽ thấy doanh thu của "Xe Super 26" là của *đúng* Super 26 gốc, không bị độn thêm bởi phiên bản "S" hay "SK". Nếu họ thắc mắc tại sao nhóm "Khác" lại lớn (5%), đó là cơ sở vững chắc để data team yêu cầu BTC **cập nhật lại danh mục product_line chuẩn** cho quý mới. 

---

## 4. Hành Động Tiếp Theo

Tôi cần sự xác nhận của bạn:
1. **Đồng ý sửa lại `db_data_quality_patch.sql`** để gỡ bỏ các rules suy diễn (SK, Batwheels, CPD, Super 26 S, v.v.), chỉ giữ lại những rule chắc chắn đúng và rule Bubbles 20?
2. Sau khi sửa SQL, tôi sẽ chạy lại script để test xem chính xác bao nhiêu SP bị đẩy về NULL để chúng ta chốt số cuối cùng.

Bạn thấy hướng xử lý trung thực với data gốc này thế nào?
