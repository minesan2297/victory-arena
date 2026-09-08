# PHÂN HỆ FRONTEND — VICTORY ARENA v2.0

* **Học phần:** Phân tích Thiết kế và Phát triển Hệ thống Thông tin (Bài kiểm tra thường xuyên 2)
* **Đơn vị phát triển:** Nhóm 20 — Lớp K23C CNTT
* **Giảng viên hướng dẫn:** ThS. Nguyễn Tuấn Anh
* **Công nghệ:** HTML5 Semantic, Cyberpunk/Glassmorphism CSS3, JavaScript ES6+ SPA, FontAwesome 6, Husky Guard Mascot SVG

---

## 1. CẤU TRÚC THƯ MỤC FRONTEND

```text
frontend/
├── css/
│   └── style.css            # Toàn bộ giao diện Cyberpunk, Glassmorphism, Responsive & Keyframe Animations
├── js/
│   ├── config.js            # Cấu hình API Base URL và Fetch URL Interceptor thông minh
│   └── app.js               # Logic nghiệp vụ SPA, State Management, JWT Auth, Role UI Guard
├── index.html               # Single Page Application Shell (Header, Navigation, Tabs, Modals)
├── package.json             # NPM package scripts (start, dev, serve)
├── chay_frontend.bat        # Script 1-Click chạy riêng Frontend trên cổng 3000
└── README.md                # Tài liệu kỹ thuật phân hệ Frontend
```

---

## 2. CƠ CHẾ KẾT NỐI API & FETCH INTERCEPTOR (`js/config.js`)

Frontend được thiết kế để có thể hoạt động độc lập hoàn toàn trên cổng `3000` (hoặc bất kỳ cổng nào) và kết nối tới Backend API trên cổng `8000`:

- **Tự động nhận diện môi trường:** Nếu cổng hiện tại là `8000`, `BASE_URL` là rỗng (same-origin). Nếu chạy trên cổng khác (`3000`, `5000`), `BASE_URL` tự động chuyển thành `http://127.0.0.1:8000`.
- **Fetch Interceptor trong suốt:** Mọi yêu cầu gọi mạng `fetch('/api/...')` trong `app.js` đều được tự động gắn tiền tố `http://127.0.0.1:8000` trước khi gửi đi, không cần sửa đổi mã nguồn nghiệp vụ.

---

## 3. CÁC PHÂN HỆ GIAO DIỆN CHÍNH (SPA TABS)

1. **Gác cổng bảo mật (Husky Guard Mascot & Login Overlay):**
   - Linh vật Husky tương tác trực tiếp theo trạng thái nhập mật khẩu.
   - Hỗ trợ Đăng nhập, Đăng ký và hiển thị thông tin tài khoản mẫu.
2. **Lịch Sân & Đặt Sân Trực Quan:**
   - Bộ chọn ngày trực quan, lưới khung giờ, thẻ sân bóng.
   - Modal hiển thị mã VietQR động NAPAS 247, nút Sandbox Test thanh toán cọc tức thì.
3. **Phân tách Tab Khách Hàng:**
   - **Sân Đã Đặt:** Hiển thị các trận đấu đang giữ chỗ (chờ cọc 10 phút) và đã xác nhận.
   - **Lịch Sử Đặt Sân:** Xem lại tất cả các đơn đã hoàn tất hoặc đã hủy, hỗ trợ in/xem chi tiết hóa đơn.
4. **Vận Hành & Thu Ngân (Dành cho Staff & Admin):**
   - Check-in bàn giao sân, thêm dịch vụ phát sinh (nước uống, thuê bóng, áo bib), thanh toán trả sân & xuất hóa đơn.
5. **AI Trợ Lý Thông Minh (Gemini 1.5 Flash):**
   - Chatbot tư vấn tìm sân trống theo ngôn ngữ tự nhiên.
   - Soạn tin nhắn thông báo trận đấu qua Zalo/SMS.
   - Phân tích báo cáo hiệu suất và đề xuất khuyến mãi khung giờ thấp điểm.
6. **Quản Trị Hệ Thống (Dành cho Admin):**
   - Quản lý danh sách sân bóng (CRUD), biểu giá thuê (cao điểm 350k/h, thường 300k/h).
   - Quản lý danh sách người dùng & khách hàng, điểm uy tín.

---

## 4. HƯỚNG DẪN KHỞI CHẠY ĐỘC LẬP

- **Cách 1 (Khuyên dùng trên Windows):** Bấm đúp file `chay_frontend.bat` để chạy server trên cổng `3000` và tự động mở trình duyệt.
- **Cách 2 (Sử dụng Python):**
  ```powershell
  python -m http.server 3000 --bind 127.0.0.1
  ```
- **Cách 3 (Sử dụng NodeJS / NPM):**
  ```powershell
  npm start
  ```
- Mở trình duyệt tại: `http://127.0.0.1:3000`
