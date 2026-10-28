"""Bộ kiểm thử tính năng Thuê Trọng Tài và Vá Lỗ Hổng Hóa Đơn Check-in.

Bao gồm:
1. Đặt sân có chọn trọng tài -> Tự động sinh SuDungDichVu (200.000đ/trận)
2. Đặt sân không chọn trọng tài -> Không sinh dịch vụ
3. Kiểm tra hạn ngạch trọng tài (Quota): Tối đa 2 trận có trọng tài trong cùng ca, ca thứ 3 bị từ chối
4. Vá lỗ hổng Check-in: Hóa đơn tạm tính tính đúng dịch vụ đặt trước (trọng tài) thay vì reset về 0
5. Nhân viên có thể gỡ bỏ dịch vụ (trọng tài/nước) khỏi đơn đặt sân
6. Đổi lịch cho đơn có trọng tài sang khung giờ đã hết quota trọng tài -> Bị từ chối
"""

from datetime import date, time, timedelta
from app.models import LoaiSan, San, BangGia, DatSan, DanhMucDichVu, SuDungDichVu, HoaDon, ThanhToan
from app.services.dat_san_service import get_vn_now


def _setup_multi_sans(session):
    """Tạo loại sân, 3 sân 7 và bảng giá chuẩn 300.000đ/h."""
    loai_7 = LoaiSan(ten_loai="Sân 7", so_nguoi_tieu_chuan=7, mo_ta="Sân 7 tiêu chuẩn")
    session.add(loai_7)
    session.flush()

    sans = []
    for ma, ten in [("SAN7-A", "Sân 7A"), ("SAN7-B", "Sân 7B"), ("SAN7-C", "Sân 7C")]:
        s = San(ma=ma, ten_san=ten, loai_san_id=loai_7.loai_san_id, trang_thai="active")
        session.add(s)
        sans.append(s)
    session.flush()

    for s in sans:
        bg = BangGia(
            san_id=s.ma,
            gio_bat_dau=time(6, 0),
            gio_ket_thuc=time(23, 0),
            don_gia=300000,
            loai_ngay="thuong"
        )
        session.add(bg)
    session.commit()
    return sans


def test_booking_with_referee_creates_service(client_and_db, authenticated_client):
    """Khách đặt sân chọn thuê trọng tài -> Hệ thống tự động tạo SuDungDichVu 200.000đ."""
    client, session = client_and_db
    _, headers = authenticated_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    res = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[0].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    assert res.status_code == 200, res.text
    booking_data = res.json()
    ma_don = booking_data["ma_don"]

    # Kiểm tra chi tiết đơn qua API detail
    res_detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert len(detail["dich_vus"]) == 1
    referee_item = detail["dich_vus"][0]
    assert "trọng tài" in referee_item["ten_dich_vu"].lower()
    assert referee_item["don_gia"] == 200000
    assert referee_item["thanh_tien"] == 200000
    assert detail["tong_dich_vu"] == 200000


def test_booking_without_referee_no_service(client_and_db, authenticated_client):
    """Khách đặt sân không chọn trọng tài -> Không sinh bản ghi dịch vụ."""
    client, session = client_and_db
    _, headers = authenticated_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    res = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[0].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": False
    })
    assert res.status_code == 200
    ma_don = res.json()["ma_don"]

    res_detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=headers)
    detail = res_detail.json()
    assert len(detail["dich_vus"]) == 0
    assert detail["tong_dich_vu"] == 0


def test_referee_quota_limit_rejects_third(client_and_db, authenticated_client):
    """Hạn ngạch trọng tài tối đa 2 trận cùng ca. Trận thứ 3 cùng ca chọn trọng tài phải bị từ chối."""
    client, session = client_and_db
    _, headers = authenticated_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=3)).isoformat()

    # Trận 1 (Sân A): 18:00 - 19:30 có trọng tài -> Thành công
    res1 = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[0].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    assert res1.status_code == 200

    # Trận 2 (Sân B): 18:30 - 20:00 (giao thoa giờ) có trọng tài -> Thành công (đủ 2 trọng tài)
    res2 = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[1].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:30:00",
        "gio_ket_thuc": "20:00:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    assert res2.status_code == 200

    # Trận 3 (Sân C): 19:00 - 20:30 (trùng giờ với cả 2 trận trước) có trọng tài -> BỊ TỪ CHỐI (400)
    res3 = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[2].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "19:00:00",
        "gio_ket_thuc": "20:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    assert res3.status_code == 400
    assert "tối đa 2 trận có trọng tài" in res3.json()["detail"]

    # Nhưng đặt sân C cùng giờ KHÔNG chọn trọng tài thì vẫn THÀNH CÔNG bình thường
    res3_no_ref = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[2].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "19:00:00",
        "gio_ket_thuc": "20:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": False
    })
    assert res3_no_ref.status_code == 200


def test_checkin_preserves_referee_service_on_invoice(client_and_db, authenticated_client, staff_client):
    """Kiểm tra vá lỗ hổng check-in: Hóa đơn tạm tính tính đúng dịch vụ đặt trước thay vì reset về 0."""
    client, session = client_and_db
    _, cust_headers = authenticated_client
    _, staff_headers = staff_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    # 1. Khách đặt sân có trọng tài (1.5h = 450.000đ tiền sân + 200.000đ trọng tài)
    res_b = client.post("/api/dat-san/booking", headers=cust_headers, json={
        "ma_san": sans[0].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    assert res_b.status_code == 200
    ma_don = res_b.json()["ma_don"]

    # 2. Nhân viên duyệt cọc
    res_conf = client.post("/api/dat-san/booking/confirm-deposit", headers=staff_headers, json={
        "ma_don": ma_don,
        "so_tien": 100000,
        "phuong_thuc": "chuyen_khoan"
    })
    assert res_conf.status_code == 200

    # 3. Nhân viên Check-in
    res_ci = client.post("/api/van-hanh/check-in", headers=staff_headers, json={
        "ma_don": ma_don,
        "ghi_chu": "Khách nhận sân đúng giờ"
    })
    assert res_ci.status_code == 200
    invoice_data = res_ci.json()

    # VÁ LỖ HỔNG: tong_dich_vu phải bằng 200.000đ, không được là 0!
    assert invoice_data["tien_san"] == 525000  # 1.5h giờ cao điểm (350k/h)
    assert invoice_data["tong_dich_vu"] == 200000
    assert invoice_data["tien_coc_da_tru"] == 100000
    # Tổng thanh toán = 525k (sân) + 200k (trọng tài) - 100k (cọc) = 625.000đ
    assert invoice_data["tong_thanh_toan"] == 625000

    # 4. Check-out quyết toán
    res_co = client.post(f"/api/van-hanh/check-out?phuong_thuc=chuyen_khoan", headers=staff_headers, json={
        "ma_don": ma_don
    })
    assert res_co.status_code == 200
    final_inv = res_co.json()
    assert final_inv["tong_thanh_toan"] == 625000
    assert final_inv["tong_dich_vu"] == 200000


def test_staff_can_remove_service(client_and_db, authenticated_client, staff_client):
    """Nhân viên có thể xóa/gỡ dịch vụ nếu khách đổi ý, hóa đơn được tự động tính toán lại."""
    client, session = client_and_db
    _, cust_headers = authenticated_client
    _, staff_headers = staff_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=2)).isoformat()
    res_b = client.post("/api/dat-san/booking", headers=cust_headers, json={
        "ma_san": sans[0].ma,
        "ngay_da": target_date,
        "gio_bat_dau": "18:00:00",
        "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000,
        "thue_trong_tai": True
    })
    ma_don = res_b.json()["ma_don"]

    # Lấy su_dung_id của trọng tài
    res_detail = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=cust_headers)
    services = res_detail.json()["dich_vus"]
    assert len(services) == 1
    su_dung_id = services[0]["su_dung_id"]

    # Nhân viên gọi API xóa dịch vụ
    res_del = client.delete(f"/api/van-hanh/service-usage/{ma_don}/{su_dung_id}", headers=staff_headers)
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # Kiểm tra lại chi tiết đơn: danh sách dịch vụ trống
    res_detail2 = client.get(f"/api/dat-san/booking/{ma_don}/detail", headers=cust_headers)
    assert len(res_detail2.json()["dich_vus"]) == 0
    assert res_detail2.json()["tong_dich_vu"] == 0


def test_doi_lich_with_referee_quota_enforced(client_and_db, authenticated_client):
    """Khi đổi lịch cho đơn có trọng tài sang khung giờ đã đủ 2 trọng tài -> Bị từ chối."""
    client, session = client_and_db
    _, headers = authenticated_client
    sans = _setup_multi_sans(session)

    target_date = (get_vn_now().date() + timedelta(days=4)).isoformat()

    # Đặt 2 trận có trọng tài lúc 18:00 - 19:30 trên sân A và B
    client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[0].ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000, "thue_trong_tai": True
    })
    client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[1].ma, "ngay_da": target_date, "gio_bat_dau": "18:00:00", "gio_ket_thuc": "19:30:00",
        "tien_coc": 100000, "thue_trong_tai": True
    })

    # Đặt trận 3 có trọng tài lúc 20:00 - 21:30 trên sân C (khung giờ khác -> thành công)
    res3 = client.post("/api/dat-san/booking", headers=headers, json={
        "ma_san": sans[2].ma, "ngay_da": target_date, "gio_bat_dau": "20:00:00", "gio_ket_thuc": "21:30:00",
        "tien_coc": 100000, "thue_trong_tai": True
    })
    assert res3.status_code == 200
    ma_don_3 = res3.json()["ma_don"]

    # Đổi lịch trận 3 về lúc 18:00 - 19:30 (khung giờ đã có 2 trọng tài) -> Bị từ chối 400!
    res_doi = client.post("/api/dat-san/booking/reschedule", headers=headers, json={
        "ma_don": ma_don_3,
        "ngay_da_moi": target_date,
        "gio_bat_dau_moi": "18:00:00",
        "gio_ket_thuc_moi": "19:30:00"
    })
    assert res_doi.status_code == 400
    assert "tối đa 2 trận có trọng tài" in res_doi.json()["detail"]
