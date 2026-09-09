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

class QRPaymentInfo(BaseModel):
    ma_don: str
    so_tien: int
    noi_dung: str
    ngan_hang: str = "MBBank"
    so_tai_khoan: str = "0988123456"
    chu_tai_khoan: str = "SAN BONG VICTORY ARENA"
    vietqr_url: str
    momo_qr_url: str
    vnpay_qr_url: str
    phuong_thuc: str = "chuyen_khoan"
    loai_thanh_toan: str = "dat_coc"
    lock_expires_at: Optional[datetime] = None
    con_lai_giay: Optional[int] = None

class SandboxQRPayRequest(BaseModel):
    ma_don: str
    phuong_thuc: str = "chuyen_khoan"

class DichVuItemDetail(BaseModel):
    su_dung_id: int
    dich_vu_id: int
    ten_dich_vu: str
    don_vi_tinh: str
    danh_muc: str
    don_gia: int
    so_luong: int
    thanh_tien: int

    model_config = ConfigDict(from_attributes=True)

class DatSanDetailResponse(BaseModel):
    ma_don: str
    ma_khach_hang: int
    khach_hang_ten: str
    khach_hang_sdt: Optional[str] = None
    ma_san: str
    ten_san: str
    loai_san: str
    vi_tri: Optional[str] = None
    ngay_da: date
    gio_bat_dau: time
    gio_ket_thuc: time
    tien_coc: int
    trang_thai: str
    lock_expires_at: Optional[datetime] = None
    ghi_chu: Optional[str] = None
    ngay_tao: datetime
    # Thông tin tài chính & hóa đơn
    tien_san: int = 0
    tong_dich_vu: int = 0
    tien_coc_da_tru: int = 0
    tong_thanh_toan: int = 0
    check_in_thuc_te: Optional[datetime] = None
    check_out_thuc_te: Optional[datetime] = None
    # Danh sách dịch vụ đi kèm
    dich_vus: List[DichVuItemDetail] = []
    # Phương thức thanh toán cọc nếu có
    phuong_thuc_coc: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


