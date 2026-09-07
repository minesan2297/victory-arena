from .auth_schema import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse
)
from .san_schema import (
    LoaiSanResponse,
    SanCreate,
    SanUpdate,
    SanResponse,
    BangGiaCreate,
    BangGiaResponse,
    BaoTriCreate
)
from .dat_san_schema import (
    DatSanCreate,
    DatSanResponse,
    XacNhanCocRequest,
    DoiLichRequest,
    SlotInfo,
    LichSanResponse
)
from .hoa_don_schema import (
    CheckInRequest,
    CheckOutRequest,
    HoaDonResponse,
    ThanhToanResponse
)
from .dich_vu_schema import (
    DichVuCreate,
    DichVuResponse,
    SuDungDVCreate,
    SuDungDVResponse
)
from .ai_schema import (
    AIConsultRequest,
    RecommendedSlot,
    AIConsultResponse,
    AIReminderRequest,
    AIReminderResponse,
    AIReportRequest,
    AIReportResponse
)

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "LoaiSanResponse",
    "SanCreate",
    "SanResponse",
    "BangGiaCreate",
    "BangGiaResponse",
    "BaoTriCreate",
    "DatSanCreate",
    "DatSanResponse",
    "XacNhanCocRequest",
    "DoiLichRequest",
    "SlotInfo",
    "LichSanResponse",
    "CheckInRequest",
    "CheckOutRequest",
    "HoaDonResponse",
    "ThanhToanResponse",
    "DichVuCreate",
    "DichVuResponse",
    "SuDungDVCreate",
    "SuDungDVResponse",
    "AIConsultRequest",
    "RecommendedSlot",
    "AIConsultResponse",
    "AIReminderRequest",
    "AIReminderResponse",
    "AIReportRequest",
    "AIReportResponse"
]
