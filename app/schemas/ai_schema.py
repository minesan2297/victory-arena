from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional, List

class AIConsultRequest(BaseModel):
    user_prompt: str = Field(..., min_length=3)
    ngay_mong_muon: Optional[date] = None

class RecommendedSlot(BaseModel):
    san_id: str
    ten_san: str
    loai_san: str
    khung_gio: str
    don_gia: float
    ly_do: str

class AIConsultResponse(BaseModel):
    assistant_message: str
    co_san_phu_hop: bool
    recommended_slots: List[RecommendedSlot]
    analyzed_intent: Optional[dict] = None

class AIReminderRequest(BaseModel):
    ma_don: str

class AIReminderResponse(BaseModel):
    ma_don: str
    noi_dung_tin_nhan: str
    kenh: str = 'web'
    da_luu: bool = False

class AIReportRequest(BaseModel):
    tu_ngay: date
    den_ngay: date

class AIReportResponse(BaseModel):
    bao_cao_id: Optional[int] = None
    tom_tat: str
    ty_le_lap_day: float
    khung_gio_cao_diem: List[str]
    de_xuat: List[str]
