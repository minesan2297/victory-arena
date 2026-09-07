from pydantic import BaseModel, ConfigDict, Field
from datetime import date, time, datetime
from typing import Optional, List
from .san_schema import SanResponse

class DatSanCreate(BaseModel):
    ma_san: str
    ngay_da: date
    gio_bat_dau: time
    gio_ket_thuc: time
    tien_coc: int = 0
    ghi_chu: Optional[str] = None
    phuong_thuc_thanh_toan: str = 'tien_mat'

class DatSanResponse(BaseModel):
    ma_don: str
    ma_khach_hang: int
    ma_san: str
    ngay_da: date
    gio_bat_dau: time
    gio_ket_thuc: time
    tien_coc: int
    trang_thai: str
    lock_expires_at: Optional[datetime] = None
    ghi_chu: Optional[str] = None
    ngay_tao: datetime
    san: Optional[SanResponse] = None
    khach_hang_ten: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class XacNhanCocRequest(BaseModel):
    ma_don: str
    so_tien: int = Field(..., gt=0)
    phuong_thuc: str = 'tien_mat'

class DoiLichRequest(BaseModel):
    ma_don: str
    ngay_da_moi: Optional[date] = None
    gio_bat_dau_moi: Optional[time] = None
    gio_ket_thuc_moi: Optional[time] = None
    ma_san_moi: Optional[str] = None

class SlotInfo(BaseModel):
    san_id: str
    ten_san: str
    loai_san: str
    gio_bat_dau: time
    gio_ket_thuc: time
    don_gia: int
    trang_thai: str
    ma_don: Optional[str] = None
    ten_khach: Optional[str] = None

class LichSanResponse(BaseModel):
    ngay: date
    tong_san: int
    slots: List[SlotInfo]
