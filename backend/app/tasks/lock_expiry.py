"""Task nền tự động quét và hủy các đơn giữ chỗ đã quá hạn 10 phút chưa đặt cọc."""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.dat_san import DatSan, LichDat
from app.models.thong_bao import ThongBao


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_vn_now() -> datetime:
    vn_tz = timezone(timedelta(hours=7))
    return datetime.now(vn_tz).replace(tzinfo=None)


def check_and_expire_bookings(db: Session) -> int:
    """Quét và xử lý vòng đời các đơn đặt sân:
    1. Đơn cho_coc: Tự động hủy nếu quá hạn giữ chỗ 10 phút hoặc trận đấu đã qua giờ bắt đầu.
    2. Đơn da_xac_nhan: Tự động đóng sang 'hoan_tat' (No-Show) nếu trận đấu đã kết thúc trong quá khứ mà khách không check-in.
    
    Returns:
        int: Tổng số đơn vừa được xử lý
    """
    utc_now = get_utc_now()
    vn_now = get_vn_now()
    count = 0
    
    # --- 1. Xử lý các đơn 'cho_coc' quá hạn 10 phút giữ chỗ ---
    pending_bookings = db.query(DatSan).filter(
        DatSan.trang_thai == 'cho_coc',
        DatSan.lock_expires_at.isnot(None),
        DatSan.lock_expires_at < utc_now
    ).all()
    
    for booking in pending_bookings:
        reason = "quá hạn giữ chỗ 10 phút"
        booking.trang_thai = 'da_huy'
        booking.lock_expires_at = None
        booking.ngay_cap_nhat = utc_now
        booking.ghi_chu = (booking.ghi_chu or "") + f" [Tự động hủy do {reason}]"
        
        # Giải phóng lịch sân
        db.query(LichDat).filter(LichDat.ma_don == booking.ma_don).delete()
        
        # Tạo thông báo hết hạn gửi khách hàng
        notif_exp = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=booking.ma_don,
            noi_dung=f"⏰ [HẾT HẠN GIỮ CHỖ] Đơn đặt sân {booking.ma_don} đã bị tự động hủy do {reason} chưa thanh toán cọc.",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            da_doc=False,
            ngay_gui=utc_now
        )
        db.add(notif_exp)
        count += 1
            
    # --- 2. Xử lý các đơn 'da_xac_nhan' trong quá khứ mà khách không đến nhận sân (No-Show) ---
    confirmed_bookings = db.query(DatSan).filter(
        DatSan.trang_thai == 'da_xac_nhan'
    ).all()
    
    for booking in confirmed_bookings:
        booking_end = datetime.combine(booking.ngay_da, booking.gio_ket_thuc)
        if booking_end <= vn_now:
            # Trận đấu đã kết thúc hoàn toàn trong quá khứ mà khách không check-in
            booking.trang_thai = 'hoan_tat'
            booking.ngay_cap_nhat = utc_now
            booking.ghi_chu = (booking.ghi_chu or "") + " [Tự động đóng: Khách không đến nhận sân (No-Show)]"
            
            # Giải phóng slot trong LichDat vì trận đấu đã kết thúc
            db.query(LichDat).filter(LichDat.ma_don == booking.ma_don).delete()
            
            # Tạo thông báo gửi khách hàng
            notif_noshow = ThongBao(
                tai_khoan_id=booking.ma_khach_hang,
                ma_don=booking.ma_don,
                noi_dung=(
                    f"🏁 [KẾT THÚC LƯỢT ĐẶT] Đơn {booking.ma_don} ({booking.ma_san}) ngày {booking.ngay_da.strftime('%d/%m/%Y')} "
                    f"lúc {booking.gio_bat_dau.strftime('%H:%M')}-{booking.gio_ket_thuc.strftime('%H:%M')} đã kết thúc giờ thi đấu (Khách vắng mặt). "
                    f"Tiền cọc đã được quyết toán theo quy chế của sân."
                ),
                kenh_gui='web',
                trang_thai_gui='da_gui',
                da_doc=False,
                ngay_gui=utc_now
            )
            db.add(notif_noshow)
            count += 1
            
    if count > 0:
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
