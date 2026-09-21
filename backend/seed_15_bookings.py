import sys
sys.stdout.reconfigure(encoding='utf-8')
from datetime import date, time, datetime, timezone
import random

from app.database import SessionLocal
from app.models.tai_khoan import TaiKhoan, VaiTro
from app.models.san import San
from app.models.dat_san import DatSan, LichDat
from app.models.hoa_don import ThanhToan
from app.auth.security import hash_password

db = SessionLocal()

# Lấy vai trò CUSTOMER
role_customer = db.query(VaiTro).filter(VaiTro.ten_vai_tro == 'CUSTOMER').first()
if not role_customer:
    role_customer = db.query(VaiTro).filter(VaiTro.vai_tro_id == 3).first()

customers_data = [
    ('nhatnamfc', 'Phạm Nhật Nam (FC Bách Khoa)', '0987110001', 'nhatnam@gmail.com', 'SAN7-001', time(9, 0), time(10, 30), 'chuyen_khoan', 'Mượn 14 áo bib xanh, 2 quả bóng số 5'),
    ('hoanglongfc', 'Lê Hoàng Long (FC Xây Dựng)', '0987110002', 'hoanglong@gmail.com', 'SAN7-001', time(14, 0), time(15, 30), 'momo', 'Trận đấu giao hữu khoa Cầu Đường'),
    ('quanghuyfc', 'Vũ Quang Huy (FC Kinh Tế Quốc Dân)', '0987110003', 'quanghuy@gmail.com', 'SAN7-001', time(15, 30), time(17, 0), 'vnpay', 'Yêu cầu chuẩn bị nước đá trước trận'),
    ('haidangfc', 'Hoàng Hải Đăng (FC Ngoại Thương)', '0987110004', 'haidang@gmail.com', 'SAN7-001', time(17, 0), time(18, 30), 'chuyen_khoan', 'Trận derby sinh viên FTU vs NEU'),
    ('quocbaofc', 'Trần Quốc Bảo (FC Y Hà Nội)', '0987110005', 'quocbao@gmail.com', 'SAN7-001', time(18, 30), time(20, 0), 'momo', 'Thuê 1 bộ găng tay thủ môn'),
    ('tiendungfc', 'Đặng Tiến Dũng (FC Giao Thông)', '0987110006', 'tiendung@gmail.com', 'SAN7-001', time(20, 0), time(21, 30), 'chuyen_khoan', 'Đá ca tối, mượn còi trọng tài'),
    ('anhtuanfc', 'Bùi Anh Tuấn (FC Bưu Chính)', '0987110007', 'anhtuan@gmail.com', 'SAN7-001', time(21, 30), time(23, 0), 'tien_mat', 'Ca muộn, bật đủ đèn sân'),
    ('minhkhangfc', 'Nguyễn Minh Khang (FC Sư Phạm)', '0987110008', 'minhkhang@gmail.com', 'SAN7-002', time(15, 30), time(17, 0), 'vnpay', 'Giao hữu tân sinh viên K24'),
    ('vanducfc', 'Phan Văn Đức (FC Kiến Trúc)', '0987110009', 'vanduc@gmail.com', 'SAN7-002', time(17, 0), time(18, 30), 'chuyen_khoan', 'Cần 20 chai nước lọc Revive'),
    ('giahuyfc', 'Đỗ Gia Huy (FC Công Nghiệp)', '0987110010', 'giahuy@gmail.com', 'SAN7-002', time(18, 30), time(20, 0), 'momo', 'Trận bán kết cúp HaUI Football'),
    ('congthanhfc', 'Hồ Công Thành (FC Thăng Long)', '0987110011', 'congthanh@gmail.com', 'SAN7-002', time(20, 0), time(21, 30), 'chuyen_khoan', 'Mượn 14 bib cam phân chia đội'),
    ('theanhfc', 'Dương Thế Anh (FC Đống Đa)', '0987110012', 'theanh@gmail.com', 'SAN7-003', time(17, 0), time(18, 30), 'vnpay', 'Đá giải phong trào quận Đống Đa'),
    ('tronghoangfc', 'Lương Trọng Hoàng (FC Cầu Giấy)', '0987110013', 'tronghoang@gmail.com', 'SAN7-003', time(18, 30), time(20, 0), 'chuyen_khoan', 'Chuẩn bị sân bóng chuẩn thi đấu'),
    ('dinhtrongfc', 'Trịnh Đình Trọng (FC Tây Hồ)', '0987110014', 'dinhtrong@gmail.com', 'SAN11-001', time(17, 0), time(18, 30), 'momo', 'Đá sân 11 người đại chiến Tây Hồ'),
    ('vanhieufc', 'Tô Văn Hiếu (FC Hoàng Mai)', '0987110015', 'vanhieu@gmail.com', 'SAN11-001', time(18, 30), time(20, 0), 'chuyen_khoan', 'Sân 11 người giao hữu cuối tuần')
]

target_date = date(2026, 9, 23)
created_bookings = []
pwd_hash = hash_password('password123')

for idx, (uname, fullname, phone, email, court_code, start_t, end_t, pay_method, note) in enumerate(customers_data, 1):
    user = db.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == uname).first()
    if not user:
        user = TaiKhoan(
            ten_dang_nhap=uname,
            mat_khau_hash=pwd_hash,
            ho_ten=fullname,
            so_dien_thoai=phone,
            email=email,
            vai_tro_id=role_customer.vai_tro_id,
            diem_uy_tin=random.randint(95, 100),
            trang_thai='active'
        )
        db.add(user)
        db.flush()
    
    dt_start = datetime.combine(target_date, start_t)
    dt_end = datetime.combine(target_date, end_t)
    
    # Dọn dẹp xung đột cũ trên slot này nếu có
    existing_lich = db.query(LichDat).filter(
        LichDat.san_id == court_code,
        LichDat.bat_dau < dt_end,
        LichDat.ket_thuc > dt_start
    ).all()
    for el in existing_lich:
        if el.dat_san:
            db.delete(el.dat_san)
        db.delete(el)
    db.flush()
    
    ma_don = f'DS20260923-{5000 + idx}'
    
    # Kiểm tra xem mã đơn đã có chưa, nếu có thì xóa
    old_booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
    if old_booking:
        db.delete(old_booking)
        db.flush()

    booking = DatSan(
        ma_don=ma_don,
        ma_khach_hang=user.tai_khoan_id,
        ma_san=court_code,
        ngay_da=target_date,
        gio_bat_dau=start_t,
        gio_ket_thuc=end_t,
        tien_coc=100000,
        trang_thai='da_xac_nhan',
        ghi_chu=note,
        ngay_tao=datetime.now(timezone.utc)
    )
    db.add(booking)
    db.flush()
    
    lich = LichDat(
        san_id=court_code,
        ma_don=ma_don,
        bat_dau=dt_start,
        ket_thuc=dt_end,
        loai_lich='thue',
        ghi_chu=f'Khách hàng: {fullname}'
    )
    db.add(lich)
    
    tt = ThanhToan(
        ma_don=ma_don,
        so_tien=100000,
        phuong_thuc=pay_method,
        loai_giao_dich='dat_coc',
        trang_thai='thanh_cong',
        ma_giao_dich_cong=f'PAY-20260923-{idx:04d}',
        thoi_gian=datetime.now(timezone.utc)
    )
    db.add(tt)
    
    start_str = start_t.strftime('%H:%M')
    end_str = end_t.strftime('%H:%M')
    created_bookings.append((ma_don, fullname, court_code, f'{start_str} - {end_str}', pay_method))

db.commit()
print(f'=== ĐÃ TẠO THÀNH CÔNG {len(created_bookings)} ĐƠN ĐẶT SÂN CHO 15 NGƯỜI KHÁC NHAU ===')
for b in created_bookings:
    print(f'- Mã: {b[0]} | Khách: {b[1]} | Sân: {b[2]} | Khung: {b[3]} | Cọc: 100.000đ ({b[4]})')
db.close()
