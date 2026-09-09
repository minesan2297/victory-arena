from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import datetime
import random
import urllib.parse
from app.models.dat_san import DatSan
from app.models.hoa_don import HoaDon, CheckIn, ThanhToan
from app.models.dich_vu import SuDungDichVu, DanhMucDichVu
from app.models.ai_models import ThongBao
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
                
        # Khắc phục lỗ hổng kinh tế: Chỉ trừ tiền cọc thực tế đã thanh toán thành công
        tong_coc_thuc_te = db.query(func.sum(ThanhToan.so_tien)).filter(
            ThanhToan.ma_don == ma_don,
            ThanhToan.loai_giao_dich == 'dat_coc',
            ThanhToan.trang_thai == 'thanh_cong'
        ).scalar() or 0
        tien_coc_da_tru = int(tong_coc_thuc_te)
        
        # Tạo HoaDon
        new_invoice = HoaDon(
            ma_hoa_don=ma_hoa_don,
            ma_don=ma_don,
            check_in_thuc_te=datetime.utcnow(),
            tien_san=tien_san,
            tong_dich_vu=0,
            tien_coc_da_tru=tien_coc_da_tru,
            tong_thanh_toan=max(0, tien_san - tien_coc_da_tru),
            trang_thai='chua_thanh_toan',
            ngay_tao=datetime.utcnow()
        )
        db.add(new_invoice)
        
        # Tạo thông báo check-in cho khách hàng
        notif_ci = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=ma_don,
            noi_dung=f"🏟️ [CHECK-IN NHẬN SÂN] Đội bóng đã check-in nhận sân {booking.ma_san} thành công. Chúc quý khách có một trận đấu cuồng nhiệt!",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            da_doc=False,
            ngay_gui=datetime.utcnow()
        )
        db.add(notif_ci)
        
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
            
        # Tạo thông báo hoàn tất thanh toán hóa đơn
        notif_co = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=ma_don,
            noi_dung=f"🏁 [QUYẾT TOÁN TRẢ SÂN] Trận đấu {ma_don} đã hoàn tất. Hóa đơn {invoice.ma_hoa_don}: Tổng thanh toán {invoice.tong_thanh_toan:,.0f} ₫ qua {phuong_thuc}. Cảm ơn quý khách đã thi đấu tại Victory Arena!",
            kenh_gui='web',
            trang_thai_gui='da_gui',
            da_doc=False,
            ngay_gui=datetime.utcnow()
        )
        db.add(notif_co)
            
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def generate_checkout_qr(db: Session, ma_don: str, phuong_thuc: str = 'chuyen_khoan') -> dict:
        invoice = db.query(HoaDon).filter(HoaDon.ma_don == ma_don).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hóa đơn của đơn đặt sân")
            
        amount = int(invoice.tong_thanh_toan)
        memo = f"HD {invoice.ma_hoa_don}"
        account_no = "0988123456"
        bank_id = "MB"
        account_name = "SAN BONG VICTORY ARENA"
        
        enc_memo = urllib.parse.quote(memo)
        enc_name = urllib.parse.quote(account_name)
        vietqr_url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.png?amount={amount}&addInfo={enc_memo}&accountName={enc_name}"
        
        momo_data = f"2|99|{account_no}|{account_name}|sanbongvictory@gmail.com|0|0|{amount}|{memo}|transfer_myqr"
        momo_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(momo_data)}"
        
        vnpay_data = f"VNPAYQR://pay?merchant=VICTORYARENA&amount={amount}&orderId={invoice.ma_hoa_don}&desc={memo}"
        vnpay_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(vnpay_data)}"
        
        return {
            "ma_hoa_don": invoice.ma_hoa_don,
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
            "loai_thanh_toan": "thanh_toan_het"
        }

