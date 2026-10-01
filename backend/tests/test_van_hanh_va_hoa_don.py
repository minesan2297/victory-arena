"""Bộ kiểm thử nghiệp vụ Vận hành sân, Dịch vụ, Hóa đơn và Hủy giữ chỗ quá hạn 10 phút.

Phủ các nghiệp vụ trọng tâm:
1. Luồng Check-in khi khách đến sân và Check-out thanh toán hóa đơn
2. Tính tiền hóa đơn tự động khi sử dụng thêm dịch vụ (nước, áo bib, bóng)
3. Tự động quét và hủy các đơn giữ chỗ quá 10 phút chưa đặt cọc
4. Báo cáo thống kê tổng quan doanh thu và tỷ lệ sử dụng sân
"""

from datetime import date, time, datetime, timedelta, timezone
from app.models import LoaiSan, San, BangGia, DatSan, LichDat, DanhMucDichVu, SuDungDichVu, ThanhToan
from app.tasks.lock_expiry import check_and_expire_bookings


def _setup_san_va_bang_gia(session):
    """Hàm phụ trợ tạo sân và bảng giá mẫu."""
    loai_7 = LoaiSan(ten_loai="Sân 7", so_nguoi_tieu_chuan=7, mo_ta="Sân 7 chuẩn")
    session.add(loai_7)
    session.flush()

    san = San(
        ma="SAN7-TEST",
        ten_san="Sân 7 Test",
        loai_san_id=loai_7.loai_san_id,
        trang_thai="active"
    )
    session.add(san)
    session.flush()

    # Bảng giá: 300.000đ/h
    bg = BangGia(
        san_id=san.ma,
        gio_bat_dau=time(6, 0),
        gio_ket_thuc=time(23, 0),
        don_gia=300000,
        loai_ngay="thuong"
    )
    session.add(bg)
    session.commit()
    return san


def test_checkin_va_checkout_thanh_toan_flow(client_and_db, staff_client):
    """Kiểm thử luồng vận hành sân: Khách đặt cọc -> Nhân viên Check-in -> Check-out trả sân."""
    client, session = client_and_db
    _, staff_headers = staff_client
    san = _setup_san_va_bang_gia(session)

    today = date.today() + timedelta(days=1)
    
    # 1. Tạo đơn đặt sân đã cọc 200.000đ
    don = DatSan(
        ma_don="DS-OPER-001",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=today,
        gio_bat_dau=time(17, 0),
        gio_ket_thuc=time(18, 30),
        tien_coc=200000,
        trang_thai="da_xac_nhan"
    )
    session.add(don)
    session.commit()

    # 2. Nhân viên thực hiện Check-in khi khách tới sân
    res_in = client.post("/api/van-hanh/check-in", json={
        "ma_don": don.ma_don,
        "ghi_chu": "Khách đã đến đúng giờ, nhận sân"
    }, headers=staff_headers)
    assert res_in.status_code == 200
    hoa_don_data = res_in.json()
    assert hoa_don_data["ma_don"] == don.ma_don

    # Kiểm tra trạng thái đơn đổi thành 'dang_da'
    session.refresh(don)
    assert don.trang_thai == "dang_da"

    # 3. Nhân viên thực hiện Check-out khi hết giờ
    res_out = client.post(f"/api/van-hanh/check-out?phuong_thuc=tien_mat", json={
        "ma_don": don.ma_don
    }, headers=staff_headers)
    assert res_out.status_code == 200
    data_out = res_out.json()
    assert data_out["tong_thanh_toan"] >= 0

    # Kiểm tra trạng thái đơn đổi thành 'hoan_tat'
    session.refresh(don)
    assert don.trang_thai == "hoan_tat"


def test_tinh_tien_hoa_don_kem_dich_vu(client_and_db, staff_client):
    """Kiểm thử tính tiền hóa đơn: Tiền sân + Dịch vụ phát sinh - Tiền cọc đã trừ."""
    client, session = client_and_db
    _, staff_headers = staff_client
    san = _setup_san_va_bang_gia(session)

    # 1. Tạo danh mục dịch vụ (Nước khoáng: 10.000đ, Thuê bóng: 50.000đ)
    dv1 = DanhMucDichVu(ten_dich_vu="Nước khoáng Lavie", don_vi_tinh="Chai", don_gia=10000, danh_muc="NUOC_UONG")
    dv2 = DanhMucDichVu(ten_dich_vu="Thuê bóng số 5", don_vi_tinh="Quả", don_gia=50000, danh_muc="TRANG_BI")
    session.add_all([dv1, dv2])
    session.commit()

    # 2. Tạo đơn đặt 1 tiếng (18:00 - 19:00 = 300.000đ tiền sân, cọc 100.000đ)
    today = date.today() + timedelta(days=1)
    don = DatSan(
        ma_don="DS-OPER-002",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=today,
        gio_bat_dau=time(18, 0),
        gio_ket_thuc=time(19, 0),
        tien_coc=100000,
        trang_thai="da_xac_nhan"
    )
    pay_coc = ThanhToan(
        ma_don=don.ma_don,
        so_tien=100000,
        phuong_thuc="chuyen_khoan",
        loai_giao_dich="dat_coc",
        trang_thai="thanh_cong"
    )
    session.add_all([don, pay_coc])
    session.commit()

    # Check-in tạo hóa đơn
    client.post("/api/van-hanh/check-in", json={"ma_don": don.ma_don}, headers=staff_headers)

    # 3. Khách gọi 5 chai nước (50.000đ) và 1 quả bóng (50.000đ) -> Tổng dịch vụ = 100.000đ
    res_dv1 = client.post("/api/van-hanh/add-service", json={
        "ma_don": don.ma_don,
        "dich_vu_id": dv1.dich_vu_id,
        "so_luong": 5
    }, headers=staff_headers)
    assert res_dv1.status_code == 200

    res_dv2 = client.post("/api/van-hanh/add-service", json={
        "ma_don": don.ma_don,
        "dich_vu_id": dv2.dich_vu_id,
        "so_luong": 1
    }, headers=staff_headers)
    assert res_dv2.status_code == 200

    # 4. Check-out và xác minh hóa đơn
    # Tiền sân (18:00 - 19:00 là giờ cao điểm) = 350.000đ
    # Dịch vụ phát sinh = 100.000đ (5 nước 50k + 1 bóng 50k)
    # Tiền cọc đã trả = 100.000đ
    # Còn phải trả = 350.000 + 100.000 - 100.000 = 350.000đ
    res_out = client.post(f"/api/van-hanh/check-out?phuong_thuc=chuyen_khoan", json={
        "ma_don": don.ma_don
    }, headers=staff_headers)
    assert res_out.status_code == 200
    bill = res_out.json()

    assert bill["tien_san"] == 350000
    assert bill["tong_dich_vu"] == 100000
    assert bill["tien_coc_da_tru"] == 100000
    assert bill["tong_thanh_toan"] == 350000


def test_tu_dong_huy_giu_cho_qua_10_phut(client_and_db):
    """Kiểm thử Background Task: Quét và hủy tự động các đơn giữ chỗ đã hết hạn 10 phút."""
    _, session = client_and_db
    san = _setup_san_va_bang_gia(session)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    past_15_mins = now - timedelta(minutes=15)
    future_5_mins = now + timedelta(minutes=5)

    # Đơn 1: Đã hết hạn (lock_expires_at cách đây 15 phút) -> PHẢI BỊ HỦY
    don_expired = DatSan(
        ma_don="DS-EXP-001",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=date.today(),
        gio_bat_dau=time(19, 0),
        gio_ket_thuc=time(20, 30),
        tien_coc=0,
        trang_thai="cho_coc",
        lock_expires_at=past_15_mins
    )
    # Lịch giữ chỗ tương ứng
    lich1 = LichDat(
        san_id=san.ma,
        ma_don=don_expired.ma_don,
        bat_dau=datetime.combine(date.today(), time(19, 0)),
        ket_thuc=datetime.combine(date.today(), time(20, 30)),
        loai_lich="thue"
    )

    # Đơn 2: Còn hạn giữ chỗ (lock_expires_at 5 phút nữa) -> PHẢI GIỮ NGUYÊN
    don_valid = DatSan(
        ma_don="DS-EXP-002",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=date.today(),
        gio_bat_dau=time(20, 30),
        gio_ket_thuc=time(22, 0),
        tien_coc=0,
        trang_thai="cho_coc",
        lock_expires_at=future_5_mins
    )
    lich2 = LichDat(
        san_id=san.ma,
        ma_don=don_valid.ma_don,
        bat_dau=datetime.combine(date.today(), time(20, 30)),
        ket_thuc=datetime.combine(date.today(), time(22, 0)),
        loai_lich="thue"
    )

    session.add_all([don_expired, lich1, don_valid, lich2])
    session.commit()

    # Kích hoạt hàm quét task nền
    expired_count = check_and_expire_bookings(session)
    assert expired_count == 1

    # Kiểm tra đơn 1 đã chuyển thành 'da_huy', lock_expires_at chuyển None, lịch sân được giải phóng
    session.refresh(don_expired)
    assert don_expired.trang_thai == "da_huy"
    assert don_expired.lock_expires_at is None
    lich_check = session.query(LichDat).filter(LichDat.ma_don == "DS-EXP-001").first()
    assert lich_check is None

    # Kiểm tra đơn 2 vẫn an toàn ở trạng thái 'cho_coc'
    session.refresh(don_valid)
    assert don_valid.trang_thai == "cho_coc"
    assert don_valid.lock_expires_at == future_5_mins


def test_bao_cao_dashboard_thong_ke(client_and_db, admin_client):
    """Kiểm thử API Báo cáo Dashboard: Thống kê số sân, tổng đơn đặt và tổng doanh thu."""
    client, session = client_and_db
    _, admin_headers = admin_client
    san = _setup_san_va_bang_gia(session)

    # Tạo giao dịch thanh toán thành công 500.000đ
    don = DatSan(
        ma_don="DS-RPT-001",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=date.today(),
        gio_bat_dau=time(16, 0),
        gio_ket_thuc=time(17, 30),
        tien_coc=200000,
        trang_thai="hoan_tat"
    )
    pay = ThanhToan(
        ma_don="DS-RPT-001",
        so_tien=500000,
        phuong_thuc="chuyen_khoan",
        loai_giao_dich="thanh_toan_het",
        trang_thai="thanh_cong"
    )
    session.add_all([don, pay])
    session.commit()

    res = client.get("/api/bao-cao/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["tong_san"] >= 1
    assert data["san_hoat_dong"] >= 1
    assert data["tong_doanh_thu"] >= 500000
