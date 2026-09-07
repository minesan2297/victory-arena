from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import datetime, date, time, timedelta
import random
import urllib.parse
from app.models.dat_san import DatSan, LichDat
from app.models.san import San, BangGia
from app.models.tai_khoan import TaiKhoan
from app.models.hoa_don import ThanhToan
from app.models.ai_models import ThongBao
from app.schemas.dat_san_schema import DatSanCreate, DoiLichRequest, LichSanResponse, SlotInfo
from app.config import get_settings

class DatSanService:
    @staticmethod
    def calculate_price(db: Session, san_id: str, ngay_da: date, gio_bat_dau: time, gio_ket_thuc: time) -> int:
        # Xác định loại ngày
        weekday = ngay_da.weekday()
        loai_ngay = 'cuoi_tuan' if weekday >= 5 else 'thuong'
        
        # Tìm bảng giá phù hợp nhất
        pricing = db.query(BangGia).filter(
            BangGia.san_id == san_id,
            BangGia.loai_ngay == loai_ngay,
            BangGia.gio_bat_dau <= gio_bat_dau,
            BangGia.gio_ket_thuc >= gio_ket_thuc
        ).first()
        
        if pricing:
            don_gia = pricing.don_gia
        else:
            # Fallback sang bảng giá bất kỳ của sân hoặc giá mặc định
            pricing = db.query(BangGia).filter(BangGia.san_id == san_id).first()
            don_gia = pricing.don_gia if pricing else 200000
            
        # Tính thời gian (giờ)
        dt_start = datetime.combine(date.min, gio_bat_dau)
        dt_end = datetime.combine(date.min, gio_ket_thuc)
        duration_hours = (dt_end - dt_start).total_seconds() / 3600.0
        
        return int(round(duration_hours * don_gia))

    @staticmethod
    def check_conflict(db: Session, san_id: str, ngay_da: date, gio_bat_dau: time, gio_ket_thuc: time, exclude_ma_don: str = None) -> bool:
        # Kiểm tra trạng thái sân hoạt động
        court = db.query(San).filter(San.ma == san_id).first()
        if not court or court.trang_thai == 'inactive':
            return True
            
        # Tạo mốc thời gian datetime
        bat_dau_dt = datetime.combine(ngay_da, gio_bat_dau)
        ket_thuc_dt = datetime.combine(ngay_da, gio_ket_thuc)
        
        # Lấy lịch đặt có trùng lắp
        query = db.query(LichDat).filter(
            LichDat.san_id == san_id,
            LichDat.bat_dau < ket_thuc_dt,
            LichDat.ket_thuc > bat_dau_dt
        )
        
        if exclude_ma_don:
            query = query.filter(LichDat.ma_don != exclude_ma_don)
            
        conflicts = query.all()
        for c in conflicts:
            # Nếu là lịch bảo trì hoặc đơn thuê đang hoạt động (chưa hủy và chưa hết hạn lock)
            if c.loai_lich == 'bao_tri':
                return True
            if c.dat_san:
                if c.dat_san.trang_thai == 'da_huy':
                    continue
                # Kiểm tra xem có bị hết hạn giữ chỗ (lock) hay không
                if c.dat_san.trang_thai == 'cho_coc' and c.dat_san.lock_expires_at:
                    if datetime.utcnow() > c.dat_san.lock_expires_at:
                        continue
                return True
                
        return False

    @staticmethod
    def create_booking(db: Session, data: DatSanCreate, current_user_id: int) -> DatSan:
        if data.gio_bat_dau >= data.gio_ket_thuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giờ bắt đầu phải nhỏ hơn giờ kết thúc"
            )
            
        # Kiểm tra trùng lịch
        if DatSanService.check_conflict(db, data.ma_san, data.ngay_da, data.gio_bat_dau, data.gio_ket_thuc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khung giờ này đã có người đặt hoặc đang bảo trì"
            )
            
        # Tạo mã đơn duy nhất (DS + YYYYMMDD + 4 số ngẫu nhiên)
        date_str = data.ngay_da.strftime("%Y%m%d")
        while True:
            ma_don = f"DS{date_str}-{random.randint(1000, 9999)}"
            if not db.query(DatSan).filter(DatSan.ma_don == ma_don).first():
                break
                
        settings = get_settings()
        
        # Kiểm tra vai trò của người đặt đơn
        user = db.query(TaiKhoan).filter(TaiKhoan.tai_khoan_id == current_user_id).first()
        is_staff_or_admin = bool(user and user.vai_tro and user.vai_tro.ten_vai_tro in ['STAFF', 'ADMIN'])
        
        # Tính toán tiền thuê sân ước tính
        tien_san_est = DatSanService.calculate_price(db, data.ma_san, data.ngay_da, data.gio_bat_dau, data.gio_ket_thuc)
        
        # Tiền cọc tối thiểu theo quy định: 30% tiền thuê sân, tối thiểu 100.000 VNĐ
        min_deposit = max(100000, int(round(tien_san_est * 0.3, -3)))
        
        # Khắc phục lỗ hổng kinh tế:
        # Khách hàng (CUSTOMER) KHÔNG THỂ tự động kích hoạt đơn 'da_xac_nhan'.
        # Đơn luôn ở trạng thái 'cho_coc' với khóa 10 phút để chờ thanh toán cọc và duyệt bill.
        # Chỉ Staff hoặc Admin tại quầy mới được phép thu cọc trực tiếp và kích hoạt 'da_xac_nhan' ngay.
        if is_staff_or_admin and data.tien_coc >= min_deposit:
            trang_thai = 'da_xac_nhan'
            lock_expires_at = None
            tien_coc_ghi_nhan = int(data.tien_coc)
        else:
            trang_thai = 'cho_coc'
            lock_expires_at = datetime.utcnow() + timedelta(minutes=settings.lock_expiry_minutes)
            tien_coc_ghi_nhan = min_deposit
            
        new_booking = DatSan(
            ma_don=ma_don,
            ma_khach_hang=current_user_id,
            ma_san=data.ma_san,
            ngay_da=data.ngay_da,
            gio_bat_dau=data.gio_bat_dau,
            gio_ket_thuc=data.gio_ket_thuc,
            tien_coc=tien_coc_ghi_nhan,
            trang_thai=trang_thai,
            lock_expires_at=lock_expires_at,
            ghi_chu=data.ghi_chu,
            ngay_tao=datetime.utcnow()
        )
        db.add(new_booking)
        db.flush() # Lấy ID/Mã đơn
        
        # Thêm vào bảng LichDat
        bat_dau_dt = datetime.combine(data.ngay_da, data.gio_bat_dau)
        ket_thuc_dt = datetime.combine(data.ngay_da, data.gio_ket_thuc)
        new_lich = LichDat(
            san_id=data.ma_san,
            ma_don=ma_don,
            bat_dau=bat_dau_dt,
            ket_thuc=ket_thuc_dt,
            loai_lich='thue'
        )
        db.add(new_lich)
        
        # Chỉ tạo bản ghi ThanhToan thành công nếu là nhân viên/admin trực tiếp thu tiền tại quầy
        if is_staff_or_admin and data.tien_coc >= min_deposit:
            new_payment = ThanhToan(
                ma_don=ma_don,
                so_tien=int(data.tien_coc),
                phuong_thuc=data.phuong_thuc_thanh_toan,
                loai_giao_dich='dat_coc',
                trang_thai='thanh_cong',
                thoi_gian=datetime.utcnow()
            )
            db.add(new_payment)
            
        db.commit()
        db.refresh(new_booking)
        return new_booking

    @staticmethod
    def xac_nhan_coc(db: Session, ma_don: str, so_tien: float, phuong_thuc: str) -> DatSan:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai != 'cho_coc':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đơn đặt sân không ở trạng thái Chờ cọc")
            
        # Kiểm tra lock hết hạn
        if booking.lock_expires_at and datetime.utcnow() > booking.lock_expires_at:
            booking.trang_thai = 'da_huy'
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giờ giữ chỗ (lock 10 phút) đã hết hạn")
            
        # Tính tiền sân để kiểm tra cận trên/dưới cọc hợp lý
        tien_san_est = DatSanService.calculate_price(db, booking.ma_san, booking.ngay_da, booking.gio_bat_dau, booking.gio_ket_thuc)
        if so_tien <= 0 or so_tien > tien_san_est:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số tiền cọc không hợp lệ (phải từ 1đ đến tối đa {tien_san_est:,}đ)"
            )
            
        booking.tien_coc = int(so_tien)
        booking.trang_thai = 'da_xac_nhan'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Thêm ThanhToan cọc
        new_payment = ThanhToan(
            ma_don=ma_don,
            so_tien=int(so_tien),
            phuong_thuc=phuong_thuc,
            loai_giao_dich='dat_coc',
            trang_thai='thanh_cong',
            thoi_gian=datetime.utcnow()
        )
        db.add(new_payment)
        
        # Tạo thông báo xác nhận cọc
        notif = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=ma_don,
            noi_dung=f"Đơn đặt sân {ma_don} đã được xác nhận đặt cọc thành công số tiền {int(so_tien):,} ₫ qua {phuong_thuc}!",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            ngay_gui=datetime.utcnow()
        )
        db.add(notif)
        
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def doi_lich(db: Session, data: DoiLichRequest) -> DatSan:
        booking = db.query(DatSan).filter(DatSan.ma_don == data.ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai not in ['cho_coc', 'da_xac_nhan']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ được đổi lịch cho đơn ở trạng thái Chờ cọc hoặc Đã xác nhận")
            
        # Các thông tin mới (hoặc giữ cũ)
        ngay_da = data.ngay_da_moi or booking.ngay_da
        gio_bat_dau = data.gio_bat_dau_moi or booking.gio_bat_dau
        gio_ket_thuc = data.gio_ket_thuc_moi or booking.gio_ket_thuc
        ma_san = data.ma_san_moi or booking.ma_san
        
        if gio_bat_dau >= gio_ket_thuc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giờ bắt đầu phải nhỏ hơn giờ kết thúc")
            
        # Kiểm tra trùng lịch
        if DatSanService.check_conflict(db, ma_san, ngay_da, gio_bat_dau, gio_ket_thuc, exclude_ma_don=booking.ma_don):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Khung giờ mới đã bị trùng lịch")
            
        # Cập nhật thông tin đơn đặt
        booking.ngay_da = ngay_da
        booking.gio_bat_dau = gio_bat_dau
        booking.gio_ket_thuc = gio_ket_thuc
        booking.ma_san = ma_san
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Cập nhật LichDat tương ứng
        lich = db.query(LichDat).filter(LichDat.ma_don == booking.ma_don).first()
        if lich:
            lich.san_id = ma_san
            lich.bat_dau = datetime.combine(ngay_da, gio_bat_dau)
            lich.ket_thuc = datetime.combine(ngay_da, gio_ket_thuc)
            
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def huy_lich(db: Session, ma_don: str) -> DatSan:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai not in ['cho_coc', 'da_xac_nhan']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể hủy đơn ở trạng thái hiện tại")
            
        # Kiểm tra tổng tiền cọc thực tế đã thanh toán thành công trong bảng ThanhToan
        tong_coc_thuc_te = db.query(func.sum(ThanhToan.so_tien)).filter(
            ThanhToan.ma_don == ma_don,
            ThanhToan.loai_giao_dich == 'dat_coc',
            ThanhToan.trang_thai == 'thanh_cong'
        ).scalar() or 0
        
        da_hoan = db.query(func.sum(ThanhToan.so_tien)).filter(
            ThanhToan.ma_don == ma_don,
            ThanhToan.loai_giao_dich == 'hoan_coc'
        ).scalar() or 0
        
        # Điều kiện hoàn cọc: Chỉ hoàn nếu đơn đã xác nhận, thực tế đã có tiền cọc đóng thành công và chưa hoàn lần nào
        booking_time = datetime.combine(booking.ngay_da, booking.gio_bat_dau)
        if booking.trang_thai == 'da_xac_nhan' and tong_coc_thuc_te > 0 and da_hoan == 0:
            if booking_time - datetime.utcnow() >= timedelta(hours=24):
                # Hoàn cọc số tiền thực tế khách đã nộp
                so_tien_hoan = int(tong_coc_thuc_te)
                new_payment = ThanhToan(
                    ma_don=ma_don,
                    so_tien=-so_tien_hoan,
                    phuong_thuc='chuyen_khoan',
                    loai_giao_dich='hoan_coc',
                    trang_thai='thanh_cong',
                    thoi_gian=datetime.utcnow()
                )
                db.add(new_payment)
                booking.ghi_chu = (booking.ghi_chu or "") + f" [Đã hoàn cọc {so_tien_hoan:,}đ do hủy trước 24h]"
            else:
                booking.ghi_chu = (booking.ghi_chu or "") + " [Không được hoàn cọc do hủy trễ < 24h]"
                
        # Cập nhật trạng thái
        booking.trang_thai = 'da_huy'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Xóa khỏi LichDat để giải phóng lịch sân
        db.query(LichDat).filter(LichDat.ma_don == ma_don).delete()
        
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def generate_deposit_qr(db: Session, ma_don: str, phuong_thuc: str = 'chuyen_khoan') -> dict:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        amount = int(booking.tien_coc)
        if amount <= 0:
            tien_san = DatSanService.calculate_price(db, booking.ma_san, booking.ngay_da, booking.gio_bat_dau, booking.gio_ket_thuc)
            amount = max(100000, int(round(tien_san * 0.3, -3)))
            booking.tien_coc = amount
            db.commit()
            
        memo = f"COC {ma_don}"
        account_no = "0988123456"
        bank_id = "MB"
        account_name = "SAN BONG VICTORY ARENA"
        
        enc_memo = urllib.parse.quote(memo)
        enc_name = urllib.parse.quote(account_name)
        vietqr_url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.png?amount={amount}&addInfo={enc_memo}&accountName={enc_name}"
        
        momo_data = f"2|99|{account_no}|{account_name}|sanbongvictory@gmail.com|0|0|{amount}|{memo}|transfer_myqr"
        momo_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(momo_data)}"
        
        vnpay_data = f"VNPAYQR://pay?merchant=VICTORYARENA&amount={amount}&orderId={ma_don}&desc={memo}"
        vnpay_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(vnpay_data)}"
        
        con_lai_giay = 0
        if booking.lock_expires_at:
            diff = (booking.lock_expires_at - datetime.utcnow()).total_seconds()
            con_lai_giay = max(0, int(diff))
            
        return {
            "ma_don": ma_don,
            "so_tien": amount,
            "noi_dung": memo,
            "ngan_hang": "MBBank (Ngân hàng Quân Đội)",
            "so_tai_khoan": account_no,
            "chu_tai_khoan": account_name,
            "vietqr_url": vietqr_url,
            "momo_qr_url": momo_qr_url,
            "vnpay_qr_url": vnpay_qr_url,
            "phuong_thuc": phuong_thuc,
            "loai_thanh_toan": "dat_coc",
            "lock_expires_at": booking.lock_expires_at,
            "con_lai_giay": con_lai_giay
        }

    @staticmethod
    def sandbox_qr_pay(db: Session, ma_don: str, phuong_thuc: str = 'chuyen_khoan') -> DatSan:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai != 'cho_coc':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đơn đặt sân không ở trạng thái Chờ cọc")
            
        if booking.lock_expires_at and datetime.utcnow() > booking.lock_expires_at:
            booking.trang_thai = 'da_huy'
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thời hạn 10 phút giữ sân đã hết hạn")
            
        amount = int(booking.tien_coc)
        if amount <= 0:
            tien_san = DatSanService.calculate_price(db, booking.ma_san, booking.ngay_da, booking.gio_bat_dau, booking.gio_ket_thuc)
            amount = max(100000, int(round(tien_san * 0.3, -3)))
            booking.tien_coc = amount
            
        booking.trang_thai = 'da_xac_nhan'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Thêm ThanhToan cọc
        new_payment = ThanhToan(
            ma_don=ma_don,
            so_tien=amount,
            phuong_thuc=phuong_thuc,
            loai_giao_dich='dat_coc',
            trang_thai='thanh_cong',
            thoi_gian=datetime.utcnow()
        )
        db.add(new_payment)
        
        # Tạo thông báo
        notif = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=ma_don,
            noi_dung=f"[Sandbox/QR] Thanh toán cọc {amount:,} ₫ qua {phuong_thuc} thành công! Đơn {ma_don} đã được duyệt tự động.",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            ngay_gui=datetime.utcnow()
        )
        db.add(notif)
        
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get_day_schedule(db: Session, query_date: date, san_id: str = None) -> LichSanResponse:
        # Nếu không truyền san_id, lấy sân đầu tiên
        if not san_id:
            first_court = db.query(San).first()
            if not first_court:
                return LichSanResponse(ngay=query_date, tong_san=0, slots=[])
            san_id = first_court.ma
            
        court = db.query(San).filter(San.ma == san_id).first()
        if not court:
            raise HTTPException(status_code=404, detail="Sân không tồn tại")
            
        # 9 khung giờ cố định trong ngày
        fixed_slots = [
            (time(6, 0), time(7, 30)),
            (time(7, 30), time(9, 0)),
            (time(9, 0), time(10, 30)),
            (time(14, 0), time(15, 30)),
            (time(15, 30), time(17, 0)),
            (time(17, 0), time(18, 30)),
            (time(18, 30), time(20, 0)),
            (time(20, 0), time(21, 30)),
            (time(21, 30), time(23, 0))
        ]
        
        slots_info = []
        for start, end in fixed_slots:
            # Tính đơn giá
            don_gia = DatSanService.calculate_price(db, san_id, query_date, start, end)
            
            # Kiểm tra trạng thái slot
            bat_dau_dt = datetime.combine(query_date, start)
            ket_thuc_dt = datetime.combine(query_date, end)
            
            lich = db.query(LichDat).filter(
                LichDat.san_id == san_id,
                LichDat.bat_dau < ket_thuc_dt,
                LichDat.ket_thuc > bat_dau_dt
            ).first()
            
            trang_thai = 'AVAILABLE'
            ma_don = None
            ten_khach = None
            
            if lich:
                if lich.loai_lich == 'bao_tri':
                    trang_thai = 'MAINTENANCE'
                elif lich.dat_san:
                    ma_don = lich.dat_san.ma_don
                    ten_khach = lich.dat_san.khach_hang.ho_ten
                    if lich.dat_san.trang_thai == 'cho_coc':
                        if lich.dat_san.lock_expires_at and datetime.utcnow() > lich.dat_san.lock_expires_at:
                            trang_thai = 'AVAILABLE'
                            ma_don = None
                            ten_khach = None
                        else:
                            trang_thai = 'LOCKED'
                    elif lich.dat_san.trang_thai in ['da_xac_nhan', 'dang_da', 'hoan_tat']:
                        trang_thai = 'BOOKED'
                    elif lich.dat_san.trang_thai == 'da_huy':
                        trang_thai = 'AVAILABLE'
                        ma_don = None
                        ten_khach = None
                        
            slots_info.append(SlotInfo(
                san_id=san_id,
                ten_san=court.ten_san,
                loai_san=court.loai_san.ten_loai,
                gio_bat_dau=start,
                gio_ket_thuc=end,
                don_gia=don_gia,
                trang_thai=trang_thai,
                ma_don=ma_don,
                ten_khach=ten_khach
            ))
            
        tong_san = db.query(San).count()
        return LichSanResponse(ngay=query_date, tong_san=tong_san, slots=slots_info)
