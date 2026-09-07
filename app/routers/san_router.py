from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.san_schema import SanCreate, SanUpdate, SanResponse, BangGiaCreate, BangGiaResponse, BaoTriCreate
from app.services.san_service import SanService
from app.auth.dependencies import require_admin, require_staff_or_admin
from app.models.tai_khoan import TaiKhoan

router = APIRouter(prefix="/api/san", tags=["San bãi"])

@router.get("", response_model=List[SanResponse])
def get_courts(db: Session = Depends(get_db)):
    return SanService.get_all_courts(db)

@router.post("", response_model=SanResponse)
def create_court(
    data: SanCreate, 
    db: Session = Depends(get_db), 
    current_user: TaiKhoan = Depends(require_admin)
):
    return SanService.create_court(db, data)

@router.post("/pricing", response_model=BangGiaResponse)
def add_pricing(
    data: BangGiaCreate, 
    db: Session = Depends(get_db), 
    current_user: TaiKhoan = Depends(require_admin)
):
    return SanService.add_pricing(db, data)

@router.post("/maintenance")
def create_maintenance(
    data: BaoTriCreate, 
    db: Session = Depends(get_db), 
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    SanService.create_maintenance(db, data)
    return {"message": "Tạo lịch bảo trì thành công, khung giờ này đã được khóa tự động"}

@router.put("/{ma}", response_model=SanResponse)
def update_court(
    ma: str,
    data: SanUpdate,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_admin)
):
    return SanService.update_court(db, ma, data)

@router.delete("/{ma}")
def delete_court(
    ma: str,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_admin)
):
    return SanService.delete_court(db, ma)
