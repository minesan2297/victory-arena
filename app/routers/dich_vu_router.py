from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.dich_vu_schema import DichVuCreate, DichVuResponse
from app.services.dich_vu_service import DichVuService
from app.auth.dependencies import require_admin
from app.models.tai_khoan import TaiKhoan

router = APIRouter(prefix="/api/dich-vu", tags=["Dịch vụ phát sinh"])

@router.get("", response_model=List[DichVuResponse])
def get_services(db: Session = Depends(get_db)):
    return DichVuService.get_all_services(db)

@router.post("", response_model=DichVuResponse)
def create_service(
    data: DichVuCreate,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_admin)
):
    return DichVuService.create_service(db, data)

@router.delete("/{service_id}", response_model=DichVuResponse)
def deactivate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_admin)
):
    return DichVuService.deactivate_service(db, service_id)
