"""Bộ kiểm thử tính năng Dịch vụ đặt kèm khi đặt sân và vá lỗ hổng trọng tài.

Bao gồm:
1. Đặt sân có chọn dịch vụ kèm (nước suối, Pocari, áo bib...) + trọng tài -> Tính đúng hóa đơn & chi tiết
2. Đặt sân không chọn dịch vụ kèm -> Không sinh SuDungDichVu ngoại trừ trọng tài (nếu có)
3. Xác thực dữ liệu đầu vào dịch vụ đặt kèm:
   - Dịch vụ không tồn tại / đã inactive -> Bị từ chối (400)
   - Chọn dịch vụ trọng tài trong danh sách đặt kèm -> Bị từ chối (400)
   - Số lượng <= 0 hoặc > 20 -> Bị từ chối (400)
   - Các món trùng lặp: gộp lại nếu tổng <= 20 thành công, vượt quá 20 bị từ chối (400)
4. Check-in và Check-out:
   - Dịch vụ kèm được ghi nhận chính xác vào hóa đơn check-in
   - Check-out quyết toán đúng số tiền (tiền sân + trọng tài + dịch vụ kèm - cọc)
5. Nhân viên gỡ bớt dịch vụ:
   - Sau khi gỡ, hóa đơn tự động cập nhật lại tổng tiền chính xác
6. Vá lỗ hổng tab vận hành:
   - Nhân viên cố tình thêm dịch vụ TRONG_TAI qua API add_service lúc đang đá -> Bị từ chối (400)
"""

from datetime import date, time, timedelta
from app.models import LoaiSan, San, BangGia, DanhMucDichVu, DatSan
from app.services.dat_san_service import get_vn_now


def _setup_court_and_services(session):
    """Tạo sân và danh mục dịch vụ mẫu."""
    loai_7 = LoaiSan(ten_loai="Sân 7", so_nguoi_tieu_chuan=7, mo_ta="Sân 7 tiêu chuẩn")
    session.add(loai_7)
    session.flush()

    san = San(ma="SAN7-TEST", ten_san="Sân 7 Test", loai_san_id=loai_7.loai_san_id, trang_thai="active")
    session.add(san)
    session.flush()

    bg = BangGia(
        san_id=san.ma,
        gio_bat_dau=time(6, 0),
        gio_ket_thuc=time(23, 0),
        don_gia=300000,
        loai_ngay="thuong"
    )
    session.add(bg)

    dv_lavie = DanhMucDichVu(ten_dich_vu="Nước khoáng Lavie 500ml", don_vi_tinh="Chai", don_gia=10000, danh_muc="NUOC_UONG", trang_thai="active")
    dv_pocari = DanhMucDichVu(ten_dich_vu="Nước điện giải Pocari 500ml", don_vi_tinh="Chai", don_gia=20000, danh_muc="NUOC_UONG", trang_thai="active")
    dv_bib = DanhMucDichVu(ten_dich_vu="Bộ áo bib 7 áo", don_vi_tinh="Bộ", don_gia=50000, danh_muc="TRANG_BI", trang_thai="active")
    dv_inactive = DanhMucDichVu(ten_dich_vu="Nước ngọt cũ", don_vi_tinh="Lon", don_gia=15000, danh_muc="NUOC_UONG", trang_thai="inactive")
    dv_ref = DanhMucDichVu(ten_dich_vu="Thuê trọng tài điều khiển trận", don_vi_tinh="Trận", don_gia=200000, danh_muc="TRONG_TAI", trang_thai="active")

    session.add_all([dv_lavie, dv_pocari, dv_bib, dv_inactive, dv_ref])
    session.commit()

    return san, {
        "lavie": dv_lavie,
        "pocari": dv_pocari,
        "bib": dv_bib,
        "inactive": dv_inactive,
        "ref": dv_ref
    }


def test_booking_with_addon_services_and_referee_success(client_and_db, authenticated_client):
    """Đặt sân kèm trọng tài và dịch vụ phát sinh (Lavie 5 chai + Pocari 2 chai)."""
    client, session = client_and_db
    _, headers = authenticated_client
    san, services = _setup_court_and_services(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    # 18:00 - 19:30 là 1.5h cao điểm (1.5 * 350k = 525.000đ)
    # Trọng tài: 200.000đ -> tiền sân = 725.000đ
    # Dịch vụ kèm: 5 Lavie (50k) + 2 Pocari (40k) = 90.000đ
    # Cọc: 100.000đ -> còn lại phải trả: 725k + 90k - 100k = 715.000đ
    res = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True,
        "dich_vu_kem": [
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 5},
            {"dich_vu_id": services["pocari"].dich_vu_id, "so_luong": 2}
        ]
    })
    assert res.status_code == 200, res.text
    booking_data = res.json()
    ma_don = booking_data["ma_don"]

    # Kiểm tra chi tiết đơn đặt sân qua API detail
    res_detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()

    assert len(detail["dich_vus"]) == 3  # 1 referee + 2 addon services
    assert detail["tien_san"] == 725000
    assert detail["tong_dich_vu"] == 90000
    assert detail["tien_coc"] == 100000
    assert detail["tong_thanh_toan"] == 715000


def test_booking_without_addon_services(client_and_db, authenticated_client):
    """Đặt sân không chọn dịch vụ kèm thì danh sách dịch vụ trống, tong_dich_vu = 0."""
    client, session = client_and_db
    _, headers = authenticated_client
    san, services = _setup_court_and_services(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    res = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": False,
        "dich_vu_kem": []
    })
    assert res.status_code == 200
    ma_don = res.json()["ma_don"]

    res_detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert len(detail["dich_vus"]) == 0
    assert detail["tong_dich_vu"] == 0
    assert detail["tien_san"] == 525000
    assert detail["tong_thanh_toan"] == 425000


def test_addon_service_validations(client_and_db, authenticated_client):
    """Xác thực các trường hợp vi phạm quy tắc dịch vụ kèm."""
    client, session = client_and_db
    _, headers = authenticated_client
    san, services = _setup_court_and_services(session)
    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()

    # 1. Dịch vụ không tồn tại
    res_not_found = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [{"dich_vu_id": 99999, "so_luong": 1}]
    })
    assert res_not_found.status_code == 400
    assert "không tồn tại" in res_not_found.json()["detail"]

    # 2. Dịch vụ inactive (ngưng kinh doanh)
    res_inactive = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [{"dich_vu_id": services["inactive"].dich_vu_id, "so_luong": 1}]
    })
    assert res_inactive.status_code == 400
    assert "tạm dừng hoạt động" in res_inactive.json()["detail"] or "không tồn tại" in res_inactive.json()["detail"]

    # 3. Chọn dịch vụ trọng tài trong danh sách dịch vụ kèm (phải dùng tùy chọn thue_trong_tai)
    res_ref = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [{"dich_vu_id": services["ref"].dich_vu_id, "so_luong": 1}]
    })
    assert res_ref.status_code == 400
    assert "Thuê trọng tài" in res_ref.json()["detail"]

    # 4. Số lượng <= 0
    res_zero = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [{"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 0}]
    })
    assert res_zero.status_code == 400
    assert "từ 1 đến 20" in res_zero.json()["detail"]

    # 5. Số lượng > 20
    res_over = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [{"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 21}]
    })
    assert res_over.status_code == 400
    assert "từ 1 đến 20" in res_over.json()["detail"]

    # 6. Món trùng gộp lại vượt quá 20 (ví dụ 12 + 10 = 22) -> Bị từ chối
    res_dup_over = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 12},
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 10}
        ]
    })
    assert res_dup_over.status_code == 400
    assert "tối đa là 20" in res_dup_over.json()["detail"]

    # 7. Món trùng gộp lại <= 20 (ví dụ 5 + 3 = 8) -> Thành công và gộp thành 1 dòng 8 chai
    res_dup_ok = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": san.ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "dich_vu_kem": [
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 5},
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 3}
        ]
    })
    assert res_dup_ok.status_code == 200
    ma_don_dup = res_dup_ok.json()["ma_don"]
    detail_dup = client.get(f"/api/dat-san/booking/{ma_don_dup}/detail", headers=headers).json()
    assert len(detail_dup["dich_vus"]) == 1
    assert detail_dup["dich_vus"][0]["so_luong"] == 8
    assert detail_dup["dich_vus"][0]["thanh_tien"] == 80000


def test_checkin_checkout_flow_with_addon_services(client_and_db, authenticated_client, staff_client):
    """Khách đặt sân kèm dịch vụ -> Nhân viên Check-in -> Check-out giữ đúng tổng tiền."""
    client, session = client_and_db
    _, cust_headers = authenticated_client
    _, staff_headers = staff_client
    san, services = _setup_court_and_services(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    # 1. Đặt sân có kèm 3 chai Pocari (60.000đ)
    res_b = client.post("/api/dat-san/booking", headers=cust_headers, json={
        "ma_san": san.ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": False,
        "dich_vu_kem": [
            {"dich_vu_id": services["pocari"].dich_vu_id, "so_luong": 3}
        ]
    })
    assert res_b.status_code == 200
    ma_don = res_b.json()["ma_don"]

    # 2. Duyệt cọc 100.000đ
    res_conf = client.post("/api/dat-san/booking/confirm-deposit", headers=staff_headers, json={
        "ma_don": ma_don,
        "so_tien": 100000,
        "phuong_thuc": "chuyen_khoan"
    })
    assert res_conf.status_code == 200

    # 3. Check-in: Hóa đơn phải tính đúng 60.000đ dịch vụ đặt trước
    res_ci = client.post("/api/van-hanh/check-in", headers=staff_headers, json={
        "ma_don": ma_don
    })
    assert res_ci.status_code == 200
    inv = res_ci.json()
    assert inv["tien_san"] == 525000
    assert inv["tong_dich_vu"] == 60000
    assert inv["tien_coc_da_tru"] == 100000
    assert inv["tong_thanh_toan"] == 485000  # 525k + 60k - 100k

    # 4. Check-out quyết toán
    res_co = client.post("/api/van-hanh/check-out?phuong_thuc=tien_mat", headers=staff_headers, json={
        "ma_don": ma_don
    })
    assert res_co.status_code == 200
    final_inv = res_co.json()
    assert final_inv["tong_dich_vu"] == 60000
    assert final_inv["tong_thanh_toan"] == 485000


def test_staff_remove_addon_service_recalculates(client_and_db, authenticated_client, staff_client):
    """Nhân viên có thể xóa món dịch vụ kèm, hóa đơn tự động tính lại."""
    client, session = client_and_db
    _, cust_headers = authenticated_client
    _, staff_headers = staff_client
    san, services = _setup_court_and_services(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    # Đặt 2 chai Lavie (20k) và 1 bộ Áo bib (50k) = 70.000đ dịch vụ
    res_b = client.post("/api/dat-san/booking", headers=cust_headers, json={
        "ma_san": san.ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "dich_vu_kem": [
            {"dich_vu_id": services["lavie"].dich_vu_id, "so_luong": 2},
            {"dich_vu_id": services["bib"].dich_vu_id, "so_luong": 1}
        ]
    })
    ma_don = res_b.json()["ma_don"]

    # Duyệt cọc & Check-in
    client.post("/api/dat-san/booking/confirm-deposit", headers=staff_headers, json={
        "ma_don": ma_don, "so_tien": 100000
    })
    res_ci = client.post("/api/van-hanh/check-in", headers=staff_headers, json={"ma_don": ma_don})
    assert res_ci.json()["tong_dich_vu"] == 70000

    # Lấy ID của món Áo bib
    detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=cust_headers).json()
    bib_usage = next(d for d in detail["dich_vus"] if d["dich_vu_id"] == services["bib"].dich_vu_id)

    # Nhân viên gỡ món Áo bib (50k)
    res_del = client.delete(f"/api/van-hanh/service-usage/{ma_don}/{bib_usage['su_dung_id']}", headers=staff_headers)
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # Chi tiết và hóa đơn được tính lại: tổng dịch vụ còn lại 20k (Lavie), tổng thanh toán giảm 50k
    detail_after = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=cust_headers).json()
    assert len(detail_after["dich_vus"]) == 1
    assert detail_after["tong_dich_vu"] == 20000
    assert detail_after["tong_thanh_toan"] == 445000  # 525k + 20k - 100k


def test_operations_tab_add_referee_hole_blocked(client_and_db, staff_client):
    """Vá lỗ hổng: Nhân viên không thể thêm dịch vụ TRONG_TAI khi đang đá qua tab vận hành."""
    client, session = client_and_db
    _, staff_headers = staff_client
    san, services = _setup_court_and_services(session)

    today = date.today() + timedelta(days=1)
    don = DatSan(
        ma_don="DS-HOLE-001",
        ma_khach_hang=1,
        ma_san=san.ma,
        ngay_da=today,
        gio_bat_dau=time(18, 0),
        gio_ket_thuc=time(19, 30),
        tien_coc=100000,
        trang_thai="da_xac_nhan"
    )
    session.add(don)
    session.commit()

    # Check-in chuyển sang dang_da
    client.post("/api/van-hanh/check-in", headers=staff_headers, json={"ma_don": don.ma_don})

    # Cố tình gọi API add-service với món TRONG_TAI -> Phải bị từ chối 400!
    res_hack = client.post("/api/van-hanh/add-service", headers=staff_headers, json={
        "ma_don": don.ma_don,
        "dich_vu_id": services["ref"].dich_vu_id,
        "so_luong": 1
    })
    assert res_hack.status_code == 400
    assert "Không thể thêm dịch vụ trọng tài trong ca thi đấu" in res_hack.json()["detail"]
