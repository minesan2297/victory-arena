from pydantic import BaseModel, ConfigDict, Field
from datetime import date, time, datetime
from typing import Optional

class LoaiSanResponse(BaseModel):
    loai_san_id: int
    ten_loai: str
    so_nguoi_tieu_chuan: int
    mo_ta: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SanCreate(BaseModel):
    ma: str
    ten_san: str
    loai_san_id: int
    vi_tri: Optional[str] = None
    mo_ta_ai: Optional[str] = None

class SanUpdate(BaseModel):
    ten_san: Optional[str] = None
    loai_san_id: Optional[int] = None
    vi_tri: Optional[str] = None
    trang_thai: Optional[str] = None
    mo_ta_ai: Optional[str] = None

class SanResponse(BaseModel):
    ma: str
    ten_san: str
    loai_san_id: int
    loai_san: Optional[LoaiSanResponse] = None
    vi_tri: Optional[str] = None
    trang_thai: str
    mo_ta_ai: Optional[str] = None
    ngay_tao: datetime

    model_config = ConfigDict(from_attributes=True)

class BangGiaCreate(BaseModel):
    san_id: str
    gio_bat_dau: time
    gio_ket_thuc: time
    don_gia: int = Field(..., gt=0)
    loai_ngay: str = 'thuong'

class BangGiaResponse(BaseModel):
    bang_gia_id: int
    san_id: str
    gio_bat_dau: time
    gio_ket_thuc: time
    don_gia: int
    loai_ngay: str

    model_config = ConfigDict(from_attributes=True)

class BaoTriCreate(BaseModel):
    san_id: str
    ngay_bao_tri: date
    gio_bat_dau: time
    gio_ket_thuc: time
    ly_do: str
