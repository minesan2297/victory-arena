from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class DichVuCreate(BaseModel):
    ten_dich_vu: str
    don_vi_tinh: str
    don_gia: int = Field(..., ge=0)
    danh_muc: str = 'NUOC_UONG'

class DichVuResponse(BaseModel):
    dich_vu_id: int
    ten_dich_vu: str
    don_vi_tinh: str
    don_gia: int
    danh_muc: str
    trang_thai: str

    model_config = ConfigDict(from_attributes=True)

class SuDungDVCreate(BaseModel):
    ma_don: str
    dich_vu_id: int
    so_luong: int = 1

class SuDungDVResponse(BaseModel):
    su_dung_id: int
    ma_don: str
    dich_vu_id: int
    so_luong: int
    don_gia_tai_ban: int
    thanh_tien: int
    ten_dich_vu: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
