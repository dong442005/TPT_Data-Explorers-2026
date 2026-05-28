# 🔍 Phân tích Chuyên sâu: Quyết định Kỹ thuật trong RFM Scoring
### Dựa trên EDA thực tế từ Database TNBike — 24/05/2026

---

## Bối cảnh: TNBike — B2B Bicycle Distribution

| Đặc điểm | Giá trị thực tế (từ EDA) | Ảnh hưởng đến RFM |
|---|---|---|
| Tổng đại lý có giao dịch | **798** | Kích thước mẫu trung bình — đủ cho phân nhóm thống kê |
| Data range | 6 tháng (T1-T3/2025 + T1-T3/2026) | **Rất ngắn** — Frequency bị nén, thiếu T4-T12/2025 |
| Mô hình kinh doanh | B2B wholesale | Tần suất mua thưa, lumpy demand |
| Customer Tier | ⚠️ **Toàn bộ 798 đại lý đều là STANDARD** | Cột `customer_tier` **vô tác dụng** — không có VIP/KEY nào |
| Chu kỳ đặt hàng tự nhiên | 2-3 tháng (đại lý nhỏ) | Recency 90 ngày ≠ churn |
| Mốc tính Recency | `2026-03-31` (ngày cuối cùng có data) | Tất cả recency tính từ mốc này |

> [!IMPORTANT]
> **Phát hiện bất ngờ từ EDA:** Toàn bộ 798 đại lý đều có `customer_tier = STANDARD`. Không hề có VIP hay KEY. Điều này có nghĩa RFM chính là **công cụ phân tầng duy nhất** cho hệ thống đại lý TNBike — tầm quan trọng của việc chọn đúng scoring method càng lớn hơn.

---

## Phần 1: Kết quả EDA — Phân bố R/F/M Thực tế

### 1.1 RECENCY — Phân bố Bi-modal (2 cụm)

**Thống kê mô tả:**

| Chỉ số | Giá trị |
|---|---|
| Mean | 148.4 ngày |
| Median | 32 ngày |
| Std | 174.3 ngày |
| Min | 0 ngày |
| Max | 449 ngày |
| Skewness | **0.61** (lệch phải nhẹ) |

**Phân bố Percentile:**

| Percentile | Giá trị | Ghi chú |
|---|---|---|
| P5 | 0 ngày | |
| P10 | 3 ngày | |
| P20 | 6 ngày | ← NTILE boundary |
| P25 | 10 ngày | |
| P40 | 19 ngày | ← NTILE boundary |
| **P50** | **32 ngày** | **← MEDIAN** |
| P60 | 62 ngày | ← NTILE boundary |
| P70 | **367 ngày** | ⚠️ **Nhảy vọt từ 62 → 367!** |
| P75 | 369 ngày | |
| P80 | 371 ngày | ← NTILE boundary |
| P90 | 390 ngày | |
| P95 | 407 ngày | |
| P99 | 442 ngày | |

**Phân bố theo khoảng ngày:**

| Khoảng | Số ĐL | Tỷ lệ | Tích lũy | Ý nghĩa |
|---|---|---|---|---|
| 0-7 ngày | 195 | 24.4% | 24.4% | Mua trong tuần cuối T3/2026 |
| 8-14 ngày | 78 | 9.8% | 34.2% | Mua giữa T3/2026 |
| 15-30 ngày | 121 | 15.2% | 49.4% | Mua đầu T3/2026 |
| 31-60 ngày | 73 | 9.1% | 58.5% | Mua trong T2/2026 |
| 61-90 ngày | 50 | 6.3% | 64.8% | Mua trong T1/2026 |
| **91-180 ngày** | **0** | **0.0%** | **64.8%** | ⚠️ **KHÔNG CÓ AI — Khoảng trống data** |
| 181-365 ngày | 40 | 5.0% | 69.8% | Mua T2-T3/2025 |
| >365 ngày | 241 | 30.2% | 100.0% | Chỉ mua trong T1/2025 |

> [!CAUTION]
> **Phát hiện quan trọng nhất:** Recency có phân bố **bi-modal** — 2 cụm tách biệt rõ ràng:
> - **Cụm Active (64.8%):** 0-90 ngày (mua trong T1-T3/2026)
> - **Cụm Inactive (35.2%):** 181-449 ngày (chỉ mua trong 2025)
> - **Khoảng trống 91-180 ngày: 0 đại lý** — Do thiếu data T4-T12/2025
>
> NTILE(5) chia đều 798 đại lý thành 5 nhóm ~160 → **ép 160 đại lý vào nhóm R=2 và R=3 nhưng thực tế khoảng giữa trống rỗng**. Phân nhóm vô nghĩa.

**Tháng mua cuối cùng — Gap Analysis:**

| Tháng mua cuối | Số ĐL | Tỷ lệ |
|---|---|---|
| 2025-T01 | 16 | 2.0% |
| 2025-T02 | 63 | 7.9% |
| 2025-T03 | 202 | 25.3% |
| *(Gap: T04 → T12/2025 — không có data)* | | |
| 2026-T01 | 56 | 7.0% |
| 2026-T02 | 67 | 8.4% |
| 2026-T03 | **394** | **49.4%** |

→ Gần **nửa** tổng đại lý có đơn cuối cùng trong T3/2026. 281 đại lý (35.2%) chỉ mua trong 2025 rồi "biến mất" — nhưng **không chắc đã churn** vì data bị thiếu 9 tháng giữa.

---

### 1.2 FREQUENCY — Lệch cực mạnh (Skew = 11.59)

**Thống kê mô tả:**

| Chỉ số | Giá trị |
|---|---|
| Mean | 3.5 đơn |
| Median | **2 đơn** |
| Std | 7.6 đơn |
| Min | 1 đơn |
| Max | **137 đơn** |
| Skewness | **11.59** (lệch phải cực mạnh) |

**Phân bố Percentile:**

| Percentile | Giá trị | Ghi chú |
|---|---|---|
| P5 – P30 | **1 đơn** | ⚠️ 30% đại lý đầu tiên đều = 1 đơn |
| P40 – P60 | **2 đơn** | 30% tiếp theo cũng chỉ 2 đơn |
| P70 | 3 đơn | |
| P75 | 4 đơn | |
| P80 | 4 đơn | ← NTILE boundary |
| P90 | 6 đơn | |
| P95 | 9 đơn | |
| P99 | 19 đơn | |

**Phân bố theo số đơn:**

| Khoảng | Số ĐL | Tỷ lệ | Tích lũy |
|---|---|---|---|
| **1 đơn** | **319** | **40.0%** | 40.0% |
| 2 đơn | 173 | 21.7% | 61.7% |
| 3 đơn | 99 | 12.4% | 74.1% |
| 4-5 đơn | 95 | 11.9% | 86.0% |
| 6-9 đơn | 78 | 9.8% | 95.7% |
| 10-19 đơn | 26 | 3.3% | 99.0% |
| 20-49 đơn | 3 | 0.4% | 99.4% |
| 50+ đơn | 5 | 0.6% | 100.0% |

> [!WARNING]
> **40% đại lý (319/798) chỉ có đúng 1 đơn hàng.** NTILE(5) chia đều thì 160 đại lý Freq=1 bị gán điểm F=1, nhưng 159 đại lý Freq=1 khác lại bị gán điểm F=2 — dù hành vi **hoàn toàn giống nhau**. Đây là vi phạm nguyên tắc segmentation: "đại lý giống nhau phải ở cùng nhóm".
>
> Ngoài ra, **61.7% đại lý chỉ có 1-2 đơn** → Frequency phân biệt kém ở phần đa số. Chỉ **top 4.3% (34 đại lý) có ≥10 đơn** — đây mới thực sự là "frequent buyers" trong B2B.

---

### 1.3 MONETARY — Lệch cực mạnh nhất (Skew = 17.06)

**Thống kê mô tả:**

| Chỉ số | Giá trị |
|---|---|
| Mean | **137.1 triệu** |
| Median | **60.6 triệu** |
| Std | 410.5 triệu |
| Min | 1.5 triệu |
| Max | **9,587 triệu (9.59 tỷ)** |
| Skewness | **17.06** (lệch phải cực kỳ mạnh) |
| Mean/Median ratio | **2.26x** (Mean gấp 2.26 lần Median) |

**Phân bố Percentile:**

| Percentile | Giá trị | Ghi chú |
|---|---|---|
| P5 | 3.2 triệu | |
| P10 | 9.2 triệu | |
| P20 | 21.5 triệu | ← NTILE boundary |
| P25 | 26.1 triệu | |
| P40 | 44.2 triệu | ← NTILE boundary |
| **P50** | **60.6 triệu** | **← MEDIAN** |
| P60 | 82.2 triệu | ← NTILE boundary |
| P75 | 130.7 triệu | |
| P80 | 158.7 triệu | ← NTILE boundary |
| P90 | 286.0 triệu | |
| P95 | 486.9 triệu | |
| P99 | 985.4 triệu | |

**Phân bố theo khoảng chi tiêu:**

| Khoảng | Số ĐL | Tỷ lệ | Tích lũy | Tổng DT (tỷ) | % Tổng DT |
|---|---|---|---|---|---|
| <5 triệu | 66 | 8.3% | 8.3% | 0.21 | 0.2% |
| 5-10 triệu | 17 | 2.1% | 10.4% | 0.13 | 0.1% |
| 10-30 triệu | 134 | 16.8% | 27.2% | 2.70 | 2.5% |
| 30-50 triệu | 132 | 16.5% | 43.7% | 5.19 | 4.7% |
| 50-100 triệu | 187 | 23.4% | 67.2% | 13.58 | 12.4% |
| 100-300 triệu | 185 | 23.2% | 90.4% | 30.42 | 27.8% |
| 300-500 triệu | 40 | 5.0% | 95.4% | 15.27 | 14.0% |
| 500 triệu - 1 tỷ | 29 | 3.6% | 99.0% | 20.26 | 18.5% |
| 1-5 tỷ | 7 | 0.9% | 99.9% | 12.11 | 11.1% |
| >5 tỷ | 1 | 0.1% | 100.0% | 9.59 | 8.8% |

> [!CAUTION]
> **Phát hiện Pareto cực đoan:**
> - **Top 1% (8 đại lý)** có monetary ≥1 tỷ → chiếm **19.9% tổng doanh thu** (21.7 tỷ / 109.5 tỷ)
> - **Top 10% (77 đại lý)** có monetary ≥286 triệu → chiếm ước tính **~53% tổng doanh thu**
> - **Bottom 27% (217 đại lý)** có monetary <30 triệu → chỉ chiếm **2.8% tổng doanh thu**
>
> NTILE(5) gán 159 đại lý điểm M=5 (top 20%) — trong khi thực tế chỉ có **8 đại lý** thực sự ở cấp "champion" (≥1 tỷ). Gán điểm 5 cho 159 đại lý là **quá rộng rãi**, mất đi khả năng phân biệt nhóm VIP thực sự.

---

### 1.4 Cross-tab: Region × R/F/M

| Region | Số ĐL | Avg Recency | Avg Freq | Avg Monetary (triệu) | Median Monetary (triệu) |
|---|---|---|---|---|---|
| Chưa xác định | 97 | 12 ngày | 2.5 | 60.6 | 31.2 |
| **Miền Bắc** | **579** | 172 ngày | 3.4 | 139.3 | 61.3 |
| **Miền Nam** | **4** | 122 ngày | **38.8** | **1,446.8** | **649.7** |
| Miền Trung | 118 | 144 ngày | 3.1 | 145.3 | 88.4 |

> [!NOTE]
> **Miền Nam (4 đại lý)** có hành vi B2B khác biệt hoàn toàn:
> - Avg Frequency = **38.8 đơn** (gấp 11x Miền Bắc)
> - Avg Monetary = **1,447 triệu** (gấp 10.4x Miền Bắc)
> - Đây là các đại lý lớn, mua sỉ số lượng khủng → RFM segment phải phản ánh đúng giá trị này.

---

### 1.5 Spot-check: Đại lý cụ thể — NTILE vs Manual

| KH Code | Recency | Freq | Monetary (triệu) | R_ntile | F_ntile | M_ntile | R_manual | F_manual | M_manual | Nhận xét |
|---|---|---|---|---|---|---|---|---|---|---|
| KH-00091 | 0d | 55 | 9,587.0 | 1 | 1 | 1 | 5 | 5 | 5 | **NTILE đảo ngược hoàn toàn** — Top dealer bị gán điểm thấp nhất |
| KH-00019 | 5d | 70 | 4,483.1 | 1 | 1 | 1 | 5 | 5 | 5 | Tương tự — đại lý miền Nam #1 |
| KH-00173 | 371d | 21 | 1,582.0 | 4 | 1 | 1 | 1 | 5 | 5 | Đại lý từng rất lớn nhưng đã inactive |
| KH-00030 | 61d | 2 | 1,366.3 | 3 | 2 | 1 | 3 | 2 | 5 | Big Spender — ít đơn nhưng giá trị cực cao |
| KH-00733 | 22d | 1 | 60.8 | 3 | 5 | 3 | 5 | 1 | 2 | NTILE gán F=5 cho đại lý chỉ 1 đơn! |
| KH-00129 | 404d | 1 | 60.3 | 5 | 5 | 3 | 1 | 1 | 2 | NTILE gán R=5, F=5 cho đại lý đã mất |
| KH-00176 | 389d | 1 | 1.5 | 5 | 5 | 5 | 1 | 1 | 1 | **Đại lý tệ nhất bị gán điểm cao nhất** |

> [!CAUTION]
> **Kết luận rõ ràng:** NTILE(5) cho kết quả **đảo ngược hoặc vô nghĩa** với data TNBike. Đại lý top nhất (9.587 tỷ, 55 đơn) bị gán điểm 1-1-1, trong khi đại lý tệ nhất (1.5 triệu, 1 đơn, 389 ngày không mua) bị gán 5-5-5. Nguyên nhân gốc: NTILE chỉ đếm thứ hạng tương đối trong nhóm, kết hợp với chiều `ORDER BY` bị phụ thuộc vào convention — dễ dẫn đến sai lầm logic.
>
> **Lưu ý kỹ thuật:** Ở bản SQL gốc trong guide, NTILE dùng `ORDER BY recency_days ASC` (recency nhỏ = nhóm 1 = điểm 1). Khi dùng trong CASE-WHEN gán segment, cần hiểu đúng rằng nhóm 1 = tốt nhất. Tuy nhiên vấn đề cốt lõi vẫn là: NTILE chia đều không phản ánh phân bố thực, **bất kể chiều sắp xếp**.

---

## Phần 2: NTILE(5) — Tại sao không phù hợp TNBike?

### 2.1 NTILE(5) là gì?

`NTILE(5)` chia 798 đại lý thành **5 nhóm bằng nhau** (~160 đại lý/nhóm), rồi gán điểm 1→5.

```
Nhóm 1: Đại lý xếp hạng 1-160     → Điểm = 1
Nhóm 2: Đại lý xếp hạng 161-320   → Điểm = 2
Nhóm 3: Đại lý xếp hạng 321-480   → Điểm = 3
Nhóm 4: Đại lý xếp hạng 481-640   → Điểm = 4
Nhóm 5: Đại lý xếp hạng 641-798   → Điểm = 5
```

### 2.2 Tại sao thường chọn NTILE?

| Lý do | Giải thích |
|---|---|
| Đơn giản | 1 dòng SQL, không cần tính toán ngưỡng thủ công |
| Phổ biến | Đa số tài liệu RFM trên mạng dùng NTILE(5) hoặc NTILE(4) |
| Phân bổ đều | Mỗi nhóm luôn có số lượng bằng nhau → dashboard cân đối |
| Không cần domain knowledge | Áp dụng được mà không cần hiểu biết về ngành |

### 2.3 Ba vấn đề cụ thể với data TNBike (đã xác nhận bằng EDA)

#### ❌ Vấn đề 1: Recency bi-modal — Khoảng trống 91-180 ngày = 0 đại lý

```
Phân bố Recency thực tế:

  0-30 ngày:  ████████████████████████████████████████████  394 ĐL (49.4%)
 31-90 ngày:  ████████████                                  123 ĐL (15.4%)
91-180 ngày:                                                  0 ĐL (0.0%)  ← TRỐNG HOÀN TOÀN
181-365 ngày: ████                                            40 ĐL (5.0%)
  >365 ngày:  ████████████████████████                       241 ĐL (30.2%)
```

NTILE chia 798 thành 5 nhóm ~160 → nhóm R=2 (rank 161-320) rơi vào đúng khoảng trống, chứa hỗn hợp đại lý 30-ngày lẫn 370-ngày trong cùng nhóm. **Phân nhóm vô nghĩa.**

#### ❌ Vấn đề 2: Frequency — 40% đại lý cùng Freq=1 bị chia thành 2 điểm khác nhau

```
Frequency thực tế:

1 đơn:  ████████████████████████████████████████ 319 ĐL (40.0%)
2 đơn:  ██████████████████████                   173 ĐL (21.7%)
3 đơn:  ████████████                              99 ĐL (12.4%)
4-5 đơn: ████████████                              95 ĐL (11.9%)
6-9 đơn: ██████████                                78 ĐL (9.8%)
10+ đơn: ████                                      34 ĐL (4.3%)
```

319 đại lý có Freq=1, NTILE chia ra: 160 cái → điểm 1, 159 cái → điểm 2. **Cùng hành vi, khác điểm.**

#### ❌ Vấn đề 3: Monetary skew = 17.06 — NTILE cho 159 đại lý điểm "top" nhưng thực chất chỉ 8 đại lý thực sự top

NTILE gán điểm M=5 cho 159 đại lý (top 20%). Nhưng thực tế:
- Chỉ **8 đại lý (1%)** có monetary ≥1 tỷ
- Chỉ **77 đại lý (9.6%)** có monetary ≥286 triệu (P90)
- Đại lý rank 159 (M=5 theo NTILE) chỉ có ~159 triệu — cách đại lý #1 (9,587 triệu) **gấp 60 lần** nhưng cùng điểm.

### 2.4 So sánh phân bố điểm: NTILE vs Manual

| Điểm | R: NTILE | R: Manual | F: NTILE | F: Manual | M: NTILE | M: Manual |
|---|---|---|---|---|---|---|
| 1 | 160 (20.1%) | **281 (35.2%)** | 160 (20.1%) | **319 (40.0%)** | 160 (20.1%) | **217 (27.2%)** |
| 2 | 160 (20.1%) | **0 (0.0%)** | 160 (20.1%) | 173 (21.7%) | 160 (20.1%) | **319 (40.0%)** |
| 3 | 159 (19.9%) | 50 (6.3%) | 159 (19.9%) | 194 (24.3%) | 159 (19.9%) | 185 (23.2%) |
| 4 | 160 (20.1%) | 73 (9.1%) | 160 (20.1%) | 78 (9.8%) | 160 (20.1%) | 69 (8.6%) |
| 5 | 159 (19.9%) | **394 (49.4%)** | 159 (19.9%) | **34 (4.3%)** | 159 (19.9%) | **8 (1.0%)** |

> [!IMPORTANT]
> **Quan sát then chốt từ bảng trên:**
> - **R Manual:** Điểm 5 = 394 đại lý (49.4%) — vì gần nửa đại lý mua trong T3/2026. Điểm 2 = 0 — vì khoảng 91-180 ngày trống rỗng. **Phản ánh đúng thực tế.**
> - **F Manual:** Điểm 1 = 319 đại lý (40%) — vì 40% chỉ mua 1 lần. Điểm 5 = 34 đại lý (4.3%) — nhóm "frequent buyer" thật sự. **Phản ánh đúng thực tế.**
> - **M Manual:** Điểm 5 = 8 đại lý (1%) — chỉ 8 đại lý thực sự đạt ≥1 tỷ. **Phản ánh đúng thực tế.**
> - **NTILE luôn = 160 mỗi nhóm** — bất kể phân bố data ra sao. **Không phản ánh thực tế.**

---

## Phần 3: Ngưỡng Segment — Dựa vào đâu?

### 3.1 Ngưỡng bản gốc (từ Guide)

```sql
CASE
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
    WHEN r_score >= 4 AND f_score >= 3                   THEN 'Loyal'
    WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 3  THEN 'Potential'
    WHEN r_score >= 4 AND f_score <= 2                   THEN 'New'
    WHEN r_score = 3  AND f_score >= 3                   THEN 'At Risk'
    WHEN r_score <= 2 AND f_score >= 3                   THEN 'Hibernating'
    ELSE 'Lost'
END
```

### 3.2 Nguồn gốc: Framework RFM Retail tiêu chuẩn

Các ngưỡng `>=4`, `>=3` đến từ **framework RFM phổ biến trong ngành Retail/E-commerce** (Putler, Baremetrics, CleverTap). Logic cốt lõi đúng:

| Segment | Logic gốc |
|---|---|
| Champions | R↑ F↑ M↑ — Mua gần đây, thường xuyên, chi nhiều |
| Loyal | R↑ F↑ — Mua gần đây + thường xuyên |
| Potential | R~ F~ M~ — Có tiềm năng |
| New | R↑ F↓ — Mới mua nhưng chưa có lịch sử |
| At Risk | R~ F↑ — Từng mua nhiều nhưng bắt đầu giãn |
| Hibernating | R↓ F↑ — Từng tích cực nhưng đã biến mất |
| Lost | Phần còn lại |

### 3.3 Vấn đề: Ngưỡng Retail ≠ B2B Xe đạp

| Chiều | Retail/E-commerce | B2B TNBike (từ EDA) | Hệ quả |
|---|---|---|---|
| Chu kỳ mua | 1-4 lần/tháng | Median = 2 đơn/6 tháng | F "cao" ở B2B ≈ 10+ đơn/6 tháng |
| Giá trị đơn | 100K - 5 triệu | Median 60.6 triệu, Max 9.59 tỷ | Monetary cần ngưỡng tỷ VND |
| Recency 30 ngày | Đáng lo | Hoàn toàn bình thường | Đại lý 60 ngày không mua = OK |
| Số lượng KH | Hàng nghìn → triệu | 798 đại lý | Champions 20% = 160 ĐL — quá rộng |
| Customer Tier | Đa dạng | 100% STANDARD | RFM là phân tầng duy nhất |

### 3.4 Ví dụ sai lệch cụ thể (từ EDA)

**Case 1: KH-00030 — "Big Spender" bị gán sai**
- Recency: 61 ngày | Freq: 2 | Monetary: **1,366 triệu (1.37 tỷ)**
- Bản gốc sẽ gán: **"Potential"** hoặc **"New"** (vì F thấp)
- Thực tế: Đây là đại lý **giá trị cực cao**, mua sỉ theo quý. Nên là **"Big Spender"** hoặc **"Loyal"**

**Case 2: KH-00020 — "Lost" nhưng thực chất rất giá trị**
- Recency: 444 ngày | Freq: 1 | Monetary: **124.6 triệu**
- Bản gốc gán: **"Lost"** → bỏ qua
- Thực tế: Chi 124.6 triệu chỉ trong 1 đơn hàng → Đại lý lớn tiềm năng, nên là **"Win-back Priority"**

**Case 3: KH-00733 — Đại lý nhỏ mới**
- Recency: 22 ngày | Freq: 1 | Monetary: 60.8 triệu
- Bản gốc gán: **"New"** ← Đúng
- Nhưng với NTILE: R_ntile=3, F_ntile=5 → có thể bị gán "At Risk" hoặc "Loyal" ← **Sai**

---

## Phần 4: Đề xuất Scoring — Business-Driven Thresholds

> [!IMPORTANT]
> **Nguyên tắc:** Mỗi ngưỡng phải trả lời được câu hỏi: **"Con số này có ý nghĩa gì với Sales Manager của TNBike?"**

### 4.1 Recency Score — Dựa trên chu kỳ B2B + Gap Analysis

```sql
CASE
    WHEN recency_days <= 30  THEN 5  -- Mua trong T3/2026 (394 ĐL = 49.4%)
    WHEN recency_days <= 60  THEN 4  -- Mua trong T2/2026 (73 ĐL = 9.1%)
    WHEN recency_days <= 90  THEN 3  -- Mua trong T1/2026 (50 ĐL = 6.3%)
    WHEN recency_days <= 180 THEN 2  -- Gap zone (0 ĐL — nhưng giữ ngưỡng cho tương lai)
    ELSE                          1  -- Chỉ mua trong 2025 (281 ĐL = 35.2%)
END AS r_score
```

**Lý do từng ngưỡng:**

| Ngưỡng | Lý do | Data support |
|---|---|---|
| **≤30 ngày → 5** | Mua trong tháng cuối cùng có data → đang active rõ ràng | 394 ĐL (49.4%) — nhóm lớn nhất, đúng thực tế |
| **≤60 ngày → 4** | Trong chu kỳ B2B bình thường (2 tháng) | 73 ĐL (9.1%) — đại lý active nhưng tần suất thấp hơn |
| **≤90 ngày → 3** | Ngưỡng churn B2B theo [business domain spec §14.3](file:///d:/NPD/V2_DataExplore/Data_Explorers_Vong_2/business_domain_specification.md#L531-L534) | 50 ĐL (6.3%) — biên giới active/inactive |
| **≤180 ngày → 2** | Xét khoảng trống data. Hiện có 0 ĐL nhưng giữ ngưỡng cho data tương lai | 0 ĐL — nhưng cần slot này khi có data T4-T12 |
| **>180 ngày → 1** | Đã qua 2+ chu kỳ B2B mà không mua → rất có thể đã churn | 281 ĐL (35.2%) — chỉ mua trong 2025 |

### 4.2 Frequency Score — Dựa trên phân bố thực tế

```sql
CASE
    WHEN frequency >= 10 THEN 5  -- Heavy hitter (34 ĐL = 4.3%)
    WHEN frequency >= 6  THEN 4  -- Regular tốt (78 ĐL = 9.8%)
    WHEN frequency >= 3  THEN 3  -- B2B bình thường (194 ĐL = 24.3%)
    WHEN frequency >= 2  THEN 2  -- Đã repeat ít nhất 1 lần (173 ĐL = 21.7%)
    ELSE                      1  -- One-time buyer (319 ĐL = 40.0%)
END AS f_score
```

**Lý do từng ngưỡng:**

| Ngưỡng | Lý do | Data support |
|---|---|---|
| **≥10 → 5** | Theo [business domain §5.1](file:///d:/NPD/V2_DataExplore/Data_Explorers_Vong_2/business_domain_specification.md#L178-L185): Heavy Hitters mua hàng tháng → 6 tháng ≈ ≥10 đơn | 34 ĐL (4.3%) — đúng với top 5% trong spec |
| **≥6 → 4** | Regular buyer (60% theo spec) mua 2-4 lần/quý → 6 tháng ≈ 4-8 đơn, ≥6 = "tốt" | 78 ĐL (9.8%) — trùng khớp P90 = 6 đơn |
| **≥3 → 3** | Occasional (25%) mua 1-2 lần/quý → 6 tháng ≈ 2-4 đơn, ≥3 = "chấp nhận được" | 194 ĐL (24.3%) |
| **≥2 → 2** | Đã quay lại ít nhất 1 lần → có retention signal | 173 ĐL (21.7%) |
| **1 → 1** | Chỉ mua 1 lần → chưa có bằng chứng quay lại | **319 ĐL (40.0%)** — nhóm lớn nhất |

> [!NOTE]
> **Ngưỡng F=1 (one-time buyer) = 40% là phát hiện quan trọng.** Nếu dùng NTILE, nhóm này bị chia thành 2 điểm (F=1 và F=2), che mất sự thật rằng gần nửa hệ thống đại lý **chưa bao giờ repeat**. Manual scoring giữ nguyên 319 ĐL ở điểm 1 → Sales team thấy rõ vấn đề.

### 4.3 Monetary Score — Dựa trên cơ cấu doanh thu thực tế

```sql
CASE
    WHEN monetary >= 1000000000  THEN 5  -- ≥1 tỷ → Đại lý chiến lược (8 ĐL = 1.0%)
    WHEN monetary >= 300000000   THEN 4  -- ≥300 triệu (69 ĐL = 8.6%)
    WHEN monetary >= 100000000   THEN 3  -- ≥100 triệu (185 ĐL = 23.2%)
    WHEN monetary >= 30000000    THEN 2  -- ≥30 triệu (319 ĐL = 40.0%)
    ELSE                              1  -- <30 triệu (217 ĐL = 27.2%)
END AS m_score
```

**Lý do từng ngưỡng:**

| Ngưỡng | Lý do | Data support |
|---|---|---|
| **≥1 tỷ → 5** | 167 triệu/tháng = đại lý cấp chiến lược, gấp 7.3x trung bình | **8 ĐL** — chỉ 1% nhưng chiếm ~20% tổng doanh thu |
| **≥300 triệu → 4** | Gấp ~2.2x trung bình (137 triệu). Tương đương P90 (286 triệu) | 69 ĐL (8.6%) — khớp với nhóm "đại lý lớn" |
| **≥100 triệu → 3** | Xấp xỉ trung bình hệ thống. Đóng góp đáng kể | 185 ĐL (23.2%) — nhóm trung bình |
| **≥30 triệu → 2** | 5 triệu/tháng ≈ 3-5 chiếc xe phổ thông/tháng → đại lý nhỏ nhưng still active | 319 ĐL (40.0%) — nhóm lớn nhất |
| **<30 triệu → 1** | Dưới P25 (26 triệu). Có thể là thử nghiệm hoặc đại lý rất nhỏ | 217 ĐL (27.2%) — gồm 66 ĐL <5 triệu |

> [!TIP]
> Ngưỡng 300 triệu (M=4) khớp gần với P90 = 286 triệu. Ngưỡng 100 triệu (M=3) nằm giữa P60 (82 triệu) và P70 (110 triệu). Các ngưỡng vừa có ý nghĩa business vừa khớp với phân bố percentile thực tế.

---

## Phần 5: Segment Rules — Điều chỉnh theo B2B TNBike

### 5.1 Rules đề xuất

```sql
CASE
    -- CHAMPIONS: Đại lý chiến lược — R↑ F↑ M↑
    -- Mua gần đây, thường xuyên, chi lớn. Cần BẢO VỆ bằng mọi giá.
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 
        THEN 'Champions'
    
    -- LOYAL: Mua đều đặn, gần đây, giá trị khá
    -- Có thể tăng giá trị bằng cross-sell nhóm SP khác.
    WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 
        THEN 'Loyal'
    
    -- BIG SPENDER: Chi lớn nhưng ít đơn — ĐẶC THÙ B2B
    -- Đại lý mua sỉ theo quý, mỗi lần 1 đơn lớn.
    -- Segment này KHÔNG CÓ trong framework Retail nhưng RẤT CẦN cho B2B.
    WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 4 
        THEN 'Big Spender'
    
    -- POTENTIAL: Còn active, có tín hiệu tích cực
    WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 2 
        THEN 'Potential'
    
    -- NEW: Mới gia nhập — 1 đơn gần đây, chưa chi nhiều
    WHEN r_score >= 4 AND f_score = 1 AND m_score <= 3 
        THEN 'New'
    
    -- AT RISK: Từng chi tiêu tốt nhưng đã lâu không mua
    -- B2B mất 1 đại lý = mất cả trăm triệu doanh thu → cần hành động NGAY
    WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 
        THEN 'At Risk'
    
    -- HIBERNATING: Đã lâu không mua, từng có giao dịch khá
    WHEN r_score <= 2 AND (f_score >= 2 OR m_score >= 2) 
        THEN 'Hibernating'
    
    -- LOST: Không mua, ít đơn, ít tiền → nhiều khả năng đã rời
    ELSE 'Lost'
END AS rfm_segment
```

### 5.2 Thay đổi so với bản gốc — Giải thích

| Thay đổi | Lý do Business | Data Support |
|---|---|---|
| **Thêm "Big Spender"** | B2B có đại lý mua sỉ 1 đơn/quý nhưng mỗi đơn hàng trăm triệu → tỷ. Bản gốc gán sai thành "New" (vì F thấp). | KH-00030: 2 đơn nhưng 1.37 tỷ, KH-00341: 5 đơn nhưng 1.02 tỷ |
| **"Loyal" thêm M≥3** | Đại lý mua thường xuyên nhưng chỉ 1-2 chiếc/lần (M=1) không nên gọi "Loyal" trong B2B | Phân biệt đại lý nhỏ nhưng siêng (Potential) vs đại lý vừa siêng vừa giá trị (Loyal) |
| **"At Risk" dùng R≤2** | Bản gốc dùng R=3 (61-90 ngày) — vẫn bình thường trong B2B. Chỉ R≤2 (>90 ngày) mới đáng lo | Khoảng 91-180 ngày = 0 ĐL → R≤2 = đại lý chỉ mua trong 2025 |
| **"New" cần M≤3** | Đại lý mới thật sự thường chi tiêu thấp ở đơn đầu. Nếu M≥4 → Big Spender, không phải New | Tránh gán nhầm KH-00030 (1.37 tỷ) thành "New" |

### 5.3 Dự kiến phân bố Segment

Dựa trên phân bố điểm Manual ở Phần 2.4, ước tính phân bố segment:

| Segment | Ước tính % | Hành động kinh doanh |
|---|---|---|
| Champions | ~2-5% (~16-40 ĐL) | Ưu đãi VIP, account manager riêng |
| Loyal | ~5-10% (~40-80 ĐL) | Cross-sell, tăng giá trị đơn hàng |
| Big Spender | ~3-5% (~24-40 ĐL) | Duy trì quan hệ, không ép tần suất |
| Potential | ~15-20% (~120-160 ĐL) | Nurturing, khuyến mãi lần mua tiếp |
| New | ~10-15% (~80-120 ĐL) | Onboarding 90 ngày, follow-up đơn đầu |
| At Risk | ~5-8% (~40-64 ĐL) | ⚠️ Liên hệ ngay, win-back offers |
| Hibernating | ~15-20% (~120-160 ĐL) | Campaign re-engagement |
| Lost | ~20-25% (~160-200 ĐL) | Phân tích nguyên nhân |

> [!NOTE]
> Số liệu chính xác cần chạy SQL thực tế trên view mới để xác nhận. Tỷ lệ Lost + Hibernating cao (~35-45%) phản ánh đúng thực tế: **35.2% đại lý chỉ mua trong 2025** và 40% chỉ mua 1 lần.

---

## Phần 6: SQL View đề xuất hoàn chỉnh

```sql
CREATE OR REPLACE VIEW tnbike.v_rfm_analysis AS
WITH rfm_raw AS (
    SELECT
        f.customer_code,
        c.customer_name,
        c.customer_tier,
        COALESCE(pr.province_name, 'Chưa xác định') AS province_name,
        COALESCE(pr.region, 'Chưa xác định') AS region,
        MAX(f.order_date) AS last_order_date,
        DATE '2026-03-31' - MAX(f.order_date) AS recency_days,
        COUNT(DISTINCT f.so_number) AS frequency,
        SUM(f.line_total) AS monetary
    FROM tnbike.fact_sales f
    JOIN tnbike.customer c ON c.customer_code = f.customer_code
    LEFT JOIN tnbike.province pr ON pr.province_id = c.province_id
    GROUP BY f.customer_code, c.customer_name, c.customer_tier, 
             pr.province_name, pr.region
),
rfm_scored AS (
    SELECT *,
        -- R Score: dựa trên chu kỳ B2B + gap analysis thực tế
        CASE
            WHEN recency_days <= 30  THEN 5  -- 394 ĐL (49.4%)
            WHEN recency_days <= 60  THEN 4  -- 73 ĐL (9.1%)
            WHEN recency_days <= 90  THEN 3  -- 50 ĐL (6.3%)
            WHEN recency_days <= 180 THEN 2  -- 0 ĐL (gap zone)
            ELSE                          1  -- 281 ĐL (35.2%)
        END AS r_score,
        
        -- F Score: dựa trên phân bố frequency thực tế (6 tháng data)
        CASE
            WHEN frequency >= 10 THEN 5  -- 34 ĐL (4.3%)
            WHEN frequency >= 6  THEN 4  -- 78 ĐL (9.8%)
            WHEN frequency >= 3  THEN 3  -- 194 ĐL (24.3%)
            WHEN frequency >= 2  THEN 2  -- 173 ĐL (21.7%)
            ELSE                      1  -- 319 ĐL (40.0%)
        END AS f_score,
        
        -- M Score: dựa trên cơ cấu doanh thu B2B TNBike
        CASE
            WHEN monetary >= 1000000000  THEN 5  -- ≥1 tỷ: 8 ĐL (1.0%)
            WHEN monetary >= 300000000   THEN 4  -- ≥300 triệu: 69 ĐL (8.6%)
            WHEN monetary >= 100000000   THEN 3  -- ≥100 triệu: 185 ĐL (23.2%)
            WHEN monetary >= 30000000    THEN 2  -- ≥30 triệu: 319 ĐL (40.0%)
            ELSE                              1  -- <30 triệu: 217 ĐL (27.2%)
        END AS m_score
    FROM rfm_raw
)
SELECT *,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 
            THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 
            THEN 'Loyal'
        WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 4 
            THEN 'Big Spender'
        WHEN r_score >= 3 AND f_score >= 2 AND m_score >= 2 
            THEN 'Potential'
        WHEN r_score >= 4 AND f_score = 1 AND m_score <= 3 
            THEN 'New'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 
            THEN 'At Risk'
        WHEN r_score <= 2 AND (f_score >= 2 OR m_score >= 2) 
            THEN 'Hibernating'
        ELSE 'Lost'
    END AS rfm_segment
FROM rfm_scored;
```

---

## Phần 7: Tóm tắt Quyết định

### So sánh tổng thể

| Khía cạnh | Bản gốc (Guide) | Bản cải tiến (sau EDA) |
|---|---|---|
| **Scoring** | NTILE(5) — chia đều 160 ĐL/nhóm | CASE-WHEN — ngưỡng business-driven |
| **Cơ sở** | Textbook generic | EDA thực tế + business domain spec |
| **Segments** | 7 (thiếu Big Spender) | 8 (thêm Big Spender cho B2B) |
| **Xử lý data gap** | Không | R=2 dành cho zone 91-180 ngày |
| **Xử lý 40% one-time** | Chia thành 2 nhóm điểm | Giữ nguyên 1 nhóm (F=1) |
| **Top dealer M=5** | 159 ĐL (20%) | 8 ĐL (1%) — chỉ ≥1 tỷ |
| **Khả năng giải thích** | "Điểm 4 = top 20-40%" | "Điểm 5 = mua trong 30 ngày gần nhất" |
| **Ổn định** | Thay đổi khi thêm/bớt ĐL | Ổn định — ngưỡng cố định |

### Quy trình ra quyết định (đã thực hiện)

```
✅ Bước 1: Hiểu Business → Chu kỳ B2B, phân tầng ĐL, đặc thù ngành
    ↓
✅ Bước 2: EDA Data → Percentile, histogram, skewness, gap analysis
    ↓
✅ Bước 3: Đặt ngưỡng → Kết hợp business rules + data distribution
    ↓
✅ Bước 4: Spot-check → KH-00091, KH-00030, KH-00176... xác nhận đúng
    ↓
⬜ Bước 5: Chạy SQL → Tạo view và kiểm tra phân bố segment thực tế
    ↓
⬜ Bước 6: Validate → Đảm bảo mỗi segment đủ lớn (≥20 ĐL)
```

---

## Phần 8: Action Items

- [ ] Chạy SQL tạo view `v_rfm_analysis` phiên bản mới
- [ ] Kiểm tra phân bố segment thực tế (đếm số ĐL mỗi segment)
- [ ] Spot-check 10-15 đại lý đã biết xem segment có hợp lý
- [ ] Cập nhật `dashboard_powerbi_guide.md` mục 5.1 với SQL mới
- [ ] Update DAX measures trong Power BI để dùng segment mới (thêm "Big Spender")

---

*Phân tích dựa trên EDA thực tế ngày 24/05/2026 | File EDA: [eda_rfm.py](file:///C:/Users/HOANG%20TUNG/TPT_Data-Explorers-2026/archive/legacy_scripts/eda_rfm.py)*
