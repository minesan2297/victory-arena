from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from app.database import get_db
from app.schemas.dat_san_schema import (
    DatSanCreate, DatSanResponse, DatSanDetailResponse, DichVuItemDetail,
    XacNhanCocRequest, DoiLichRequest, LichSanResponse,
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

@router.get("/booking/{ma_don}/detail", response_model=DatSanDetailResponse)
def get_booking_detail(
    ma_don: str,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(get_current_user)
):
    booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    if current_user.vai_tro.ten_vai_tro == "CUSTOMER" and booking.ma_khach_hang != current_user.tai_khoan_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem thông tin đơn này")
    
    # Lấy thông tin hóa đơn nếu có
    tien_san = 0
    tong_dich_vu = 0
    tien_coc_da_tru = booking.tien_coc
    tong_thanh_toan = 0
    check_in_thuc_te = None
    check_out_thuc_te = None
    
    if booking.hoa_don:
        tien_san = booking.hoa_don.tien_san
        tong_dich_vu = booking.hoa_don.tong_dich_vu
        tien_coc_da_tru = booking.hoa_don.tien_coc_da_tru
        tong_thanh_toan = booking.hoa_don.tong_thanh_toan
        check_in_thuc_te = booking.hoa_don.check_in_thuc_te
        check_out_thuc_te = booking.hoa_don.check_out_thuc_te
    else:
        tien_san = DatSanService.calculate_price(db, booking.ma_san, booking.ngay_da, booking.gio_bat_dau, booking.gio_ket_thuc)
        tong_thanh_toan = max(0, tien_san - booking.tien_coc)
        
    # Lấy danh sách dịch vụ
    dich_vus = []
    for s in booking.su_dung_dich_vus:
        dich_vus.append(DichVuItemDetail(
            su_dung_id=s.su_dung_id,
            dich_vu_id=s.dich_vu_id,
            ten_dich_vu=s.dich_vu.ten_dich_vu if s.dich_vu else "Dịch vụ",
            don_vi_tinh=s.dich_vu.don_vi_tinh if s.dich_vu else "Phần",
            danh_muc=s.dich_vu.danh_muc if s.dich_vu else "KHAC",
            don_gia=s.don_gia_tai_ban,
            so_luong=s.so_luong,
            thanh_tien=s.thanh_tien
        ))
        
    # Lấy phương thức cọc
    phuong_thuc_coc = None
    deposit_pay = [p for p in booking.thanh_toans if p.loai_giao_dich == 'dat_coc' and p.trang_thai == 'thanh_cong']
    if deposit_pay:
        phuong_thuc_coc = deposit_pay[0].phuong_thuc
        
    return DatSanDetailResponse(
        ma_don=booking.ma_don,
        ma_khach_hang=booking.ma_khach_hang,
        khach_hang_ten=booking.khach_hang.ho_ten if booking.khach_hang else "Khách vãng lai",
        khach_hang_sdt=booking.khach_hang.so_dien_thoai if booking.khach_hang else None,
        ma_san=booking.ma_san,
        ten_san=booking.san.ten_san if booking.san else booking.ma_san,
        loai_san=booking.san.loai_san.ten_loai if (booking.san and booking.san.loai_san) else "Sân bóng",
        vi_tri=booking.san.vi_tri if booking.san else None,
        ngay_da=booking.ngay_da,
        gio_bat_dau=booking.gio_bat_dau,
        gio_ket_thuc=booking.gio_ket_thuc,
        tien_coc=booking.tien_coc,
        trang_thai=booking.trang_thai,
        lock_expires_at=booking.lock_expires_at,
        ghi_chu=booking.ghi_chu,
        ngay_tao=booking.ngay_tao,
        tien_san=tien_san,
        tong_dich_vu=tong_dich_vu,
        tien_coc_da_tru=tien_coc_da_tru,
        tong_thanh_toan=tong_thanh_toan,
        check_in_thuc_te=check_in_thuc_te,
        check_out_thuc_te=check_out_thuc_te,
        dich_vus=dich_vus,
        phuong_thuc_coc=phuong_thuc_coc
    )


