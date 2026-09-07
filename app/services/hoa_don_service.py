from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import random
from app.models.dat_san import DatSan
from app.models.hoa_don import HoaDon, CheckIn, ThanhToan
from app.models.dich_vu import SuDungDichVu, DanhMucDichVu
from app.services.dat_san_service import DatSanService

class HoaDonService:
    @staticmethod
    def check_in(db: Session, ma_don: str, nhan_vien_id: int, ghi_chu: str = None) -> HoaDon:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai != 'da_xac_nhan':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Đơn đặt sân phải ở trạng thái Đã xác nhận mới có thể Check-in"
            )
            
        # Cập nhật trạng thái đặt sân
        booking.trang_thai = 'dang_da'
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Tạo bản ghi CheckIn
        new_checkin = CheckIn(
            ma_don=ma_don,
            thoi_gian_checkin=datetime.utcnow(),
            nhan_vien_id=nhan_vien_id,
            ghi_chu=ghi_chu
        )
        db.add(new_checkin)
        
        # Tính tiền sân tạm tính
        tien_san = DatSanService.calculate_price(
            db, booking.ma_san, booking.ngay_da, booking.gio_bat_dau, booking.gio_ket_thuc
        )
        
        # Tạo mã hóa đơn duy nhất
        date_str = datetime.utcnow().strftime("%Y%m%d")
        while True:
            ma_hoa_don = f"HD{date_str}-{random.randint(1000, 9999)}"
            if not db.query(HoaDon).filter(HoaDon.ma_hoa_don == ma_hoa_don).first():
                break
                
        # Tạo HoaDon
        new_invoice = HoaDon(
            ma_hoa_don=ma_hoa_don,
            ma_don=ma_don,
            check_in_thuc_te=datetime.utcnow(),
            tien_san=tien_san,
            tong_dich_vu=0,
            tien_coc_da_tru=int(booking.tien_coc),
            tong_thanh_toan=max(0, tien_san - int(booking.tien_coc)),
            trang_thai='chua_thanh_toan',
            ngay_tao=datetime.utcnow()
        )
        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)
        return new_invoice

    @staticmethod
    def add_service_usage(db: Session, ma_don: str, dich_vu_id: int, so_luong: int) -> SuDungDichVu:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai != 'dang_da':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Chỉ có thể thêm dịch vụ khi đang thi đấu (trạng thái Đang đá)"
            )
            
        service = db.query(DanhMucDichVu).filter(DanhMucDichVu.dich_vu_id == dich_vu_id).first()
        if not service or service.trang_thai != 'active':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dịch vụ không tồn tại hoặc đã dừng kinh doanh")
            
        # Kiểm tra xem đã sử dụng dịch vụ này chưa
        usage = db.query(SuDungDichVu).filter(
            SuDungDichVu.ma_don == ma_don,
            SuDungDichVu.dich_vu_id == dich_vu_id
        ).first()
        
        if usage:
            usage.so_luong += so_luong
            usage.thanh_tien = usage.so_luong * usage.don_gia_tai_ban
        else:
            usage = SuDungDichVu(
                ma_don=ma_don,
                dich_vu_id=dich_vu_id,
                so_luong=so_luong,
                don_gia_tai_ban=service.don_gia,
                thanh_tien=so_luong * service.don_gia
            )
            db.add(usage)
            
        db.commit()
        db.refresh(usage)
        
        # Cập nhật tổng dịch vụ trong hóa đơn
        invoice = db.query(HoaDon).filter(HoaDon.ma_don == ma_don).first()
        if invoice:
            # Tính lại tổng dịch vụ
            usages = db.query(SuDungDichVu).filter(SuDungDichVu.ma_don == ma_don).all()
            invoice.tong_dich_vu = sum(u.thanh_tien for u in usages)
            invoice.tong_thanh_toan = max(0.0, invoice.tien_san + invoice.tong_dich_vu - invoice.tien_coc_da_tru)
            db.commit()
            
        return usage

    @staticmethod
    def get_service_usages(db: Session, ma_don: str):
        # Lấy các chi tiết kèm tên dịch vụ
        usages = db.query(SuDungDichVu).filter(SuDungDichVu.ma_don == ma_don).all()
        for u in usages:
            u.ten_dich_vu = u.dich_vu.ten_dich_vu
        return usages

    @staticmethod
    def check_out_and_pay(db: Session, ma_don: str, phuong_thuc: str) -> HoaDon:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn đặt sân không tồn tại")
            
        if booking.trang_thai != 'dang_da':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Đơn đặt sân phải ở trạng thái Đang đá mới có thể Check-out"
            )
            
        invoice = db.query(HoaDon).filter(HoaDon.ma_don == ma_don).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hóa đơn tạm tính")
            
        # Cập nhật hóa đơn chính thức
        invoice.check_out_thuc_te = datetime.utcnow()
        
        # Tính toán lại tổng lần cuối
        usages = db.query(SuDungDichVu).filter(SuDungDichVu.ma_don == ma_don).all()
        invoice.tong_dich_vu = int(sum(u.thanh_tien for u in usages))
        invoice.tong_thanh_toan = max(0, int(invoice.tien_san + invoice.tong_dich_vu - invoice.tien_coc_da_tru))
        invoice.trang_thai = 'da_thanh_toan'
        
        # Cập nhật đơn đặt sân
        booking.trang_thai = 'hoan_tat'
        booking.ngay_cap_nhat = datetime.utcnow()
        
        # Thêm ThanhToan toàn bộ
        if invoice.tong_thanh_toan > 0:
            payment = ThanhToan(
                ma_don=ma_don,
                so_tien=invoice.tong_thanh_toan,
                phuong_thuc=phuong_thuc,
                loai_giao_dich='thanh_toan_het',
                trang_thai='thanh_cong',
                thoi_gian=datetime.utcnow()
            )
            db.add(payment)
            
        db.commit()
        db.refresh(invoice)
        return invoice
