from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CheckInRequest(BaseModel):
    ma_don: str
    ghi_chu: Optional[str] = None

class CheckOutRequest(BaseModel):
    ma_don: str

class HoaDonResponse(BaseModel):
    ma_hoa_don: str
    ma_don: str
    check_in_thuc_te: Optional[datetime] = None
    check_out_thuc_te: Optional[datetime] = None
    tien_san: int
    tong_dich_vu: int
    tien_coc_da_tru: int
    tong_thanh_toan: int
    ngay_tao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ThanhToanResponse(BaseModel):
    thanh_toan_id: int
    ma_don: str
    so_tien: int
    phuong_thuc: str
    loai_giao_dich: str
    trang_thai: str
    thoi_gian: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
