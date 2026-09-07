import enum

class VaiTroEnum(str, enum.Enum):
    ADMIN = 'ADMIN'
    STAFF = 'STAFF'
    CUSTOMER = 'CUSTOMER'

class TrangThaiSan(str, enum.Enum):
    ACTIVE = 'active'
    MAINTENANCE = 'maintenance'
    INACTIVE = 'inactive'

class TrangThaiDatSan(str, enum.Enum):
    CHO_COC = 'cho_coc'           # Đang giữ chỗ (lock 10 phút)
    DA_XAC_NHAN = 'da_xac_nhan'   # Đã đặt cọc thành công
    DANG_DA = 'dang_da'           # Đã check-in, đang thi đấu
    HOAN_TAT = 'hoan_tat'         # Đã check-out, thanh toán xong
    DA_HUY = 'da_huy'             # Đã hủy

class PhuongThucThanhToan(str, enum.Enum):
    TIEN_MAT = 'tien_mat'
    CHUYEN_KHOAN = 'chuyen_khoan'
    VNPAY = 'vnpay'
    MOMO = 'momo'

class LoaiGiaoDich(str, enum.Enum):
    DAT_COC = 'dat_coc'
    THANH_TOAN_HET = 'thanh_toan_het'
    HOAN_COC = 'hoan_coc'

class TrangThaiThanhToan(str, enum.Enum):
    CHO_XU_LY = 'cho_xu_ly'
    THANH_CONG = 'thanh_cong'
    THAT_BAI = 'that_bai'

class KieuGoiAI(str, enum.Enum):
    CONSULT = 'CONSULT'
    NOTIFY = 'NOTIFY'
    REPORT = 'REPORT'

class TrangThaiAI(str, enum.Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'

class KenhGui(str, enum.Enum):
    WEB = 'web'
    ZALO = 'zalo'
    SMS = 'sms'

class TrangThaiGui(str, enum.Enum):
    CHO_GUI = 'cho_gui'
    DA_GUI = 'da_gui'
    LOI = 'loi'

class DanhMucDV(str, enum.Enum):
    NUOC_UONG = 'NUOC_UONG'
    TRANG_BI = 'TRANG_BI'
    KHAC = 'KHAC'

class LoaiNgay(str, enum.Enum):
    THUONG = 'thuong'
    CUOI_TUAN = 'cuoi_tuan'
    LE = 'le'
