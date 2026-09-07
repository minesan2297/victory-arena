# HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CHO THUÊ TÍCH HỢP AI (VICTORY ARENA v2.0)

* **Học phần:** Phân tích Thiết kế và Phát triển Hệ thống Thông tin
* **Đề tài:** Hệ thống Quản lý Sân thể thao cho thuê có tích hợp AI (Bài kiểm tra thường xuyên 2)
* **Đơn vị thực hiện:** Nhóm 20 — Lớp K23C CNTT, Khoa Công nghệ Thông tin
* **Giảng viên hướng dẫn:** ThS. Nguyễn Tuấn Anh
* **Chuẩn mã nguồn:** **Python PEP 8** (Kiến trúc phân tầng Layered Architecture, Type Hints, Pydantic v2)
* **Công nghệ:** FastAPI + SQLAlchemy 2.0 + SQLite/SQL Server + Pydantic v2 + Google Generative AI (Gemini 1.5 Flash)

---

## 1. MỤC TIÊU VÀ BÀI TOÁN THỰC TẾ TRONG QUẢN LÝ SÂN BÓNG

Tại các cụm sân bóng đá cỏ nhân tạo và sân lớn tiêu chuẩn, mô hình quản lý thủ công (ghi chép sổ tay, nhắn tin Zalo, gọi điện) thường phát sinh 4 bài toán lớn:
1. **Trùng lịch trận đấu (Overbooking):** Hai đội bóng cùng đến sân tại một khung giờ vàng (18:30 – 20:00).
2. **Khách bùng sân, mất cọc:** Đặt miệng nhưng không đến thi đấu, gây thất thu mặt bằng.
3. **Lãng phí công suất giờ thấp điểm:** Giờ tối và cuối tuần luôn kín 100%, trong khi giờ trưa (11:30 – 15:30) và sáng sớm vắng khách.
4. **Tốn nhân lực trực tổng đài tư vấn:** Nhân viên liên tục phải nghe điện thoại trả lời các câu hỏi về sân trống, giá thuê.

👉 **Victory Arena v2.0 giải quyết trọn vẹn các bài toán trên bằng Backend hiện đại, thuật toán chống trùng lịch toán học và 3 Module AI Copilot chuyên sâu về bóng đá.**

---

## 2. CẤU TRÚC HỆ THỐNG VÀ PHÂN TẦNG KIẾN TRÚC

Hệ thống áp dụng kiến trúc phân tầng chuẩn (**Layered Architecture**):

```text
chuong_trinh_he_thong/
├── app/
│   ├── main.py                  # Entry point FastAPI, CORS & Static Files & Favicon
│   ├── config.py                # Cấu hình Pydantic Settings (.env)
│   ├── database.py              # SQLite SQLAlchemy Engine (PRAGMA foreign_keys=ON)
│   ├── models/                  # 8 file ORM Database Models chuẩn 3NF (16 bảng)
│   ├── schemas/                 # 7 file Pydantic Schemas (Validation & Serialization)
│   ├── services/                # 8 file Business Logic (Đặt sân, Vận hành, AI, Task ngầm)
│   ├── routers/                 # 9 file RESTful API Endpoints
│   ├── auth/                    # Bảo mật JWT, băm mật khẩu Bcrypt & Dependencies RBAC
│   └── static/                  # Single Page Application Frontend (HTML5, Cyber CSS, JS)
├── tests/                       # Test suite tự động với Pytest (9 ca kiểm thử)
├── seed_data.py                 # Script nạp dữ liệu mẫu ban đầu (5 sân chuẩn)
├── requirements.txt             # Danh sách thư viện phụ thuộc
├── .env.example                 # Mẫu cấu hình môi trường
├── sports_court.db              # File cơ sở dữ liệu SQLite
├── CHAY_HE_THONG.bat            # File 1-Click: Bấm đúp chạy server ngay lập tức
└── README.md                    # Tài liệu hướng dẫn sử dụng và kiểm thử
```

---

## 3. CỤM SÂN BÓNG ĐÁ VÀ QUY ĐỊNH HẠ TẦNG

Hệ thống quản lý cụm sân chuẩn gồm **đúng 5 sân bóng đá** (Đã loại bỏ hoàn toàn Sân 5 và Futsal theo phản hồi của Hội đồng):
- **3 Sân 7 người (Bóng đá phủi):**
  - `SAN7-001` (Sân 7A - Bernabeu)
  - `SAN7-002` (Sân 7B - San Siro)
  - `SAN7-003` (Sân 7C - Camp Nou)
- **2 Sân 11 người (Bóng đá tiêu chuẩn):**
  - `SAN11-001` (Sân 11A - Old Trafford)
  - `SAN11-002` (Sân 11B - Wembley)

---

## 4. THUẬT TOÁN CHỐNG TRÙNG LỊCH TRẬN ĐẤU (ANTI-OVERBOOKING)

Thuật toán kiểm tra giao thoa thời gian (Time Interval Overlap) tại `app/services/dat_san_service.py`:

$$\text{Xung đột} \iff (\text{new\_start} < \text{existing\_end}) \land (\text{new\_end} > \text{existing\_start})$$

* Áp dụng trên cùng mã sân (`ma_san`) và cùng ngày thi đấu (`ngay_da`).
* Kiểm tra đồng thời cả đơn đặt sân đã cọc (`da_xac_nhan`), đơn đang giữ chỗ 10 phút (`cho_coc`), và lịch bảo trì sân (`LichDat.loai_lich == 'bao_tri'`).

---

## 5. 3 CHỨC NĂNG AI COPILOT TÍCH HỢP

1. **AI-1 Match Consultant (`consult_pitch`):**
   * Chatbot phân tích nhu cầu tự nhiên: số lượng người chơi (Sân 7 vs Sân 11), khung giờ mong muốn.
   * **Anti-Hallucination Guardrail:** AI chỉ được gợi ý các slot trống thực tế (`AVAILABLE`) lấy từ CSDL.
2. **AI-2 Football Match Reminder (`generate_reminder`):**
   * Tự động sinh tin nhắn Zalo/SMS truyền cảm hứng thi đấu, dặn dò mang giày đinh TF/FG, tất dài và có mặt trước 15 phút.
3. **AI-3 Capacity & Revenue Insights (`analyze_revenue`):**
   * Phân tích tỷ lệ lấp đầy sân và đề xuất 3 chương trình kích cầu giảm giá giờ thấp điểm.

---

## 6. HƯỚNG DẪN CÀI ĐẶT VÀ KHỞI CHẠY DỰ ÁN

### Cách 1: Chạy 1-Click trên Windows (Khuyên dùng)
* Nhấp đúp chuột vào file: **`CHAY_HE_THONG.bat`**
* Server sẽ tự kiểm tra thư viện, nạp CSDL mẫu và khởi chạy tại: `http://127.0.0.1:8000`.

### Cách 2: Chạy thủ công bằng dòng lệnh
```bash
# Bước 1: Cài đặt thư viện
pip install -r requirements.txt

# Bước 2: Nạp dữ liệu cụm sân và tài khoản mẫu
python seed_data.py

# Bước 3: Khởi chạy Server FastAPI
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* **Giao diện Web SPA Victory Arena:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Tài liệu Swagger API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 7. TÀI KHOẢN MẪU KIỂM THỬ HỆ THỐNG

| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn & Chức năng kiểm thử |
|---|---|---|---|
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Cấu hình Sân bãi (Thêm, Sửa, Xóa), Bảng giá, Dịch vụ, Xem Báo cáo AI |
| **Nhân viên sân (STAFF)** | `staff` | `staff123` | Xác nhận cọc, Check-in vào sân, Bán dịch vụ nước/áo, Check-out POS |
| **Khách hàng 1** | `tuan_fc` | `tuan123` | Tra cứu lịch trực quan, Đặt giữ chỗ 10p, Xem lịch sử cá nhân, Hủy đơn |
| **Khách hàng 2** | `hai_nam` | `hai123` | Trải nghiệm Chatbot AI tư vấn tìm sân theo ngôn ngữ tự nhiên |

---

## 8. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (PYTEST)

```bash
pytest -v
```

**9/9 Ca kiểm thử chuyên sâu đều đạt 100% Passed:**
1. `test_ai_consult_recommendation`: Kiểm tra AI tư vấn đúng slot trống thực tế.
2. `test_ai_notifications_generation`: Kiểm tra AI sinh tin nhắn nhắc lịch Zalo/SMS chuẩn format.
3. `test_ai_promotions_insight`: Kiểm tra AI phân tích công suất và đề xuất khuyến mãi giờ trưa.
4. `test_auth_registration`: Kiểm tra đăng ký và phân quyền JWT Role-based.
5. `test_create_booking_success`: Kiểm tra đặt sân thành công khi slot trống và kích hoạt lock 10 phút.
6. `test_anti_overbooking_overlap`: Kiểm tra thuật toán chặn đứng đặt trùng giờ hoặc giao thoa thời gian.
7. `test_booking_maintenance_lock`: Kiểm tra tự động khóa slot khi sân có lịch bảo dưỡng mặt cỏ/đèn.
8. `test_booking_cancellation_refund`: Kiểm tra chính sách hủy trước 24h tự động hoàn tiền cọc.
9. `test_court_crud_operations`: Kiểm tra toàn diện 4 thao tác CRUD Sân bãi (Thêm mới, Xem, Sửa thông tin, Xóa an toàn).
