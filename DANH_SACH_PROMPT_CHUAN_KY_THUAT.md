# BỘ PROMPT CHUẨN CẤU TRÚC KỸ THUẬT CHO BÀI TẬP LỚN / BÀI TẬP MÔN HỌC
**Môn học:** Ứng dụng Trí tuệ Nhân tạo (AI Application)  
**Học phần:** Học kỳ 1 - Năm 3  
**Nhóm thực hiện:** Nhóm 20 - Lớp K23C CNTT  
**Đề tài bài tập lớn:** Hệ Thống Quản Lý Sân Thể Thao Cho Thuê Tích Hợp AI (Mini Victory Arena v2.0)  

---
### 📐 Cấu trúc Prompt kỹ thuật chuẩn áp dụng:
`[ROLE/VAI TRÒ] + [CONTEXT/BỐI CẢNH DỰ ÁN MÔN HỌC] + [TASK/NHIỆM VỤ CHI TIẾT] + [CONSTRAINTS/RÀNG BUỘC KỸ THUẬT] + [OUTPUT/KẾT QUẢ ĐẦU RA]`

---

## PROMPT 1: TÁCH CHƯƠNG TRÌNH THÀNH FRONTEND VÀ BACKEND CHUẨN MÔ HÌNH CLIENT-SERVER

```text
[Role]: Bạn là một lập trình viên Fullstack Web hỗ trợ sinh viên thực hành bài tập lớn môn học.
[Context]: Nhóm em đang làm bài tập môn Ứng dụng Trí tuệ Nhân tạo với đề tài "Hệ thống quản lý sân thể thao cho thuê tích hợp AI - Mini Victory v2.0". Hiện tại source code đang để chung tất cả file Python và giao diện trong một thư mục, thầy giáo bộ môn yêu cầu phải tách biệt rõ ràng theo kiến trúc Client - Server để chấm điểm thực hành.
[Task]: Hãy tái cấu trúc lại chương trình thành 2 thư mục độc lập `frontend/` và `backend/`:
  1. Thư mục `backend/`: Sử dụng Python FastAPI theo mô hình phân tầng:
     - `app/routers/`: Tách riêng các API endpoints (`auth_router.py`, `san_router.py`, `dat_san_router.py`, `van_hanh_router.py`, `ai_router.py`).
     - `app/services/`: Chứa các hàm xử lý logic nghiệp vụ và tích hợp mô hình AI.
     - `app/models/`: Chứa các bảng cơ sở dữ liệu SQLAlchemy (TaiKhoan, San, DatSan, HoaDon, DichVu, ThongBao,...).
     - `app/schemas/`: Định nghĩa Pydantic models để validate dữ liệu đầu vào/ra.
     - Cấu hình CORS middleware cho phép frontend gọi sang cổng 8000.
  2. Thư mục `frontend/`:
     - `index.html`: Cấu trúc giao diện người dùng.
     - `css/style.css`: Giao diện phong cách Esports Thể thao hiện đại.
     - `js/app.js` và `js/config.js`: Xử lý tương tác DOM và gọi dữ liệu từ backend thông qua Fetch API.
[Constraints]: Giữ nguyên toàn bộ dữ liệu mẫu (seed data) và logic nghiệp vụ hiện có; mã nguồn phân tách rõ ràng, sạch sẽ, có chú thích để nhóm em dễ dàng thuyết trình trước lớp.
[Output]: Bản đồ cấu trúc thư mục mới cùng hướng dẫn các câu lệnh chạy độc lập backend (port 8000) và frontend (port 3000).
```

---

## PROMPT 2: HOÀN THIỆN MODULE THÔNG BÁO HỆ THỐNG THỜI GIAN THỰC

```text
[Role]: Bạn là một lập trình viên Fullstack Web.
[Context]: Trong bài tập môn học quản lý sân bóng, nhóm em đã thiết kế bảng CSDL `thong_bao` (lưu các thông tin: thong_bao_id, tai_khoan_id, tieu_de, noi_dung, loai, da_doc, ngay_gui) nhưng icon chuông trên thanh Topbar và danh sách thông báo trên Dashboard hiện chỉ là giao diện tĩnh, chưa kết nối dữ liệu thật.
[Task]: Hãy lập trình kết nối hoàn chỉnh chức năng thông báo từ Backend sang Frontend:
  1. Backend (FastAPI):
     - Xây dựng API `GET /api/thong-bao`: Trả về danh sách thông báo của tài khoản đang đăng nhập theo JWT token.
     - Xây dựng API `PUT /api/thong-bao/{id}/read`: Đánh dấu một thông báo là đã đọc (`da_doc = True`).
     - Xây dựng API `DELETE /api/thong-bao/clear-all`: Xóa toàn bộ thông báo của người dùng.
  2. Frontend (HTML/JS):
     - Viết hàm `fetchNotifications()` thiết lập cơ chế polling tự động mỗi 20 giây để kiểm tra thông báo mới.
     - Hiển thị số lượng thông báo chưa đọc lên Badge đỏ ở icon quả chuông topbar (`#topbar-notif-badge`).
     - Khi bấm vào chuông, mở dropdown hiển thị danh sách thông báo kèm icon phân loại (AI tư vấn, Đặt cọc, Bàn giao sân) và thời gian tương đối (ví dụ: 'vừa xong', '5 phút trước').
     - Bổ sung nút "Đánh dấu tất cả đã đọc" và "Xóa tất cả".
[Constraints]: Truyền đúng Bearer Token trong header HTTP; nếu không có thông báo nào phải hiển thị trạng thái trống (Empty State) thẩm mỹ.
[Output]: Đoạn mã bổ sung vào router backend và các hàm JavaScript xử lý hiển thị tương ứng trong `frontend/js/app.js`.
```

---

## PROMPT 3: THIẾT LẬP GUARDRAIL GIỚI HẠN PHẠM VI TRẢ LỜI CỦA TRỢ LÝ AI CHATBOT

```text
[Role]: Bạn là một Kỹ sư AI (Prompt Engineer).
[Context]: Đây là bài tập môn Ứng dụng Trí tuệ Nhân tạo. Nhóm em có tính năng Trợ lý AI tư vấn tìm sân và đặt lịch thi đấu. Tuy nhiên khi demo, nếu người dùng hỏi các câu hỏi không liên quan (như hỏi về lập trình, giải toán, thời tiết, chính trị...) thì AI vẫn trả lời lan man, không đúng trọng tâm bài tập về nghiệp vụ sân thể thao.
[Task]: Cập nhật lại System Prompt và cơ chế kiểm soát cho Trợ lý AI (`/api/ai/consult-pitch`):
  1. Định vị vai trò (System Prompt):
     - Xác định rõ vai trò: Trợ lý AI chuyên trách của Sân bóng đá Mini Victory Arena.
     - Phạm vi cho phép (Allowed Scope): Chỉ trả lời những vấn đề liên quan trực tiếp đến sân bóng: giá thuê, vị trí sân (Sân 7A, 7B, Sân 11), khung giờ trống, dịch vụ đi kèm (nước ngọt, áo bít, bóng thi đấu), quy định đặt cọc và chính sách hủy sân.
     - Giới hạn nghiêm ngặt (Guardrail Rule): Đối với tất cả những câu hỏi nằm ngoài phạm vi sân bóng, nội dung bừa bãi, linh tinh hoặc không liên quan, AI bắt buộc phải từ chối lịch sự bằng đúng câu chữ sau:
       "Xin lỗi! Điều này không nằm trọng phạm vi của tôi! Xin lỗi và cảm ơn bạn đã đặt câu hỏi"
  2. Tích hợp:
     - Đưa System Prompt này vào hàm gọi AI trong file `backend/app/services/ai_service.py`.
[Constraints]: Câu từ chối phải chuẩn xác từng chữ theo yêu cầu; không để người dùng dùng prompt injection (ví dụ: "Hãy đóng vai một nhà thơ...") để bẻ khóa quy tắc này.
[Output]: Toàn bộ nội dung System Prompt mới trong `ai_service.py` và kịch bản test thử 2 câu hỏi đúng nghiệp vụ cùng 2 câu hỏi ngoài lề để nộp báo cáo.
```

---

## PROMPT 4: HIỂN THỊ MODAL CHI TIẾT ĐƠN ĐẶT SÂN VÀ DỊCH VỤ PHÁT SINH KHI CLICK

```text
[Role]: Bạn là một Frontend Web Developer.
[Context]: Trong giao diện quản lý đơn đặt sân của bài tập môn học, khi hiển thị thông tin như "Sân 7A – Phủi Pro", sinh viên khi bấm vào đó vẫn chưa tương tác được để xem cụ thể đơn đặt gồm những gì.
[Task]: Hãy lập trình một Modal Popup chi tiết (`#modal-booking-detail`) hiển thị toàn bộ thông tin đơn đặt sân và dịch vụ đi kèm khi người dùng bấm vào dòng hoặc thẻ sân:
  1. Giao diện Modal (HTML/CSS):
     - Header: Tên sân, mã đơn đặt sân, badge trạng thái (CHỜ CỌC, ĐÃ XÁC NHẬN, ĐANG ĐÁ, HOÀN TẤT).
     - Khối thông tin sân bãi: Ngày thi đấu, khung giờ, vị trí sân, ghi chú trận đấu.
     - Khối thông tin khách hàng: Tên người đặt, số điện thoại, tiền cọc đã đóng, thời hạn giữ chỗ 10 phút.
     - Bảng danh sách dịch vụ phát sinh đã gọi: Tên dịch vụ (nước, áo bít, bóng), danh mục, đơn vị tính, đơn giá, số lượng, thành tiền.
     - Dòng tổng kết tài chính: Tổng tiền dịch vụ và Tổng tiền còn lại cần thanh toán khi trả sân.
     - Footer: Nút Đóng modal cùng các nút tác vụ theo phân quyền (Check-in, Check-out, QR Cọc, Hủy).
  2. Xử lý sự kiện (JavaScript):
     - Viết hàm `window.showBookingDetailModal(maDon)` gọi API lấy chi tiết đơn và dịch vụ từ backend rồi đổ vào modal.
     - Gắn sự kiện `onclick` cho các thẻ ca đá và dòng dữ liệu sân trong bảng danh sách.
[Constraints]: Có hiệu ứng animation mờ nền, hỗ trợ đóng modal bằng nút `X`, nút Đóng, phím ESC hoặc click ngoài backdrop.
[Output]: Khối HTML modal trong `frontend/index.html` và đoạn mã JS xử lý gán sự kiện trong `frontend/js/app.js`.
```

---

## PROMPT 5: TẠO ĐỘ TRỄ GIẢ LẬP KHI TẢI LỊCH SÂN ĐỂ TĂNG TÍNH CHÂN THẬT

```text
[Role]: Bạn là một UI/UX Frontend Developer.
[Context]: Khi sinh viên bấm chọn sân bóng trên thanh lọc (filter) để xem lịch trống, do chạy local nên dữ liệu hiện ra tức thì (<5ms), nhìn rất cứng nhắc và không giống như một hệ thống thực tế đang gửi request truy vấn cơ sở dữ liệu qua Internet.
[Task]: Hãy tinh chỉnh lại hàm `fetchSchedule()` để tạo trải nghiệm tải dữ liệu chân thật:
  1. Thêm độ trễ giả lập (Artificial Delay):
     - Dùng `Promise.all` kết hợp giữa lệnh gọi API thật và một khoảng chờ `setTimeout` từ 1 đến 2 giây (khuyến nghị 1.2s - 1.5s).
  2. Trạng thái hiển thị trong lúc chờ:
     - Lập tức xóa danh sách cũ, hiển thị khối hiệu ứng radar quét sân đang hoạt động.
     - Hiển thị 4 - 6 khung xương thẻ ca thi đấu (Skeleton Card) với hiệu ứng quét ánh sáng lấp lánh (shimmer effect).
  3. Khi có kết quả:
     - Render danh sách ca thi đấu chính thức với hiệu ứng fade-in mượt mà.
[Constraints]: Không làm đơ (freeze) giao diện người dùng; hủy bỏ timeout an toàn nếu người dùng chuyển đổi tab nhanh.
[Output]: Mã nguồn hàm `fetchSchedule()` đã được tối ưu trong `frontend/js/app.js`.
```

---

## PROMPT 6: THIẾT KẾ LẠI HIỆU ỨNG QUAY VÒNG LOADING THEO PHONG CÁCH RADAR STADIUM

```text
[Role]: Bạn là một CSS UI Specialist.
[Context]: Hiệu ứng quay vòng khi tải lịch sân hiện tại chỉ là icon spinner xoay mặc định của trình duyệt, nhìn thô sơ và chưa có hoạt ảnh animation sống động đúng chất thể thao điện tử của bài tập môn học.
[Task]: Hãy thiết kế lại component hiệu ứng quay vòng tải dữ liệu thành "Radar Quét Khung Giờ Sân Vận Động" (Stadium Radar Loader):
  1. Hoạt ảnh Animation (CSS Keyframes):
     - Vòng ngoài (`.radar-ring-outer`): Đường tròn nét đứt màu xanh neon Cyan `#00f0ff`, đường kính ~60px, xoay thuận chiều kim đồng hồ liên tục.
     - Vòng trong (`.radar-ring-inner`): Vòng gradient bán nguyệt xoay ngược chiều kim đồng hồ tạo cảm giác đa tầng công nghệ.
     - Tâm trung tâm (`.radar-center-ball`): Icon quả bóng đá `fa-futbol` phát sáng và co giãn nhẹ (breathing pulse) nhịp nhàng.
  2. Nội dung thông báo đi kèm:
     - Dòng chữ trạng thái: "Đang đồng bộ sơ đồ ca thi đấu từ máy chủ..." với hiệu ứng chữ phát sáng neon và dấu chấm nhảy nhịp (dot bounce).
[Constraints]: Viết bằng CSS thuần `@keyframes`, không dùng thư viện nặng bên ngoài, tối ưu hiệu năng render 60fps trên trình duyệt.
[Output]: Toàn bộ CSS keyframes đưa vào `frontend/css/style.css` và template HTML hiển thị trong `frontend/js/app.js`.
```

---

## PROMPT 7: BỔ SUNG HIỆU ỨNG TƯ DUY NƠ-RON CHO CẢ TRỢ LÝ AI VÀ BÁO CÁO AI

```text
[Role]: Bạn là một Frontend Developer chuyên về giao diện Trí tuệ Nhân tạo.
[Context]: Trong bài tập môn AI, hai chức năng cốt lõi là Trợ lý AI (tư vấn tìm sân) và Báo cáo AI (phân tích doanh thu & đề xuất tỷ lệ lấp đầy) khi người dùng bấm gửi yêu cầu thì chỉ hiện thông báo chờ đơn giản, chưa làm nổi bật được yếu tố "AI đang xử lý thông minh".
[Task]: Xây dựng hiệu ứng "Tư duy Nơ-ron Nhân tạo" (Neural Thinking Animation) cho cả 2 chức năng này:
  1. Trợ lý AI Chatbot:
     - Khi user gửi câu hỏi, hiển thị khối tin nhắn tạm của AI với icon bộ não `fa-brain` phát sáng nhịp nhàng, 3 chấm nơ-ron lan tỏa và dòng chữ "AI đang suy nghĩ và tra cứu lịch sân phù hợp...".
  2. Báo cáo Doanh thu & Tối ưu AI:
     - Thiết kế khối hiển thị trạng thái phân tích: Vòng xoay nơ-ron đa tầng, thanh tiến trình (Progress Bar) tăng dần từ 25% -> 55% -> 85% -> 100%.
     - Thay đổi chữ thông điệp động theo từng mốc thời gian:
       + "Đang trích xuất dữ liệu doanh thu 7 ngày qua..."
       + "Đang tính toán tỷ lệ lấp đầy & phân loại khung giờ cao điểm..."
       + "AI đang sinh chiến lược khuyến mãi giờ thấp điểm..."
       + "Hoàn tất! Đang kết xuất báo cáo thông minh..."
     - Có khung Skeleton tóm tắt mờ bên dưới trước khi nội dung thật hiển thị.
[Constraints]: Đồng bộ thời gian hiển thị animation từ 1.5s - 1.8s để người dùng kịp quan sát các bước phân tích logic của AI.
[Output]: Mã nguồn cập nhật trong hàm `handleChatbotSubmit()` và `handleAIReport()` trong `frontend/js/app.js`.
```

---

## PROMPT 8: SỬA LỖI TÍNH TOÁN VÀ ĐỊNH DẠNG TỔNG TIỀN DỊCH VỤ

```text
[Role]: Bạn là một Web Developer phụ trách kiểm thử và sửa lỗi (Bug Fixer).
[Context]: Trong modal chi tiết đơn đặt sân của hệ thống, phần tổng tiền dịch vụ đang bị tính toán sai: khi cộng dồn bị lỗi hiển thị `NaNđ` hoặc không khớp với giá tiền các dịch vụ nước uống, áo đấu mà khách đã gọi thêm.
[Task]: Hãy kiểm tra và lập trình lại chính xác logic tính toán tiền dịch vụ trong frontend:
  1. Chuẩn hóa dữ liệu đầu vào:
     - Trong mảng dịch vụ phát sinh, thuộc tính đơn giá có thể mang tên `don_gia` hoặc `don_gia_tai_ban`. Cần lấy giá trị an toàn: `Number(item.don_gia ?? item.don_gia_tai_ban ?? 0)`.
     - Số lượng: `Number(item.so_luong || 1)`.
  2. Công thức tính toán:
     - Thành tiền mỗi món: `thanhTien = donGia * soLuong`.
     - Tổng tiền dịch vụ: `tongDichVu = sum(thanhTien)` tính bằng hàm `.reduce()`.
     - Số tiền còn phải trả tại quầy: `tienConLai = Number(tienSan) + tongDichVu - Number(tienCocDaTra)`.
  3. Định dạng hiển thị:
     - Định dạng dấu chấm hàng nghìn bằng `.toLocaleString('vi-VN') + 'đ'` cho tất cả các trường: đơn giá, thành tiền, tổng tiền dịch vụ và tổng thanh toán.
[Constraints]: Xử lý tuyệt đối không để xuất hiện giá trị `NaN` hoặc số âm; hiển thị rõ ràng thông báo nếu trận đấu chưa sử dụng dịch vụ nào.
[Output]: Đoạn mã logic đã chỉnh sửa trong hàm hiển thị modal chi tiết đặt sân tại `frontend/js/app.js`.
```

---

## PROMPT 9: THIẾT KẾ MODAL HIỂN THỊ HỒ SƠ THÔNG TIN CÁ NHÂN NGƯỜI DÙNG

```text
[Role]: Bạn là một Frontend UI/UX Developer.
[Context]: Trên giao diện bài tập quản lý sân bóng, ở góc trên Topbar ("Xin chào, Nguyen Van C") và góc dưới Sidebar (khung user panel), hiện tại người dùng bấm vào không có phản hồi gì. Nhóm em muốn khi bấm vào bất kỳ chỗ nào trong hai vị trí này sẽ bật ra một Modal hiển thị đầy đủ thông tin cá nhân đã đăng ký.
[Task]: Thiết kế và tích hợp Modal Hồ sơ Cá nhân (`#modal-user-profile`):
  1. Điểm kích hoạt tương tác (Triggers):
     - Khung User Panel ở Sidebar (`#sidebar-user-panel`): Có hiệu ứng hover viền sáng neon, con trỏ chuột dạng pointer, bấm vào để mở modal. Chú ý: Nút icon Đăng xuất nhỏ bên cạnh phải có `event.stopPropagation()` để khi bấm đăng xuất không bị kích hoạt nhầm mở modal.
     - Cụm thông tin trên Topbar (`#topbar-user-btn`): Bấm vào cụm tên và avatar để mở modal.
  2. Giao diện Modal (Thẻ Hồ Sơ Cá Nhân):
     - Banner đầu thẻ thể thao hiện đại, avatar lớn có icon phân biệt theo vai trò (ADMIN: khiên đỏ, STAFF: cà vạt cam, CUSTOMER: cầu thủ xanh neon).
     - Hiển thị đầy đủ thông tin đã đăng ký: Họ và tên, Tên đăng nhập (`@username`), Số điện thoại (kèm tem 'Đã xác minh'), Địa chỉ Email, Điểm uy tín đặt sân (ví dụ: `100 / 100 ⭐`), Mã định danh tài khoản (`#TK-03`), và trạng thái hoạt động ("🟢 Đang hoạt động").
     - Footer: Có nút Đóng và nút Đăng Xuất nhanh tài khoản.
  3. Xử lý JavaScript:
     - Viết hàm `window.showUserProfileModal()` lấy dữ liệu từ biến toàn cục `currentUser` (hoặc gọi API `/api/auth/me`) và đổ vào các phần tử tương ứng trong modal.
     - Đóng modal khi bấm nút `X`, nút Đóng ở footer, phím ESC hoặc click ra ngoài vùng nền mờ.
[Constraints]: Giao diện tương thích tốt, hiệu ứng mở modal mượt mà bằng CSS Keyframes; dữ liệu hiển thị chính xác theo tài khoản đang đăng nhập.
[Output]: Khối HTML modal trong `frontend/index.html`, style trong `frontend/css/style.css` và hàm JavaScript trong `frontend/js/app.js`.
```

---

## PROMPT 10: KIỂM THỬ VÀ CHẶN LỖI KÝ TỰ DẤU, KHOẢNG TRẮNG Ở ĐĂNG KÝ VÀ ĐĂNG NHẬP

```text
[Role]: Bạn là một Lập trình viên Fullstack Web & Tester kiểm thử phần mềm.
[Context]: Trong bài tập môn học Ứng dụng AI, nhóm em đang rà soát lại module Xác thực tài khoản (Đăng nhập & Đăng ký). Khi test các ca nhập liệu thực tế, nhóm em phát hiện người dùng có thể gõ tên đăng nhập có dấu tiếng Việt (như 'nguyễn văn a'), chèn khoảng trắng ở giữa ('user 123') hoặc đặt mật khẩu chỉ toàn dấu cách ('      '). Ngoài ra, khi đăng nhập lỡ copy dính dấu cách ở đầu/cuối ('  user1  ') thì hệ thống báo lỗi không đăng nhập được.
[Task]: Hãy kiểm thử toàn diện và xử lý triệt để các lỗi về ký tự có dấu và khoảng trắng cho cả Backend lẫn Frontend:
  1. Backend (Pydantic Schema & FastAPI Handler):
     - Tại `app/schemas/auth_schema.py`:
       + `ten_dang_nhap`: Thêm `@field_validator` kiểm tra biểu thức chính quy `^[a-zA-Z0-9_-]+$`. Chặn tuyệt đối dấu tiếng Việt, khoảng trắng và ký tự đặc biệt. Tự động `.strip().lower()` để đồng nhất chữ thường.
       + `mat_khau`: Bắt buộc độ dài tối thiểu 6 ký tự thực tế, cấm hoàn toàn chứa khoảng trắng (không cho phép mật khẩu chỉ toàn dấu cách).
       + `so_dien_thoai`: Ràng buộc đúng 10 chữ số chuẩn đầu số di động Việt Nam (`03`, `05`, `07`, `08`, `09`).
       + `ten_dang_nhap` khi Đăng nhập: Tự động `.strip()` cắt bỏ khoảng trắng thừa đầu/cuối để người dùng lỡ copy-paste vẫn đăng nhập thành công.
     - Tại `app/main.py`: Bổ sung `validation_exception_handler` để khi vi phạm định dạng thì trả về thông báo lỗi tiếng Việt thân thiện, rõ ràng thay vì mã lỗi kỹ thuật 422 mặc định.
  2. Frontend (`frontend/js/app.js`):
     - Bổ sung validate ngay trên trình duyệt trước khi gửi request: Kiểm tra tên đăng nhập bằng regex không dấu/không cách, kiểm tra mật khẩu không chứa khoảng trắng, kiểm tra số điện thoại.
     - Nếu vi phạm: Bôi đỏ viền ô nhập liệu (`input-invalid`), hiển thị thông báo lỗi rõ ràng trên thẻ `auth-alert` và rung lắc nhẹ form để người dùng dễ nhận biết.
  3. Viết bộ kiểm thử tự động (Unit Test):
     - Tạo file `tests/test_auth.py` viết 8 ca kiểm thử pytest: Đăng ký hợp lệ, từ chối tên có dấu tiếng Việt, từ chối tên có khoảng trắng, từ chối mật khẩu có khoảng trắng/toàn dấu cách, từ chối số điện thoại sai chuẩn, đăng nhập tự động trim khoảng trắng đầu/cuối thành công.
[Constraints]: Toàn bộ 23 ca kiểm thử của hệ thống phải chạy qua (PASS 100%); không làm hỏng tính năng đăng nhập/đăng ký hiện có của đồ án.
[Output]: Đoạn code cập nhật trong `auth_schema.py`, `main.py`, `app.js` và file kiểm thử hoàn chỉnh `tests/test_auth.py`.
```

