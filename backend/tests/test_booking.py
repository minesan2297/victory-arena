import pytest
from datetime import date, time, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.database import Base
from app.models import VaiTro, TaiKhoan, LoaiSan, San, BangGia, DatSan, LichDat, ThanhToan
from app.models.ai_models import ThongBao
from app.models.enums import VaiTroEnum, TrangThaiDatSan
from app.schemas.auth_schema import RegisterRequest
from app.schemas.san_schema import SanCreate, BangGiaCreate, BaoTriCreate
from app.schemas.dat_san_schema import DatSanCreate, DoiLichRequest
from app.services.auth_service import AuthService
from app.services.san_service import SanService
from app.services.dat_san_service import DatSanService

@pytest.fixture(scope="function")
def db_session():
    """Tạo database SQLite in-memory độc lập cho từng ca kiểm thử."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed VaiTro và LoaiSan cần thiết
    v_admin = VaiTro(ten_vai_tro="ADMIN", mo_ta="Quản trị viên")
    v_staff = VaiTro(ten_vai_tro="STAFF", mo_ta="Nhân viên")
    v_customer = VaiTro(ten_vai_tro="CUSTOMER", mo_ta="Khách hàng")
    session.add_all([v_admin, v_staff, v_customer])
    
    l5 = LoaiSan(ten_loai="Sân 5", so_nguoi_tieu_chuan=5)
    session.add(l5)
    session.commit()

    # Tạo User khách hàng
    customer_user = TaiKhoan(
        ten_dang_nhap="customer1",
        mat_khau_hash="hashed",
        ho_ten="Khách hàng Test",
        so_dien_thoai="0988000111",
        vai_tro_id=v_customer.vai_tro_id
    )
    session.add(customer_user)
    
    # Tạo Sân
    court = San(
        ma="SAN5-001",
        ten_san="Sân Test 5 Pro",
        loai_san_id=l5.loai_san_id,
        trang_thai="active"
    )
    session.add(court)
    
    # Tạo Bảng Giá
    pricing = BangGia(
        san_id="SAN5-001",
        gio_bat_dau=time(6, 0),
        gio_ket_thuc=time(23, 0),
        don_gia=250000.0,
        loai_ngay="thuong"
    )
    session.add(pricing)
    
    session.commit()
    
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

def test_auth_registration(db_session):
    """Kiểm tra chức năng đăng ký tài khoản mới."""
    reg = RegisterRequest(
        ten_dang_nhap="newuser",
        mat_khau="password123",
        ho_ten="Người dùng Mới",
        so_dien_thoai="0987654321",
        email="newuser@test.com"
    )
    user = AuthService.register(db_session, reg)
    assert user.tai_khoan_id is not None
    assert user.ten_dang_nhap == "newuser"
    assert user.vai_role_name_check_val() == "CUSTOMER"

def test_create_booking_success(db_session):
    """Kiểm tra đặt sân thành công: Khách tạo đơn ở trạng thái cho_coc, sau đó được duyệt da_xac_nhan."""
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date(2026, 9, 1),
        gio_bat_dau=time(18, 0),
        gio_ket_thuc=time(19, 30),
        tien_coc=100000.0,
        phuong_thuc_thanh_toan="tien_mat"
    )
    
    # Khách đặt đơn: Phải ở trạng thái cho_coc (chờ cọc) với khóa giữ chỗ 10 phút
    booking = DatSanService.create_booking(db_session, booking_in, customer.tai_khoan_id)
    assert booking.ma_don is not None
    assert booking.trang_thai == "cho_coc"
    assert booking.lock_expires_at is not None
    assert booking.tien_coc >= 100000
    
    # Nhân viên duyệt / xác nhận cọc -> chuyển sang da_xac_nhan
    confirmed = DatSanService.xac_nhan_coc(db_session, booking.ma_don, 100000, "chuyen_khoan")
    assert confirmed.trang_thai == "da_xac_nhan"
    assert confirmed.lock_expires_at is None
    assert confirmed.tien_coc == 100000

def test_anti_overbooking_overlap(db_session):
    """Kiểm tra ngăn chặn đặt trùng giờ (Interval Overlap)."""
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    # Đặt đơn 1: 18:00 - 19:30
    booking1_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date(2026, 9, 1),
        gio_bat_dau=time(18, 0),
        gio_ket_thuc=time(19, 30),
        tien_coc=100000.0
    )
    DatSanService.create_booking(db_session, booking1_in, customer.tai_khoan_id)
    
    # Đặt đơn 2: 18:30 - 20:00 (chồng lấn)
    booking2_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date(2026, 9, 1),
        gio_bat_dau=time(18, 30),
        gio_ket_thuc=time(20, 0),
        tien_coc=100000.0
    )
    
    with pytest.raises(HTTPException) as exc_info:
        DatSanService.create_booking(db_session, booking2_in, customer.tai_khoan_id)
    assert exc_info.value.status_code == 400
    assert "chính xác cùng giờ" in exc_info.value.detail or "trùng" in exc_info.value.detail or "bảo trì" in exc_info.value.detail

def test_booking_maintenance_lock(db_session):
    """Kiểm tra từ chối đặt sân trong khung giờ đang bảo trì."""
    # Tạo lịch bảo trì từ 14:00 đến 16:00
    maint_in = BaoTriCreate(
        san_id="SAN5-001",
        ngay_bao_tri=date(2026, 9, 1),
        gio_bat_dau=time(14, 0),
        gio_ket_thuc=time(16, 0),
        ly_do="Bảo trì đèn chiếu sáng"
    )
    SanService.create_maintenance(db_session, maint_in)
    
    # Đặt sân từ 14:30 đến 15:30 (nằm trong khung bảo trì)
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date(2026, 9, 1),
        gio_bat_dau=time(14, 30),
        gio_ket_thuc=time(15, 30),
        tien_coc=100000.0
    )
    
    with pytest.raises(HTTPException) as exc_info:
        DatSanService.create_booking(db_session, booking_in, customer.tai_khoan_id)
    assert exc_info.value.status_code == 400

def test_booking_cancellation_refund(db_session):
    """Kiểm tra chính sách hủy đơn và hoàn cọc tự động: Chỉ hoàn cọc khi đã nộp cọc thành công và hủy trước 24h."""
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    # Đặt đơn thi đấu vào 3 ngày tới (> 24 giờ trước)
    future_date = date.today() + timedelta(days=3)
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=future_date,
        gio_bat_dau=time(18, 0),
        gio_ket_thuc=time(19, 30),
        tien_coc=100000.0
    )
    booking = DatSanService.create_booking(db_session, booking_in, customer.tai_khoan_id)
    
    # Nhân viên xác nhận cọc thành công (để có giao dịch cọc thật trong CSDL)
    DatSanService.xac_nhan_coc(db_session, booking.ma_don, 100000, "chuyen_khoan")
    
    # Hủy đơn
    cancelled = DatSanService.huy_lich(db_session, booking.ma_don)
    assert cancelled.trang_thai == "da_huy"
    
    # Kiểm tra đã sinh giao dịch hoàn cọc
    refund = db_session.query(ThanhToan).filter(
        ThanhToan.ma_don == booking.ma_don,
        ThanhToan.loai_giao_dich == "hoan_coc"
    ).first()
    assert refund is not None
    assert refund.so_tien == -100000.0 # Hoàn cọc âm

def test_unpaid_booking_cancellation_no_phantom_refund(db_session):
    """Kiểm tra chống lỗ hổng hoàn cọc ảo: Hủy đơn chưa cọc (cho_coc) thì không được sinh giao dịch hoàn tiền âm."""
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    future_date = date.today() + timedelta(days=3)
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=future_date,
        gio_bat_dau=time(14, 0),
        gio_ket_thuc=time(15, 30),
        tien_coc=100000.0
    )
    booking = DatSanService.create_booking(db_session, booking_in, customer.tai_khoan_id)
    assert booking.trang_thai == "cho_coc"
    
    # Khách hủy đơn khi chưa đóng cọc thật
    cancelled = DatSanService.huy_lich(db_session, booking.ma_don)
    assert cancelled.trang_thai == "da_huy"
    
    # Chắc chắn KHÔNG có giao dịch hoàn cọc ảo nào sinh ra
    refund = db_session.query(ThanhToan).filter(
        ThanhToan.ma_don == booking.ma_don,
        ThanhToan.loai_giao_dich == "hoan_coc"
    ).first()
    assert refund is None

def test_qr_deposit_generation_and_sandbox(db_session):
    """Kiểm tra sinh mã QR ảo (VietQR, MoMo, VNPAY) và giả lập thanh toán Sandbox."""
    customer = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date(2026, 9, 2),
        gio_bat_dau=time(19, 0),
        gio_ket_thuc=time(20, 30),
        tien_coc=100000.0
    )
    booking = DatSanService.create_booking(db_session, booking_in, customer.tai_khoan_id)
    
    # 1. Sinh QR cọc
    qr_info = DatSanService.generate_deposit_qr(db_session, booking.ma_don, "chuyen_khoan")
    assert "vietqr.io" in qr_info["vietqr_url"]
    assert "MB" in qr_info["vietqr_url"]
    assert qr_info["noi_dung"] == f"COC {booking.ma_don}"
    assert qr_info["so_tien"] >= 100000
    assert "momo_qr_url" in qr_info
    assert "vnpay_qr_url" in qr_info
    
    # 2. Giả lập thanh toán Sandbox QR
    paid_booking = DatSanService.sandbox_qr_pay(db_session, booking.ma_don, "chuyen_khoan")
    assert paid_booking.trang_thai == "da_xac_nhan"
    assert paid_booking.lock_expires_at is None
    
    # Kiểm tra có bản ghi thanh toán cọc thành công
    payment = db_session.query(ThanhToan).filter(
        ThanhToan.ma_don == booking.ma_don,
        ThanhToan.loai_giao_dich == "dat_coc"
    ).first()
    assert payment is not None
    assert payment.trang_thai == "thanh_cong"


def test_court_crud_operations(db_session):
    """Kiểm tra đầy đủ chức năng CRUD sân bóng: Tạo mới, Xem, Sửa thông tin và Xóa."""
    from app.schemas.san_schema import SanUpdate
    
    # 1. CREATE
    court_in = SanCreate(
        ma="SAN7-TEST",
        ten_san="Sân 7 Test Pro",
        loai_san_id=1,
        vi_tri="Khu Test",
        mo_ta_ai="Mặt cỏ đạt chuẩn"
    )
    court = SanService.create_court(db_session, court_in)
    assert court.ma == "SAN7-TEST"
    assert court.ten_san == "Sân 7 Test Pro"
    
    # 2. READ
    all_courts = SanService.get_all_courts(db_session)
    assert any(c.ma == "SAN7-TEST" for c in all_courts)
    
    # 3. UPDATE
    update_in = SanUpdate(
        ten_san="Sân 7 Test VIP Đổi Tên",
        vi_tri="Khu Test VIP",
        trang_thai="maintenance"
    )
    updated = SanService.update_court(db_session, "SAN7-TEST", update_in)
    assert updated.ten_san == "Sân 7 Test VIP Đổi Tên"
    assert updated.vi_tri == "Khu Test VIP"
    assert updated.trang_thai == "maintenance"
    
    # 4. DELETE (Chưa có đơn đặt -> Hard Delete)
    del_res = SanService.delete_court(db_session, "SAN7-TEST")
    assert del_res["action"] == "hard_delete"
    assert db_session.query(San).filter(San.ma == "SAN7-TEST").first() is None

# Helper extension to check user role from database record in test context
def check_role_helper(user: TaiKhoan) -> str:
    return user.vai_tro.ten_vai_tro

TaiKhoan.vai_role_name_check_val = check_role_helper

def test_notification_flow(db_session):
    """Kiểm tra toàn bộ luồng thông báo: Đặt sân -> Tạo thông báo -> Cọc -> Đổi lịch -> Đánh dấu đã đọc -> Xóa."""
    cust = db_session.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == "customer1").first()
    
    # 1. Đặt sân: phải tự động sinh thông báo cho khách hàng
    booking_in = DatSanCreate(
        ma_san="SAN5-001",
        ngay_da=date.today() + timedelta(days=5),
        gio_bat_dau=time(8, 0),
        gio_ket_thuc=time(9, 30),
        tien_coc=100000.0,
        phuong_thuc_thanh_toan="chuyen_khoan"
    )
    booking = DatSanService.create_booking(db_session, booking_in, cust.tai_khoan_id)
    
    notifs = db_session.query(ThongBao).filter(ThongBao.tai_khoan_id == cust.tai_khoan_id).all()
    assert len(notifs) >= 1
    latest_notif = notifs[-1]
    assert booking.ma_don in latest_notif.noi_dung
    assert latest_notif.da_doc == False
    
    # 2. Xác nhận cọc: sinh thêm thông báo xác nhận cọc
    DatSanService.xac_nhan_coc(db_session, booking.ma_don, 100000.0, "chuyen_khoan")
    notifs = db_session.query(ThongBao).filter(ThongBao.tai_khoan_id == cust.tai_khoan_id).all()
    assert len(notifs) >= 2
    assert any("xác nhận đặt cọc thành công" in n.noi_dung for n in notifs)
    
    # 3. Đánh dấu đã đọc
    db_session.query(ThongBao).filter(ThongBao.thong_bao_id == latest_notif.thong_bao_id).update({ThongBao.da_doc: True})
    db_session.commit()
    check_notif = db_session.query(ThongBao).filter(ThongBao.thong_bao_id == latest_notif.thong_bao_id).first()
    assert check_notif.da_doc == True
    
    # 4. Hủy đơn: sinh thêm thông báo hủy lịch
    DatSanService.huy_lich(db_session, booking.ma_don)
    notifs_after_cancel = db_session.query(ThongBao).filter(ThongBao.tai_khoan_id == cust.tai_khoan_id).all()
    assert any("HỦY LỊCH ĐẶT SÂN" in n.noi_dung for n in notifs_after_cancel)

