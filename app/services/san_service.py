from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from app.models.san import San, LoaiSan, BangGia
from app.models.dat_san import LichDat
from app.schemas.san_schema import SanCreate, SanUpdate, BangGiaCreate, BaoTriCreate

class SanService:
    @staticmethod
    def get_all_courts(db: Session):
        return db.query(San).all()
        
    @staticmethod
    def create_court(db: Session, data: SanCreate) -> San:
        # Kiểm tra mã sân trùng
        if db.query(San).filter(San.ma == data.ma).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã sân đã tồn tại"
            )
            
        # Kiểm tra loại sân tồn tại
        loai_san = db.query(LoaiSan).filter(LoaiSan.loai_san_id == data.loai_san_id).first()
        if not loai_san:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loại sân không tồn tại"
            )
            
        new_court = San(
            ma=data.ma,
            ten_san=data.ten_san,
            loai_san_id=data.loai_san_id,
            vi_tri=data.vi_tri,
            mo_ta_ai=data.mo_ta_ai,
            trang_thai='active',
            ngay_tao=datetime.utcnow()
        )
        db.add(new_court)
        db.commit()
        db.refresh(new_court)
        return new_court
        
    @staticmethod
    def add_pricing(db: Session, data: BangGiaCreate) -> BangGia:
        # Kiểm tra sân tồn tại
        court = db.query(San).filter(San.ma == data.san_id).first()
        if not court:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sân không tồn tại"
            )
            
        # Kiểm tra giờ bắt đầu < giờ kết thúc
        if data.gio_bat_dau >= data.gio_ket_thuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giờ bắt đầu phải nhỏ hơn giờ kết thúc"
            )
            
        new_pricing = BangGia(
            san_id=data.san_id,
            gio_bat_dau=data.gio_bat_dau,
            gio_ket_thuc=data.gio_ket_thuc,
            don_gia=data.don_gia,
            loai_ngay=data.loai_ngay
        )
        db.add(new_pricing)
        db.commit()
        db.refresh(new_pricing)
        return new_pricing
        
    @staticmethod
    def create_maintenance(db: Session, data: BaoTriCreate) -> LichDat:
        # Kiểm tra sân tồn tại
        court = db.query(San).filter(San.ma == data.san_id).first()
        if not court:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sân không tồn tại"
            )
            
        if data.gio_bat_dau >= data.gio_ket_thuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giờ bắt đầu phải nhỏ hơn giờ kết thúc"
            )
            
        # Tạo thời điểm bắt đầu và kết thúc
        bat_dau = datetime.combine(data.ngay_bao_tri, data.gio_bat_dau)
        ket_thuc = datetime.combine(data.ngay_bao_tri, data.gio_ket_thuc)
        
        # Thêm lịch bảo trì vào LichDat
        new_maint = LichDat(
            san_id=data.san_id,
            ma_don=None,
            bat_dau=bat_dau,
            ket_thuc=ket_thuc,
            loai_lich='bao_tri',
            ghi_chu=data.ly_do
        )
        db.add(new_maint)
        
        # Cập nhật trạng thái sân thành bảo trì tạm thời
        court.trang_thai = 'maintenance'
        
        db.commit()
        db.refresh(new_maint)
        return new_maint

    @staticmethod
    def update_court(db: Session, ma: str, data: SanUpdate) -> San:
        court = db.query(San).filter(San.ma == ma).first()
        if not court:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sân bóng có mã '{ma}'"
            )
            
        if data.loai_san_id is not None:
            loai_san = db.query(LoaiSan).filter(LoaiSan.loai_san_id == data.loai_san_id).first()
            if not loai_san:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Loại sân không tồn tại"
                )
            court.loai_san_id = data.loai_san_id
            
        if data.ten_san is not None:
            court.ten_san = data.ten_san
            
        if data.vi_tri is not None:
            court.vi_tri = data.vi_tri
            
        if data.mo_ta_ai is not None:
            court.mo_ta_ai = data.mo_ta_ai
            
        if data.trang_thai is not None:
            if data.trang_thai not in ['active', 'maintenance', 'inactive']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Trạng thái sân không hợp lệ (chỉ chấp nhận: active, maintenance, inactive)"
                )
            court.trang_thai = data.trang_thai
            
        try:
            db.commit()
            db.refresh(court)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Lỗi cập nhật dữ liệu sân bóng")
            
        return court

    @staticmethod
    def delete_court(db: Session, ma: str) -> dict:
        court = db.query(San).filter(San.ma == ma).first()
        if not court:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sân bóng có mã '{ma}'"
            )
            
        from app.models.dat_san import DatSan
        has_bookings = db.query(DatSan).filter(DatSan.ma_san == ma).first()
        
        # Nếu sân đã có lịch sử đơn đặt -> Áp dụng Soft Delete để bảo vệ tính toàn vẹn dữ liệu
        if has_bookings:
            court.trang_thai = 'inactive'
            db.commit()
            return {
                "message": f"Sân '{court.ten_san}' ({ma}) đã có lịch sử đơn đặt sân nên được chuyển sang trạng thái ngưng hoạt động (inactive) để bảo toàn dữ liệu lịch sử.",
                "action": "soft_delete",
                "ma": ma
            }
        else:
            # Sân chưa có đơn đặt -> Cho phép xóa hoàn toàn khỏi CSDL
            db.query(BangGia).filter(BangGia.san_id == ma).delete()
            db.delete(court)
            db.commit()
            return {
                "message": f"Đã xóa hoàn toàn sân '{court.ten_san}' ({ma}) khỏi hệ thống.",
                "action": "hard_delete",
                "ma": ma
            }
