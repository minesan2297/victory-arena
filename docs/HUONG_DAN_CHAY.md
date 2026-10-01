# HƯỚNG DẪN VẬN HÀNH HỆ THỐNG VICTORY ARENA v2.0
**Nhóm 20 — Lớp K23C CNTT | GVHD: ThS. Nguyễn Tuấn Anh**

Hệ thống được thiết kế theo kiến trúc phân tách hiện đại (**Decoupled Architecture**), đồng thời hỗ trợ cả mô hình **All-in-One**:
- **Phân hệ Backend (FastAPI RESTful API):** Cổng `8000` (Tài liệu OpenAPI tại `/docs`, tích hợp sẵn Web SPA tại `/`)
- **Phân hệ Frontend (Single Page Application):** Cổng `3000` (hoặc Live Server cổng `5500`, hoặc chạy thẳng cổng `8000`)

---

## 🚀 Cách 1: Khởi động 1-Click Toàn bộ Hệ thống (Khuyên dùng)

- Bấm đúp chuột vào file: **`CHAY_HE_THONG.bat`** (tại thư mục gốc).
- Kịch bản sẽ tự động:
  1. Kiểm tra môi trường Python và tự cài đặt thư viện nếu máy mới chưa có.
  2. Nạp dữ liệu cơ sở dữ liệu (5 sân bóng tiêu chuẩn, biểu giá và các tài khoản mẫu).
  3. Khởi động song song 2 cửa sổ tiến trình (bind `0.0.0.0` để các máy khác cùng mạng truy cập được):
     - **Backend Server:** `http://127.0.0.1:8000` (hoặc `http://<IP-May-Ban>:8000`)
     - **Frontend Web:** `http://127.0.0.1:3000` (hoặc `http://<IP-May-Ban>:3000`)
  4. Tự động hiển thị địa chỉ IP mạng LAN và mở trình duyệt web tại `http://127.0.0.1:3000`.

---

## 🌐 Cách 2: Đưa Chương Trình Cho Người Khác Sử Dụng

### Trường hợp A: Người khác kết nối từ điện thoại / máy tính khác qua cùng mạng WiFi/LAN
1. Trên máy của bạn, chạy file **`CHAY_HE_THONG.bat`**.
2. Nhìn vào cửa sổ khởi động, hệ thống sẽ in ra địa chỉ IP của bạn (ví dụ: `http://192.168.1.15:3000` hoặc `http://192.168.1.15:8000`).
3. Gửi địa chỉ đó cho bạn bè/thầy cô mở trên trình duyệt của họ.
4. Hệ thống đã được cấu hình **Dynamic Hostname Interceptor** và **Full CORS**, các thiết bị khác đăng nhập mượt mà không bao giờ bị lỗi kết nối máy chủ!

### Trường hợp B: Người khác sao chép (copy) toàn bộ thư mục mã nguồn về máy tính của họ
1. Người đó chỉ cần mở thư mục và nhấp đúp vào **`CHAY_HE_THONG.bat`**.
2. Hệ thống sẽ tự động phát hiện Python, cài đặt thư viện thiếu (nếu có), tự động nạp cơ sở dữ liệu `mini_victory.db` đầy đủ tài khoản, và mở trình duyệt web lên sẵn sàng sử dụng.

---

## 💻 Cách 3: Khởi động Độc lập Từng Phân hệ

### 1. Khởi động Phân hệ Backend:
- **Tự động:** Bấm đúp vào `backend/chay_backend.bat`.
- **Thủ công qua Terminal:**
  ```powershell
  cd backend
  python -m pip install -r requirements.txt
  python seed_data.py
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Tài liệu API Backend & Web SPA:**
  - Giao diện Web All-in-One: [http://127.0.0.1:8000](http://127.0.0.1:8000)
  - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 2. Khởi động Phân hệ Frontend:
- **Tự động:** Bấm đúp vào `frontend/chay_frontend.bat`.
- **Thủ công qua Terminal:**
  ```powershell
  cd frontend
  python -m http.server 3000
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
*(Toàn bộ các ca kiểm thử chuyên sâu về Auth, Booking, Chống trùng lịch Overlap toán học, Giữ chỗ 10 phút, Hoàn tiền cọc và AI đều PASS 100%).*
