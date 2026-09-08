# HƯỚNG DẪN VẬN HÀNH HỆ THỐNG VICTORY ARENA v2.0
**Nhóm 20 — Lớp K23C CNTT | GVHD: ThS. Nguyễn Tuấn Anh**

Hệ thống được thiết kế theo kiến trúc phân tách chuyên nghiệp (**Decoupled Architecture**):
- **Phân hệ Backend (FastAPI RESTful API):** Cổng `8000` (Tài liệu OpenAPI tại `/docs`)
- **Phân hệ Frontend (Single Page Application):** Cổng `3000`

---

## 🚀 Cách 1: Khởi động 1-Click Toàn bộ Hệ thống (Khuyên dùng)

- Bấm đúp chuột vào file: **`CHAY_HE_THONG.bat`** (tại thư mục gốc).
- Kịch bản sẽ tự động:
  1. Kiểm tra môi trường Python và cài đặt thư viện phụ thuộc.
  2. Nạp dữ liệu cơ sở dữ liệu (5 sân bóng tiêu chuẩn, biểu giá và các tài khoản mẫu).
  3. Khởi động song song 2 cửa sổ tiến trình:
     - **Backend Server:** `http://127.0.0.1:8000`
     - **Frontend Web:** `http://127.0.0.1:3000`
  4. Tự động mở trình duyệt web tại `http://127.0.0.1:3000`.

---

## 💻 Cách 2: Khởi động Độc lập Từng Phân hệ

### 1. Khởi động Phân hệ Backend:
- **Tự động:** Bấm đúp vào `backend/chay_backend.bat`.
- **Thủ công qua Terminal:**
  ```powershell
  cd backend
  python -m pip install -r requirements.txt
  python seed_data.py
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Tài liệu API Backend:**
  - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 2. Khởi động Phân hệ Frontend:
- **Tự động:** Bấm đúp vào `frontend/chay_frontend.bat`.
- **Thủ công qua Terminal:**
  ```powershell
  cd frontend
  python -m http.server 3000 --bind 127.0.0.1
  # Hoặc dùng NodeJS: npm start
  ```
- **Giao diện Web:** [http://127.0.0.1:3000](http://127.0.0.1:3000)

---

## 🔑 Danh sách Tài khoản Kiểm thử Hệ thống

| Vai trò | Tên đăng nhập | Mật khẩu | Phạm vi chức năng chính |
|---|---|---|---|
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Quản trị sân bãi, biểu giá cao điểm/thường, quản lý người dùng, xem báo cáo doanh thu & AI |
| **Nhân viên sân (STAFF)** | `staff` | `staff123` | Check-in bàn giao sân, thêm dịch vụ nước uống/áo bib, quyết toán trả sân xuất hóa đơn |
| **Khách hàng mẫu (CUSTOMER)** | `tuanfc` | `tuan123` | Đặt lịch sân bóng, nhận mã VietQR thanh toán cọc, xem tab Sân đã đặt và Lịch sử |
| **Tài khoản cá nhân test** | `test01` | `123456` | Kiểm tra luồng đặt sân, tra cứu lịch thi đấu |

---

## 🧪 Chạy Bộ Kiểm thử Tự động (Unit Tests)

```powershell
cd backend
python -m pytest -v
```
*(Toàn bộ 11/11 ca kiểm thử chuyên sâu về Auth, Booking, Chống trùng lịch Overlap toán học, Giữ chỗ 10 phút, Hoàn tiền cọc và AI đều PASS 100%).*
