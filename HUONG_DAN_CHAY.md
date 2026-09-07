# HƯỚNG DẪN CHẠY HỆ THỐNG VICTORY ARENA v2.0
**Nhóm 20 — K23C CNTT | GVHD: ThS. Nguyễn Tuấn Anh**

Thư mục này chứa **toàn bộ mã nguồn và dữ liệu độc lập** để chạy hệ thống Quản lý Sân thể thao cho thuê tích hợp AI.

---

## 🚀 Cách 1: Chạy nhanh bằng 1-Click (Khuyên dùng trên Windows)
- Nhấp đúp chuột vào file: **`CHAY_HE_THONG.bat`**
- File này sẽ tự động:
  1. Kiểm tra và cài đặt thư viện cần thiết.
  2. Nạp dữ liệu CSDL chuẩn 5 sân (3 Sân 7, 2 Sân 11).
  3. Khởi động máy chủ uvicorn tại địa chỉ: `http://127.0.0.1:8000`.

---

## 💻 Cách 2: Chạy thủ công qua Terminal (PowerShell / Command Prompt)

1. **Di chuyển vào thư mục này:**
   ```bash
   cd "C:\Users\ADMIN\.gemini\antigravity\scratch\sports_court_ai_mgmt\chuong_trinh_he_thong"
   ```

2. **Cài đặt thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Nạp dữ liệu mẫu ban đầu:**
   ```bash
   python seed_data.py
   ```

4. **Khởi chạy Server FastAPI:**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Mở trình duyệt Web:**
   - Truy cập giao diện ứng dụng: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Xem tài liệu Swagger API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔑 Tài khoản mẫu có sẵn trong hệ thống:
| Vai trò | Tên đăng nhập | Mật khẩu | Chức năng chính |
|---|---|---|---|
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Cấu hình sân bãi, giá, dịch vụ, xem báo cáo doanh thu & AI |
| **Nhân viên sân (STAFF)** | `staff` | `staff123` | Check-in, bán nước/áo bib, Check-out quyết toán POS |
| **Khách hàng 1** | `tuan_fc` | `tuan123` | Đặt lịch, giữ chỗ 10p, xem lịch sử đặt của mình |
| **Khách hàng 2** | `hai_nam` | `hai123` | Đặt lịch, tư vấn tìm sân qua AI Copilot |

---

## 🧪 Chạy bộ kiểm thử tự động (Pytest):
```bash
pytest -v
```
*(Hiện có 9/9 ca kiểm thử chuyên sâu về Auth, Booking, Chống trùng lịch, Khóa 10p, Hoàn cọc, AI và CRUD Sân bãi đạt 100% Passed).*
