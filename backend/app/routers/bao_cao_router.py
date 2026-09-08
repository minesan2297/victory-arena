from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.auth.dependencies import require_staff_or_admin
from app.models.tai_khoan import TaiKhoan
from app.models.san import San
from app.models.dat_san import DatSan
from app.models.hoa_don import ThanhToan

router = APIRouter(prefix="/api/bao-cao", tags=["Báo cáo thống kê"])

@router.get("/dashboard")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    tong_san = db.query(San).count()
    san_hoat_dong = db.query(San).filter(San.trang_thai == 'active').count()
    
    tong_dat_san = db.query(DatSan).filter(DatSan.trang_thai != 'da_huy').count()
    
    # Tính tổng doanh thu từ các hóa đơn thanh toán thành công
    payments = db.query(ThanhToan).filter(ThanhToan.trang_thai == 'thanh_cong').all()
    tong_doanh_thu = sum(p.so_tien for p in payments)
    
    # Thống kê hiệu suất từng sân
    courts = db.query(San).all()
    court_performance = []
    
    for c in courts:
        bookings_count = db.query(DatSan).filter(
            DatSan.ma_san == c.ma,
            DatSan.trang_thai != 'da_huy'
        ).count()
        
        # Doanh thu sân này
        court_payments = db.query(ThanhToan).join(DatSan).filter(
            DatSan.ma_san == c.ma,
            ThanhToan.trang_thai == 'thanh_cong'
        ).all()
        court_revenue = sum(p.so_tien for p in court_payments)
        
        court_performance.append({
            "ma_san": c.ma,
            "ten_san": c.ten_san,
            "loai_san": c.loai_san.ten_loai,
            "so_luot_dat": bookings_count,
            "doanh_thu": court_revenue
        })
        
    return {
        "tong_san": tong_san,
        "san_hoat_dong": san_hoat_dong,
        "tong_dat_san": tong_dat_san,
        "tong_doanh_thu": tong_doanh_thu,
        "hieu_suat_san": court_performance
    }
