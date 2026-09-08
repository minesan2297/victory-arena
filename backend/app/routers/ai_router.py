from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ai_schema import (
    AIConsultRequest, AIConsultResponse, AIReminderRequest, AIReminderResponse,
    AIReportRequest, AIReportResponse
)
from app.services.ai_service import AIService
from app.auth.dependencies import get_current_user, require_admin, require_staff_or_admin
from app.models.tai_khoan import TaiKhoan

router = APIRouter(prefix="/api/ai", tags=["AI Copilot"])

@router.post("/consult", response_model=AIConsultResponse)
def consult_pitch(data: AIConsultRequest, db: Session = Depends(get_db)):
    return AIService.consult_pitch(db, data.user_prompt, data.ngay_mong_muon)

@router.post("/reminder", response_model=AIReminderResponse)
def send_reminder(
    data: AIReminderRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_staff_or_admin)
):
    return AIService.generate_reminder(db, data.ma_don)

@router.post("/report", response_model=AIReportResponse)
def generate_report(
    data: AIReportRequest,
    db: Session = Depends(get_db),
    current_user: TaiKhoan = Depends(require_admin)
):
    return AIService.analyze_revenue(db, data.tu_ngay, data.den_ngay, current_user.tai_khoan_id)
