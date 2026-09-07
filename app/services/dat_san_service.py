from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, date, time, timedelta
import random
from app.models.dat_san import DatSan, LichDat
from app.models.san import San, BangGia
from app.models.tai_khoan import TaiKhoan
from app.models.hoa_don import ThanhToan
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
        
        # Xác định trạng thái ban đầu dựa vào cọc
        if data.tien_coc > 0:
            trang_thai = 'da_xac_nhan'
            lock_expires_at = None
        else:
            trang_thai = 'cho_coc'
            lock_expires_at = datetime.utcnow() + timedelta(minutes=settings.lock_expiry_minutes)
            
        new_booking = DatSan(
            ma_don=ma_don,
            ma_khach_hang=current_user_id,
            ma_san=data.ma_san,
            ngay_da=data.ngay_da,
            gio_bat_dau=data.gio_bat_dau,
            gio_ket_thuc=data.gio_ket_thuc,
            tien_coc=data.tien_coc,
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
        
        # Tạo ThanhToan nếu có cọc
        if data.tien_coc > 0:
            new_payment = ThanhToan(
                ma_don=ma_don,
                so_tien=data.tien_coc,
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
            
        booking.tien_coc = so_tien
        booking.trang_thai = 'da_xac_nhan'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Thêm ThanhToan cọc
        new_payment = ThanhToan(
            ma_don=ma_don,
            so_tien=so_tien,
            phuong_thuc=phuong_thuc,
            loai_giao_dich='dat_coc',
            trang_thai='thanh_cong',
            thoi_gian=datetime.utcnow()
        )
        db.add(new_payment)
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
            
        # Kiểm tra điều kiện hoàn cọc (trước 24h)
        booking_time = datetime.combine(booking.ngay_da, booking.gio_bat_dau)
        if booking.trang_thai == 'da_xac_nhan' and booking.tien_coc > 0:
            if booking_time - datetime.utcnow() >= timedelta(hours=24):
                # Hoàn cọc
                new_payment = ThanhToan(
                    ma_don=ma_don,
                    so_tien=-booking.tien_coc, # Phản ánh số tiền hoàn
                    phuong_thuc='chuyen_khoan',
                    loai_giao_dich='hoan_coc',
                    trang_thai='thanh_cong',
                    thoi_gian=datetime.utcnow()
                )
                db.add(new_payment)
                booking.ghi_chu = (booking.ghi_chu or "") + " [Đã hoàn cọc do hủy trước 24h]"
            else:
                booking.ghi_chu = (booking.ghi_chu or "") + " [Không được hoàn cọc do hủy trễ]"
                
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
