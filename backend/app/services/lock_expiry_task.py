import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.dat_san import DatSan, LichDat
from app.models.ai_models import ThongBao

def check_and_expire_bookings(db: Session):
    """Quét và hủy các đơn giữ chỗ đã hết hạn 10 phút chưa thanh toán cọc."""
    now = datetime.utcnow()
    expired_bookings = db.query(DatSan).filter(
        DatSan.trang_thai == 'cho_coc',
        DatSan.lock_expires_at < now
    ).all()
    
    if not expired_bookings:
        return
        
    for booking in expired_bookings:
        print(f"Lock Expiry Task: Hủy đơn hết hạn giữ chỗ: {booking.ma_don}")
        booking.trang_thai = 'da_huy'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = now
        booking.ghi_chu = (booking.ghi_chu or "") + " [Tự động hủy do quá hạn giữ chỗ 10 phút]"
        
        # Giải phóng lịch sân
        db.query(LichDat).filter(LichDat.ma_don == booking.ma_don).delete()
        
        # Tạo thông báo hết hạn gửi khách hàng
        notif_exp = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=booking.ma_don,
            noi_dung=f"⏰ [HẾT HẠN GIỮ CHỖ] Đơn đặt sân {booking.ma_don} đã bị tự động hủy do quá thời gian giữ chỗ 10 phút chưa thanh toán cọc.",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            da_doc=False,
            ngay_gui=now
        )
        db.add(notif_exp)
        
    db.commit()

async def start_lock_expiry_scheduler():
    """Vòng lặp background quét lịch hết hạn mỗi 30 giây"""
    print("Khởi chạy Background Lock Expiry Task (30s interval)...")
    while True:
        try:
            db = SessionLocal()
            try:
                check_and_expire_bookings(db)
            finally:
                db.close()
        except Exception as e:
            print(f"Lỗi trong Background Lock Expiry Task: {e}")
        await asyncio.sleep(30)
