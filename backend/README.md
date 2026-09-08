# PHÂN HỆ BACKEND — VICTORY ARENA v2.0 RESTful API

* **Học phần:** Phân tích Thiết kế và Phát triển Hệ thống Thông tin (Bài kiểm tra thường xuyên 2)
* **Đơn vị phát triển:** Nhóm 20 — Lớp K23C CNTT
* **Giảng viên hướng dẫn:** ThS. Nguyễn Tuấn Anh
* **Công nghệ cốt lõi:** FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2, Python-Jose (JWT HS256), Passlib (Bcrypt), Google Generative AI (Gemini 1.5 Flash), Pytest

---

## 1. CẤU TRÚC THƯ MỤC BACKEND

```text
backend/
├── app/
│   ├── auth/                    # Bảo mật JWT, mã hóa Bcrypt, Dependencies phân quyền (RBAC)
│   ├── models/                  # 8 file ORM Database Models chuẩn 3NF (16 bảng CSDL)
│   ├── schemas/                 # 7 file Pydantic v2 Schemas (Validation & Serialization)
│   ├── services/                # 8 file Business Services (Đặt sân, Vận hành, AI, Task ngầm)
│   ├── routers/                 # 8 file RESTful API Endpoints
│   ├── config.py                # Cấu hình Pydantic BaseSettings (.env)
│   ├── database.py              # SQLite SQLAlchemy Engine (PRAGMA foreign_keys=ON)
│   ├── main.py                  # Entrypoint FastAPI, CORS Middleware & Lifespan Task
│   └── __init__.py
├── tests/                       # Bộ kiểm thử tự động với Pytest (11 Unit Tests)
├── seed_data.py                 # Script nạp dữ liệu mẫu ban đầu (5 sân bóng & tài khoản)
├── requirements.txt             # Danh mục thư viện phụ thuộc Python
├── .env.example                 # Mẫu file biến môi trường cấu hình API Key
├── mini_victory.db              # CSDL SQLite chính thức của hệ thống
├── sports_court.db              # CSDL SQLite môi trường kiểm thử
├── chay_backend.bat             # Script 1-Click khởi chạy riêng Backend trên cổng 8000
└── README.md                    # Tài liệu kỹ thuật phân hệ Backend
```

---

## 2. DANH MỤC API ROUTERS & ENDPOINTS CHÍNH

Hệ thống cung cấp đầy đủ tài liệu API tương tác tự động tại:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc Spec:** `http://127.0.0.1:8000/redoc`

| Nhóm API | Prefix | Phương thức | Chức năng chính | Phân quyền |
|---|---|---|---|---|
| **Auth** | `/api/auth` | POST /login, POST /register, GET /me | Đăng nhập cấp phát JWT Token, Đăng ký, Lấy profile | Public / Token |
| **Sân bóng** | `/api/san` | GET /, GET /{ma}, POST /, PUT /{ma}, DELETE /{ma} | Quản lý danh mục sân, biểu giá thuê, lịch bảo trì | Public / Admin |
| **Đặt sân** | `/api/dat-san` | GET /lich, POST /, POST /xac-nhan-coc, POST /doi-lich, DELETE /{ma} | Thuật toán chống trùng lịch toán học, giữ chỗ 10 phút, hoàn cọc | Customer / Staff |
| **Vận hành** | `/api/van-hanh` | POST /check-in, POST /check-out, GET /don-cho-duyet | Check-in nhận sân, trả sân, tính hóa đơn và phụ phí | Staff / Admin |
| **Dịch vụ** | `/api/dich-vu` | GET /, POST /, POST /su-dung | Danh mục nước uống, phụ kiện, ghi nhận dùng dịch vụ tại sân | Staff / Admin |
| **Khách hàng** | `/api/khach-hang` | GET /lich-su, GET /tra-cuu, GET /danh-sach | Lịch sử đặt sân, tra cứu khách hàng, quản trị user | Token / Admin |
| **AI Copilot** | `/api/ai` | POST /consult, POST /reminder, POST /report | Trợ lý tư vấn sân trống, sinh tin nhắc lịch, tóm tắt báo cáo | Token / Staff / Admin |
| **Báo cáo** | `/api/bao-cao` | GET /tong-quan, GET /doanh-thu | Thống kê doanh thu, tỷ lệ lấp đầy sân, xuất dữ liệu | Admin |

---

## 3. CÁC QUY TẮC NGHIỆP VỤ LÕI (CORE BUSINESS RULES)

1. **Thuật toán Chống trùng lịch (Anti-Overbooking):**
   - Hai khoảng thời gian $[A, B)$ và $[C, D)$ giao thoa khi và chỉ khi: $(A < D) \land (B > C)$.
   - Bỏ qua các đơn đã hủy (`da_huy`) hoặc đơn giữ chỗ quá hạn 10 phút (`lock_expires_at < now`).
2. **Quy định Giữ chỗ và Tiền cọc:**
   - Khi khách tạo đơn đặt sân, hệ thống gán trạng thái `cho_coc` và khóa vị trí trong **10 phút**.
   - Khách thanh toán cọc cố định **100.000 VNĐ** (qua mã VietQR NAPAS 247). Sau khi xác nhận cọc, đơn chuyển sang `da_xac_nhan`.
   - Nếu quá 10 phút chưa cọc, Background Task (`lock_expiry_task`) tự động thu hồi slot.
3. **Thuật toán Biểu giá thuê sân:**
   - Khung giờ cao điểm (16:00 - 20:00): **350.000 VNĐ/giờ**.
   - Khung giờ thường (còn lại): **300.000 VNĐ/giờ**.
   - Hệ thống tự động bóc tách khoảng thời gian theo từng phút để tính toán chính xác tuyệt đối.

---

## 4. HƯỚNG DẪN KHỞI CHẠY ĐỘC LẬP & KIỂM THỬ

### Cài đặt môi trường
```powershell
cd backend
python -m pip install -r requirements.txt
```

### Khởi chạy Backend Server (Port 8000)
- **Windows:** Bấm đúp file `chay_backend.bat` hoặc gõ:
  ```powershell
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```

### Chạy bộ kiểm thử tự động (Unit Tests)
```powershell
cd backend
python -m pytest -v
```
