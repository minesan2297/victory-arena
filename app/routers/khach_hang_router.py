from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.dependencies import get_current_user, require_staff_or_admin
from app.schemas.auth_schema import UserResponse
from app.models.tai_khoan import TaiKhoan, VaiTro
from app.models.enums import VaiTroEnum

router = APIRouter(prefix="/api/khach-hang", tags=["Hồ sơ khách hàng"])

@router.get("/search", response_model=List[UserResponse])
def search_customers(
    q: str = Query(..., min_length=1, description="Tìm kiếm theo Tên hoặc Số điện thoại"),
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    # Tìm vai trò customer để lọc
    customer_role = db.query(VaiTro).filter(VaiTro.ten_vai_tro == VaiTroEnum.CUSTOMER.value.upper()).first()
    role_id = customer_role.vai_tro_id if customer_role else None
    
    query = db.query(TaiKhoan)
    if role_id:
        query = query.filter(TaiKhoan.vai_tro_id == role_id)
        
    results = query.filter(
        (TaiKhoan.ho_ten.like(f"%{q}%")) | 
        (TaiKhoan.so_dien_thoai.like(f"%{q}%"))
    ).all()
    
    return [
        UserResponse(
            tai_khoan_id=u.tai_khoan_id,
            ten_dang_nhap=u.ten_dang_nhap,
            ho_ten=u.ho_ten,
            so_dien_thoai=u.so_dien_thoai,
            email=u.email,
            vai_tro=u.vai_tro.ten_vai_tro,
            diem_uy_tin=u.diem_uy_tin,
            trang_thai=u.trang_thai
        ) for u in results
    ]
