from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from app.database import get_db
from app.schemas.dat_san_schema import (
    DatSanCreate, DatSanResponse, XacNhanCocRequest, DoiLichRequest, LichSanResponse,
    QRPaymentInfo, SandboxQRPayRequest
)
from app.services.dat_san_service import DatSanService
from app.auth.dependencies import get_current_user, require_staff_or_admin
from app.models.tai_khoan import TaiKhoan
from app.models.dat_san import DatSan

router = APIRouter(prefix="/api/dat-san", tags=["Đặt sân"])

def to_booking_response(booking: DatSan) -> DatSanResponse:
    return DatSanResponse(
        ma_don=booking.ma_don,
        ma_khach_hang=booking.ma_khach_hang,
        ma_san=booking.ma_san,
        ngay_da=booking.ngay_da,
        gio_bat_dau=booking.gio_bat_dau,
        gio_ket_thuc=booking.gio_ket_thuc,
        tien_coc=booking.tien_coc,
        trang_thai=booking.trang_thai,
        lock_expires_at=booking.lock_expires_at,
        ghi_chu=booking.ghi_chu,
        ngay_tao=booking.ngay_tao,
        san=booking.san,
        khach_hang_ten=booking.khach_hang.ho_ten if booking.khach_hang else None
    )

@router.get("/schedule", response_model=LichSanResponse)
def get_schedule(
    ngay: date = Query(default_factory=date.today),
    san_id: str = Query(None),
    db: Session = Depends(get_db)
):
    return DatSanService.get_day_schedule(db, ngay, san_id)

@router.get("/bookings", response_model=List[DatSanResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    # Nếu là customer, chỉ xem của chính họ. Staff/Admin xem hết.
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER":
        bookings = db.query(DatSan).filter(DatSan.ma_khach_hang == current_user.tai_khoan_id).all()
    else:
        bookings = db.query(DatSan).all()
    return [to_booking_response(b) for b in bookings]

@router.post("/booking", response_model=DatSanResponse)
def create_booking(
    data: DatSanCreate,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    booking = DatSanService.create_booking(db, data, current_user.tai_khoan_id)
    return to_booking_response(booking)

@router.post("/booking/confirm-deposit", response_model=DatSanResponse)
def confirm_deposit(
    data: XacNhanCocRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    booking = DatSanService.xac_nhan_coc(db, data.ma_don, data.so_tien, data.phuong_thuc)
    return to_booking_response(booking)

@router.post("/booking/reschedule", response_model=DatSanResponse)
def reschedule(
    data: DoiLichRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    # Kiểm tra quyền: chỉ Admin, Staff hoặc chính khách hàng của đơn đặt
    booking = db.query(DatSan).filter(DatSan.ma_don == data.ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
        
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa đơn đặt sân của người khác")
        
    updated = DatSanService.doi_lich(db, data)
    return to_booking_response(updated)

@router.post("/booking/cancel", response_model=DatSanResponse)
def cancel_booking(
    ma_don: str = Query(...),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    # Kiểm tra quyền
    booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
        
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hủy đơn đặt sân của người khác")
        
    cancelled = DatSanService.huy_lich(db, ma_don)
    return to_booking_response(cancelled)

@router.get("/booking/{ma_don}/qr-deposit", response_model=QRPaymentInfo)
def get_deposit_qr(
    ma_don: str,
    phuong_thuc: str = Query('chuyen_khoan'),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem thông tin thanh toán của người khác")
    return DatSanService.generate_deposit_qr(db, ma_don, phuong_thuc)

@router.post("/booking/sandbox-qr-pay", response_model=DatSanResponse)
def sandbox_qr_pay(
    data: SandboxQRPayRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    booking = db.query(DatSan).filter(DatSan.ma_don == data.ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thanh toán cho đơn của người khác")
    updated = DatSanService.sandbox_qr_pay(db, data.ma_don, data.phuong_thuc)
    return to_booking_response(updated)

