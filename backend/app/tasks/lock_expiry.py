"""Task nền tự động quét và hủy các đơn giữ chỗ đã quá hạn 10 phút chưa đặt cọc."""

import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.dat_san import DatSan, LichDat
from app.models.thong_bao import ThongBao


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def check_and_expire_bookings(db: Session) -> int:
    """Quét và hủy các đơn giữ chỗ đã hết hạn 10 phút chưa thanh toán cọc.
    
    Returns:
        int: Số lượng đơn vừa được tự động hủy
    """
    now = get_utc_now()
    expired_bookings = db.query(DatSan).filter(
        DatSan.trang_thai == 'cho_coc',
        DatSan.lock_expires_at < now
    ).all()
    
    if not expired_bookings:
        return 0
        
    count = 0
    for booking in expired_bookings:
        print(f"[LockExpiryTask] Tự động hủy đơn hết hạn giữ chỗ: {booking.ma_don}")
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
        count += 1
        
    db.commit()
    return count


async def start_lock_expiry_scheduler():
    """Vòng lặp background quét lịch hết hạn mỗi 30 giây"""
    print("[LockExpiryTask] Khởi chạy Background Scheduler (30s interval)...")
    while True:
        try:
            db = SessionLocal()
            try:
                check_and_expire_bookings(db)
            finally:
                db.close()
        except Exception as e:
            print(f"[LockExpiryTask] Lỗi trong scheduler: {e}")
        await asyncio.sleep(30)
