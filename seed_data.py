import sys
from datetime import date, time, datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.auth.security import hash_password
from app.models.enums import VaiTroEnum, LoaiNgay, TrangThaiSan, TrangThaiDatSan
from app.models.tai_khoan import VaiTro, TaiKhoan
from app.models.san import LoaiSan, San, BangGia
from app.models.dat_san import DatSan, LichDat
from app.models.hoa_don import HoaDon, CheckIn, ThanhToan
from app.models.dich_vu import DanhMucDichVu, SuDungDichVu
from app.models.ai_models import AIConfig

# Đảm bảo in Unicode tiếng Việt mượt mà trên Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def seed_database():
    print("🚀 Bắt đầu khởi tạo CSDL và nạp dữ liệu mẫu (Sân 7 & Sân 11)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed VaiTro
        v_admin = VaiTro(ten_vai_tro="ADMIN", mo_ta="Quản trị viên hệ thống")
        v_staff = VaiTro(ten_vai_tro="STAFF", mo_ta="Nhân viên vận hành sân")
        v_customer = VaiTro(ten_vai_tro="CUSTOMER", mo_ta="Khách hàng đặt sân")
        db.add_all([v_admin, v_staff, v_customer])
        db.flush()
        
        # 2. Seed TaiKhoan
        admin = TaiKhoan(
            ten_dang_nhap="admin",
            mat_khau_hash=hash_password("admin123"),
            ho_ten="Nguyễn Quản Trị",
            so_dien_thoai="0901000001",
            email="admin@minivictory.ai",
            vai_tro_id=v_admin.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        staff = TaiKhoan(
            ten_dang_nhap="staff",
            mat_khau_hash=hash_password("staff123"),
            ho_ten="Trần Lễ Tân",
            so_dien_thoai="0901000002",
            email="staff@minivictory.ai",
            vai_tro_id=v_staff.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach1 = TaiKhoan(
            ten_dang_nhap="tuanfc",
            mat_khau_hash=hash_password("tuan123"),
            ho_ten="Trần Minh Tuấn (FC Barcelona)",
            so_dien_thoai="0988111222",
            email="tuanfc@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach2 = TaiKhoan(
            ten_dang_nhap="haihoang",
            mat_khau_hash=hash_password("hai123"),
            ho_ten="Lê Hoàng Hải",
            so_dien_thoai="0977333444",
            email="haihoang@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=90,
            trang_thai="active"
        )
        khach3 = TaiKhoan(
            ten_dang_nhap="ducanhfc",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Đức Anh (FC Thanh Niên)",
            so_dien_thoai="0912345678",
            email="ducanh@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach4 = TaiKhoan(
            ten_dang_nhap="hungdung",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Đỗ Hùng Dũng (Hà Nội FC Fans)",
            so_dien_thoai="0934567890",
            email="hungdung@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach5 = TaiKhoan(
            ten_dang_nhap="vietanhfc",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Bùi Hoàng Việt Anh (FC Phủi)",
            so_dien_thoai="0945678901",
            email="vietanh@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach6 = TaiKhoan(
            ten_dang_nhap="quanghai",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Nguyễn Quang Hải (CAHN Fanclub)",
            so_dien_thoai="0967890123",
            email="quanghai@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach7 = TaiKhoan(
            ten_dang_nhap="vanhau",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Đoàn Văn Hậu (FC Thái Bình)",
            so_dien_thoai="0978901234",
            email="vanhau@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        khach8 = TaiKhoan(
            ten_dang_nhap="tienlinh",
            mat_khau_hash=hash_password("123456"),
            ho_ten="Nguyễn Tiến Linh (FC Bcons)",
            so_dien_thoai="0989012345",
            email="tienlinh@gmail.com",
            vai_tro_id=v_customer.vai_tro_id,
            diem_uy_tin=100,
            trang_thai="active"
        )
        db.add_all([admin, staff, khach1, khach2, khach3, khach4, khach5, khach6, khach7, khach8])
        db.flush()
        
        # 3. Seed LoaiSan (Chỉ giữ Sân 7 và Sân 11)
        l7 = LoaiSan(ten_loai="Sân 7", so_nguoi_tieu_chuan=7, mo_ta="Sân cỏ nhân tạo 7 người cao cấp")
        l11 = LoaiSan(ten_loai="Sân 11", so_nguoi_tieu_chuan=11, mo_ta="Sân cỏ tự nhiên tiêu chuẩn thi đấu FIFA")
        db.add_all([l7, l11])
        db.flush()
        
        # 4. Seed San (Chỉ Sân 7 và Sân 11)
        s7a = San(ma="SAN7-001", ten_san="Sân 7A - Phủi Pro", loai_san_id=l7.loai_san_id, vi_tri="Khu B", trang_thai="active", mo_ta_ai="Sân cỏ 7 người dàn đèn 400W tiêu chuẩn")
        s7b = San(ma="SAN7-002", ten_san="Sân 7B - Bernabeu Field", loai_san_id=l7.loai_san_id, vi_tri="Khu B", trang_thai="active", mo_ta_ai="Sân 7 người mặt cỏ FIFA 2 sao")
        s7c = San(ma="SAN7-003", ten_san="Sân 7C - Champions League", loai_san_id=l7.loai_san_id, vi_tri="Khu B", trang_thai="active", mo_ta_ai="Sân 7 người hệ thống thoát nước mượt mà")
        s11a = San(ma="SAN11-001", ten_san="Sân Vận Động FIFA 11A", loai_san_id=l11.loai_san_id, vi_tri="Khu C", trang_thai="active", mo_ta_ai="Sân 11 người khán đài 500 chỗ ngồi")
        s11b = San(ma="SAN11-002", ten_san="Sân Vận Động FIFA 11B", loai_san_id=l11.loai_san_id, vi_tri="Khu C", trang_thai="active", mo_ta_ai="Sân 11 người thi đấu đêm cao cấp")
        db.add_all([s7a, s7b, s7c, s11a, s11b])
        db.flush()
        
        # 5. Seed BangGia
        prices = [
            # Sân 7
            BangGia(san_id=s7a.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(17,30), don_gia=400000, loai_ngay=LoaiNgay.THUONG.value),
            BangGia(san_id=s7a.ma, gio_bat_dau=time(17,30), gio_ket_thuc=time(23,0), don_gia=600000, loai_ngay=LoaiNgay.THUONG.value),
            BangGia(san_id=s7a.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(23,0), don_gia=650000, loai_ngay=LoaiNgay.CUOI_TUAN.value),
            
            BangGia(san_id=s7b.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(17,30), don_gia=400000, loai_ngay=LoaiNgay.THUONG.value),
            BangGia(san_id=s7b.ma, gio_bat_dau=time(17,30), gio_ket_thuc=time(23,0), don_gia=600000, loai_ngay=LoaiNgay.THUONG.value),
            
            BangGia(san_id=s7c.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(23,0), don_gia=500000, loai_ngay=LoaiNgay.THUONG.value),
            
            # Sân 11
            BangGia(san_id=s11a.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(17,30), don_gia=800000, loai_ngay=LoaiNgay.THUONG.value),
            BangGia(san_id=s11a.ma, gio_bat_dau=time(17,30), gio_ket_thuc=time(23,0), don_gia=1200000, loai_ngay=LoaiNgay.THUONG.value),
            BangGia(san_id=s11b.ma, gio_bat_dau=time(6,0), gio_ket_thuc=time(23,0), don_gia=1000000, loai_ngay=LoaiNgay.THUONG.value),
        ]
        db.add_all(prices)
        db.flush()
        
        # 6. Seed DanhMucDichVu
        dv1 = DanhMucDichVu(ten_dich_vu="Nước suối Aquafina 500ml", don_vi_tinh="Chai", don_gia=10000, danh_muc="NUOC_UONG")
        dv2 = DanhMucDichVu(ten_dich_vu="Nước ngọt Pocari Sweat 500ml", don_vi_tinh="Chai", don_gia=20000, danh_muc="NUOC_UONG")
        dv3 = DanhMucDichVu(ten_dich_vu="Thuê áo bib (bộ 7 chiếc)", don_vi_tinh="Lượt", don_gia=30000, danh_muc="TRANG_BI")
        dv4 = DanhMucDichVu(ten_dich_vu="Thuê quả bóng số 5", don_vi_tinh="Lượt", don_gia=50000, danh_muc="TRANG_BI")
        db.add_all([dv1, dv2, dv3, dv4])
        db.flush()
        
        # 7. Seed AIConfig
        ai_cfg = AIConfig(
            provider="google",
            model="gemini-1.5-flash",
            api_key_encrypted="",
            prompt_template="",
            trang_thai="active"
        )
        db.add(ai_cfg)
        db.flush()
        
        # 8. Seed Lịch bảo trì mẫu (Sân 7B bảo trì chiều nay)
        today = date.today()
        maint = LichDat(
            san_id=s7b.ma,
            ma_don=None,
            bat_dau=datetime.combine(today, time(14, 0)),
            ket_thuc=datetime.combine(today, time(15, 30)),
            loai_lich='bao_tri',
            ghi_chu="Chải hạt cao su và căng lại lưới cầu môn"
        )
        db.add(maint)
        db.flush()
        
        # 9. Seed Trận đấu mẫu đã đặt cọc
        b1 = DatSan(
            ma_don="DS20260822-001",
            ma_khach_hang=khach1.tai_khoan_id,
            ma_san=s7a.ma,
            ngay_da=today,
            gio_bat_dau=time(18, 30),
            gio_ket_thuc=time(20, 0),
            tien_coc=200000,
            trang_thai=TrangThaiDatSan.DA_XAC_NHAN.value,
            lock_expires_at=None,
            ghi_chu="Trận derby nội bộ"
        )
        db.add(b1)
        db.flush()
        
        # LichDat cho đơn đặt cọc
        l1 = LichDat(
            san_id=s7a.ma,
            ma_don=b1.ma_don,
            bat_dau=datetime.combine(today, time(18, 30)),
            ket_thuc=datetime.combine(today, time(20, 0)),
            loai_lich='thue'
        )
        db.add(l1)
        
        # Thanh toán cọc
        t1 = ThanhToan(
            ma_don=b1.ma_don,
            so_tien=200000,
            phuong_thuc="chuyen_khoan",
            loai_giao_dich="dat_coc",
            trang_thai="thanh_cong"
        )
        db.add(t1)

        # 10. Seed Lịch đá khách ảo từ 09/09/2026 đến 11/09/2026
        mock_bookings = [
            # Ngày 09/09/2026
            ("DS20260909-001", khach3.tai_khoan_id, s7a.ma, date(2026, 9, 9), time(17, 30), time(19, 0), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Giao lưu bóng đá công ty xây dựng", "chuyen_khoan"),
            ("DS20260909-002", khach4.tai_khoan_id, s7b.ma, date(2026, 9, 9), time(19, 0), time(20, 30), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Đá phủi tranh cúp mini", "vnpay"),
            ("DS20260909-003", khach5.tai_khoan_id, s7c.ma, date(2026, 9, 9), time(20, 0), time(21, 30), 200000, TrangThaiDatSan.CHO_COC.value, "Đội bóng sinh viên K23", "tien_mat"),
            ("DS20260909-004", khach6.tai_khoan_id, s11a.ma, date(2026, 9, 9), time(18, 0), time(20, 0), 500000, TrangThaiDatSan.DA_XAC_NHAN.value, "Trận bóng đá sân 11 hiệp hội doanh nghiệp", "chuyen_khoan"),
            # Ngày 10/09/2026
            ("DS20260910-001", khach1.tai_khoan_id, s7a.ma, date(2026, 9, 10), time(18, 0), time(19, 30), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Trận nội bộ FC Barcelona Fanclub", "momo"),
            ("DS20260910-002", khach7.tai_khoan_id, s7b.ma, date(2026, 9, 10), time(19, 30), time(21, 0), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Đội IT ngân hàng giao hữu", "chuyen_khoan"),
            ("DS20260910-003", khach2.tai_khoan_id, s7c.ma, date(2026, 9, 10), time(17, 30), time(19, 0), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "CLB thể thao quận Hoàng Mai", "tien_mat"),
            ("DS20260910-004", khach8.tai_khoan_id, s11b.ma, date(2026, 9, 10), time(19, 0), time(21, 0), 500000, TrangThaiDatSan.DA_XAC_NHAN.value, "Trận thi đấu giải bóng đá mở rộng 11 người", "vnpay"),
            # Ngày 11/09/2026
            ("DS20260911-001", khach4.tai_khoan_id, s7a.ma, date(2026, 9, 11), time(17, 0), time(18, 30), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Đá bóng sau giờ làm việc thứ 6", "chuyen_khoan"),
            ("DS20260911-002", khach3.tai_khoan_id, s7a.ma, date(2026, 9, 11), time(19, 0), time(20, 30), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Trận siêu kinh điển phủi cuối tuần", "momo"),
            ("DS20260911-003", khach5.tai_khoan_id, s7b.ma, date(2026, 9, 11), time(18, 30), time(20, 0), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Giao hữu các trường đại học", "chuyen_khoan"),
            ("DS20260911-004", khach7.tai_khoan_id, s7c.ma, date(2026, 9, 11), time(19, 30), time(21, 0), 200000, TrangThaiDatSan.DA_XAC_NHAN.value, "Đội bóng cơ quan viễn thông", "vnpay"),
            ("DS20260911-005", khach6.tai_khoan_id, s11a.ma, date(2026, 9, 11), time(18, 30), time(20, 30), 500000, TrangThaiDatSan.DA_XAC_NHAN.value, "Chung kết cúp bóng đá sân 11 Victory", "chuyen_khoan"),
        ]

        for ma_don, uid, san_id, n_da, g_start, g_end, t_coc, t_thai, gchu, pttt in mock_bookings:
            d_san = DatSan(
                ma_don=ma_don,
                ma_khach_hang=uid,
                ma_san=san_id,
                ngay_da=n_da,
                gio_bat_dau=g_start,
                gio_ket_thuc=g_end,
                tien_coc=t_coc,
                trang_thai=t_thai,
                lock_expires_at=None,
                ghi_chu=gchu
            )
            db.add(d_san)
            db.flush()

            l_dat = LichDat(
                san_id=san_id,
                ma_don=ma_don,
                bat_dau=datetime.combine(n_da, g_start),
                ket_thuc=datetime.combine(n_da, g_end),
                loai_lich="thue",
                ghi_chu=gchu
            )
            db.add(l_dat)

            if t_thai == TrangThaiDatSan.DA_XAC_NHAN.value:
                pay = ThanhToan(
                    ma_don=ma_don,
                    so_tien=t_coc,
                    phuong_thuc=pttt,
                    loai_giao_dich="dat_coc",
                    trang_thai="thanh_cong"
                )
                db.add(pay)

        db.commit()
        print("✅ Đã nạp thành công CSDL mẫu chỉ chứa Sân 7 & Sân 11 kèm các lịch đá 09-11/09/2026!")
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi nạp dữ liệu: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
