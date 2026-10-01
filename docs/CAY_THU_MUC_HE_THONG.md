# 🌳 CÂY THƯ MỤC HỆ THỐNG QUẢN LÝ VÀ ĐẶT SÂN BÓNG VICTORY ARENA (v2.0)

> **Dự án:** Hệ thống Quản lý Sân thể thao cho thuê tích hợp AI (Victory Arena v2.0)  
> **Nhóm thực hiện:** Nhóm 20 — Lớp K23C CNTT  
> **Giảng viên hướng dẫn:** TS. Nguyễn Tuấn Anh  
> **Kiến trúc:** Layered Architecture chuẩn công nghiệp (Presentation SPA $\leftrightarrow$ RESTful API $\leftrightarrow$ Business Logic $\leftrightarrow$ Data Access)

---

## 1. Cấu Trúc Cây Thư Mục Hoàn Chỉnh (Sau Tái Cấu Trúc)

```text
chuong_trinh_he_thong/
│
├── 📜 CHAY_HE_THONG.bat            # Script 1-click khởi chạy song song Backend (8000) & Frontend (3000)
├── 📜 HUONG_DAN_CHAY.md            # Tài liệu hướng dẫn cài đặt môi trường & các bước chạy thử
├── 📜 README.md                    # Tài liệu tổng quan đề tài, kiến trúc, công nghệ và phân công nhóm
├── 📜 requirements.txt             # Tham chiếu gốc (-r backend/requirements.txt) tránh trùng lặp
├── ⚙️ .gitignore                   # Cấu hình bảo mật: Bỏ qua *.db, cache, .env khỏi Git
│
├── 📂 docs/                        # TÀI LIỆU DỰ ÁN & BÁO CÁO KỸ THUẬT
│   ├── 📄 CAY_THU_MUC_HE_THONG.md  # Tài liệu kiến trúc & cấu trúc phân tầng chi tiết
│   └── 📄 HUONG_DAN_CHAY.md        # Hướng dẫn chi tiết dành cho giảng viên/hội đồng
│
├── 📂 backend/                     # PHÂN HỆ BACKEND RESTFUL API SERVICE
│   ├── 📜 chay_backend.bat         # Script khởi chạy riêng FastAPI Backend (0.0.0.0:8000)
│   ├── 📜 requirements.txt         # Khai báo thư viện Backend (FastAPI, SQLAlchemy, Gemini AI,...)
│   ├── 📜 README.md                # Tài liệu API & hướng dẫn riêng cho Backend
│   ├── ⚙️ .env.example             # File cấu hình biến môi trường mẫu chuẩn
│   │
│   ├── 📂 data/                    # NƠI LƯU CƠ SỞ DỮ LIỆU CỤC BỘ (Đã đưa vào .gitignore)
│   │   └── 🗄️ mini_victory.db      # Database SQLite chính thức (Không commit lên Git)
│   │
│   ├── 📂 scripts/                 # CÁC SCRIPT TIỆN ÍCH DỮ LIỆU
│   │   ├── 📄 seed_data.py         # Nạp dữ liệu mẫu ban đầu: Sân 7, Sân 11, Bảng giá, Tài khoản
│   │   └── 📄 seed_demo_bookings.py# Sinh N đơn đặt sân demo linh hoạt phục vụ test tải
│   │
│   ├── 📂 app/                     # MÃ NGUỒN CHÍNH CỦA BACKEND
│   │   ├── 📄 main.py              # Entry point: Mount Router, Static Files, CORS, Lifespan
│   │   ├── 📄 config.py            # Quản lý cấu hình tập trung (Pydantic BaseSettings đọc .env)
│   │   ├── 📄 database.py          # SQLAlchemy Engine, SessionLocal, Dependency get_db
│   │   ├── 📄 __init__.py
│   │   │
│   │   ├── 📂 auth/                # MODULE XÁC THỰC & PHÂN QUYỀN
│   │   │   ├── 📄 security.py      # Băm mật khẩu (Bcrypt), ký & giải mã JWT Token
│   │   │   ├── 📄 dependencies.py  # Middleware kiểm tra vai trò: get_current_user, require_admin,...
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📂 models/              # LỚP THỰC THỂ CƠ SỞ DỮ LIỆU (16 Bảng ORM chuẩn 3NF)
│   │   │   ├── 📄 enums.py         # Các enum trạng thái: VaiTro, TrangThaiSan, TrangThaiDatSan,...
│   │   │   ├── 📄 tai_khoan.py     # Bảng: TaiKhoan, VaiTro (Customer, Staff, Admin)
│   │   │   ├── 📄 san.py           # Bảng: San, LoaiSan, BangGia
│   │   │   ├── 📄 dat_san.py       # Bảng: DatSan, LichDat (Chống trùng lịch)
│   │   │   ├── 📄 hoa_don.py       # Bảng: HoaDon, ThanhToan, CheckIn
│   │   │   ├── 📄 dich_vu.py       # Bảng: DanhMucDichVu, SuDungDichVu (Nước, phụ kiện)
│   │   │   ├── 📄 bao_cao.py       # Bảng: BaoCao (Doanh thu, tỷ lệ lấp đầy sân)
│   │   │   ├── 📄 thong_bao.py     # Bảng: ThongBao (Thông báo gửi người dùng)
│   │   │   ├── 📄 ai_models.py     # Bảng: AIConfig, AIRequest (Nhật ký gọi Gemini AI)
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📂 schemas/             # LỚP DTO KIỂM CHUẨN DỮ LIỆU ĐẦU VÀO (Pydantic v2)
│   │   │   ├── 📄 auth_schema.py   # Schema: Login, Register, DoiMatKhauRequest (TC1-TC7)
│   │   │   ├── 📄 san_schema.py    # Schema: SanResponse, BangGiaCreate
│   │   │   ├── 📄 dat_san_schema.py# Schema: DatSanCreate, XacNhanCoc, SlotInfo
│   │   │   ├── 📄 hoa_don_schema.py# Schema: CheckInRequest, CheckOutRequest, HoaDonResponse
│   │   │   ├── 📄 dich_vu_schema.py# Schema: DichVuResponse, SuDungDVCreate
│   │   │   ├── 📄 ai_schema.py     # Schema: AIConsultRequest, AIReminderRequest
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📂 services/            # LỚP LOGIC NGHIỆP VỤ CỐT LÕI (Business Logic)
│   │   │   ├── 📄 auth_service.py  # Nghiệp vụ tài khoản, đổi mật khẩu đúng DB session
│   │   │   ├── 📄 san_service.py   # Nghiệp vụ quản lý sân và khung giờ
│   │   │   ├── 📄 dat_san_service.py # Nghiệp vụ đặt sân, chống overbooking, tính cọc 30%
│   │   │   ├── 📄 hoa_don_service.py # Nghiệp vụ tính hóa đơn (tiền sân + dịch vụ - cọc)
│   │   │   ├── 📄 dich_vu_service.py # Nghiệp vụ dịch vụ gia tăng
│   │   │   ├── 📄 ai_service.py    # AI Engine tích hợp Gemini 1.5 Flash + Fallback
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📂 tasks/               # LỚP BACKGROUND TASKS & CRON SCHEDULER
│   │   │   ├── 📄 lock_expiry.py   # Tự động quét và hủy các đơn giữ chỗ quá 10 phút chưa cọc
│   │   │   └── 📄 __init__.py
│   │   │
│   │   └── 📂 routers/             # LỚP RESTFUL API ENDPOINTS
│   │       ├── 📄 auth_router.py   # /api/auth (login, register, change-password)
│   │       ├── 📄 san_router.py    # /api/san (danh sách sân, bảng giá)
│   │       ├── 📄 dat_san_router.py# /api/dat-san (timeline matrix, đặt chỗ, hủy lịch)
│   │       ├── 📄 van_hanh_router.py # /api/van-hanh (check-in, check-out, xuất hóa đơn)
│   │       ├── 📄 dich_vu_router.py# /api/dich-vu (gọi nước, thuê đồ)
│   │       ├── 📄 khach_hang_router.py # /api/khach-hang (tra cứu lịch sử đặt sân)
│   │       ├── 📄 bao_cao_router.py# /api/bao-cao (dashboard thống kê doanh thu)
│   │       ├── 📄 ai_router.py     # /api/ai (AI tư vấn tìm sân, nhắc lịch thi đấu)
│   │       └── 📄 __init__.py
│   │
│   └── 📂 tests/                   # BỘ KIỂM THỬ TỰ ĐỘNG PYTEST (44 Tests, 100% Passed)
│       ├── 📄 conftest.py          # Fixtures In-Memory SQLite cô lập: client_and_db, staff_client,...
│       ├── 📄 test_auth.py         # 16 tests: Xác thực, bảo mật, đổi mật khẩu TC1-TC7
│       ├── 📄 test_booking.py      # 14 tests: Đặt sân, chống overbooking, khóa bảo trì
│       ├── 📄 test_van_hanh_va_hoa_don.py # 4 tests: Check-in/out, tính tiền dịch vụ, hủy giữ chỗ 10p, báo cáo
│       ├── 📄 test_ai.py           # 10 tests: Test case AI consult, nhắc lịch, fallback engine
│       └── 📄 __init__.py
│
└── 📂 frontend/                    # GIAO DIỆN NGƯỜI DÙNG SPA (Single Page Application)
    ├── 📜 chay_frontend.bat        # Script chạy máy chủ HTTP tĩnh (Port 3000)
    ├── 📜 README.md                # Tài liệu giao diện người dùng
    ├── 📜 package.json             # Cấu hình meta frontend
    ├── 📄 index.html               # Trang giao diện chính SPA (Dashboard, Timeline Grid, Modal Đổi MK)
    │
    ├── 📂 css/
    │   └── 📄 style.css            # Stylesheet Cyberpunk / Glassmorphism, Responsive
    │
    └── 📂 js/
        ├── 📄 config.js            # Tự động nhận diện hostname/IP kết nối API linh hoạt
        └── 📄 app.js               # Logic điều khiển giao diện, gọi API, VietQR Sandbox, Chatbot AI
```

---

## 2. Bảng Đối Soát Cải Tiến So Với Nhận Xét Đánh Giá

| Tiêu chí | Trước khi sửa | Sau khi sửa (Hiện tại) | Lợi ích |
| :--- | :--- | :--- | :--- |
| **Bảo mật CSDL (`.db`)** | 2 file `.db` bị theo dõi trên Git | Đưa vào `backend/data/`, thêm `*.db` vào `.gitignore`, untrack khỏi Git | Không lộ dữ liệu thật, không xung đột git merge |
| **Trùng lặp file cấu hình** | `requirements.txt` & `.env.example` lặp lại ở 2 nơi | Gốc trỏ `-r backend/requirements.txt`, `.env.example` chuẩn hóa duy nhất ở `backend/` | Đồng bộ 100%, không bị lệch version thư viện |
| **Phân tách Models** | `BaoCao` và `ThongBao` nhét chung vào `ai_models.py` | Tách thành `bao_cao.py`, `thong_bao.py`, `ai_models.py` riêng biệt | Đúng nguyên lý Single Responsibility (SRP) |
| **Phân loại Task nền** | `lock_expiry_task.py` đặt trong `services/` | Tạo phân hệ `backend/app/tasks/` riêng cho scheduler & background tasks | Tách biệt nghiệp vụ người dùng với tác vụ chạy ngầm |
| **Tổ chức Seed Data** | Để file seed lung tung ở root `backend/` | Gom vào `backend/scripts/`, có script `seed_demo_bookings.py` nhận tham số số lượng | Thư mục gọn gàng, chuyên nghiệp |
| **Kiến trúc Kiểm thử** | Fixture lặp lại, thiếu test hóa đơn & hủy 10 phút | Có `conftest.py` in-memory dùng chung; thêm `test_van_hanh_va_hoa_don.py` | **44/44 tests Passed**, phủ toàn diện từ đặt sân, dịch vụ đến hóa đơn |
| **Tài liệu & Thư mục** | File `.md` phân tán | Tạo thư mục `docs/` lưu trữ tài liệu hệ thống | Dễ tìm kiếm, sẵn sàng nộp báo cáo cho giảng viên |
