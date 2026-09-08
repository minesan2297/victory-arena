from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.dich_vu import DanhMucDichVu
from app.schemas.dich_vu_schema import DichVuCreate

class DichVuService:
    @staticmethod
    def get_all_services(db: Session):
        return db.query(DanhMucDichVu).all()

    @staticmethod
    def create_service(db: Session, data: DichVuCreate) -> DanhMucDichVu:
        # Kiểm tra trùng tên dịch vụ
        if db.query(DanhMucDichVu).filter(DanhMucDichVu.ten_dich_vu == data.ten_dich_vu).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dịch vụ này đã tồn tại"
            )
            
        new_service = DanhMucDichVu(
            ten_dich_vu=data.ten_dich_vu,
            don_vi_tinh=data.don_vi_tinh,
            don_gia=data.don_gia,
            danh_muc=data.danh_muc,
            trang_thai='active'
        )
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service

    @staticmethod
    def deactivate_service(db: Session, service_id: int) -> DanhMucDichVu:
        service = db.query(DanhMucDichVu).filter(DanhMucDichVu.dich_vu_id == service_id).first()
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy dịch vụ")
            
        service.trang_thai = 'inactive'
        db.commit()
        db.refresh(service)
        return service
