from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.hoa_don_schema import CheckInRequest, CheckOutRequest, HoaDonResponse
from app.schemas.dich_vu_schema import SuDungDVCreate, SuDungDVResponse
from app.services.hoa_don_service import HoaDonService
from app.auth.dependencies import require_staff_or_admin, get_current_user
from app.models.tai_khoan import TaiKhoan
from app.models.hoa_don import HoaDon
from app.models.dat_san import DatSan
from app.models.ai_models import ThongBao
from fastapi import HTTPException

router = APIRouter(prefix="/api/van-hanh", tags=["Vận hành sân"])

@router.post("/check-in", response_model=HoaDonResponse)
def check_in(
    data: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    return HoaDonService.check_in(db, data.ma_don, current_user.tai_khoan_id, data.ghi_chu)

@router.post("/add-service", response_model=SuDungDVResponse)
def add_service(
    data: SuDungDVCreate,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    usage = HoaDonService.add_service_usage(db, data.ma_don, data.dich_vu_id, data.so_luong)
    # Gán tên dịch vụ để trả về đúng schema
    usage.ten_dich_vu = usage.dich_vu.ten_dich_vu
    return usage

@router.get("/service-usage", response_model=List[SuDungDVResponse])
def get_service_usages(
    ma_don: str = Query(...),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    return HoaDonService.get_service_usages(db, ma_don)

@router.post("/check-out", response_model=HoaDonResponse)
def check_out(
    data: CheckOutRequest,
    phuong_thuc: str = Query('tien_mat'),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    return HoaDonService.check_out_and_pay(db, data.ma_don, phuong_thuc)

@router.get("/invoice/{ma_don}/qr-checkout")
def get_checkout_qr(
    ma_don: str,
    phuong_thuc: str = Query('chuyen_khoan'),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    return HoaDonService.generate_checkout_qr(db, ma_don, phuong_thuc)

@router.get("/invoice/{ma_don}", response_model=HoaDonResponse)
def get_invoice_by_booking(
    ma_don: str,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem hóa đơn của người khác")
        
    invoice = db.query(HoaDon).filter(HoaDon.ma_don == ma_don).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Đơn đặt sân này chưa có hóa đơn")
    return invoice

@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    # Lấy 25 thông báo mới nhất cho tài khoản
    notifications = db.query(ThongBao).filter(
        (ThongBao.tai_khoan_id == current_user.tai_khoan_id) | (ThongBao.tai_khoan_id == None)
    ).order_by(ThongBao.ngay_gui.desc()).limit(25).all()
    
    return [
        {
            "thong_bao_id": n.thong_bao_id,
            "ma_don": n.ma_don,
            "noi_dung": n.noi_dung,
            "kenh_gui": n.kenh_gui,
            "trang_thai_gui": n.trang_thai_gui,
            "da_doc": bool(n.da_doc),
            "ngay_gui": n.ngay_gui.isoformat() if n.ngay_gui else None
        }
        for n in notifications
    ]

@router.post("/notifications/mark-read")
def mark_notifications_as_read(
    thong_bao_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    """Đánh dấu một hoặc toàn bộ thông báo của người dùng là đã đọc."""
    query = db.query(ThongBao).filter(ThongBao.tai_khoan_id == current_user.tai_khoan_id)
    if thong_bao_id is not None:
        query = query.filter(ThongBao.thong_bao_id == thong_bao_id)
    query.update({ThongBao.da_doc: True}, synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "Đã cập nhật trạng thái đã đọc"}

@router.post("/notifications/clear")
def clear_notifications(
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    db.query(ThongBao).filter(ThongBao.tai_khoan_id == current_user.tai_khoan_id).delete()
    db.commit()
    return {"status": "success"}

