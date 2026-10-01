"""Model cấu hình và nhật ký tương tác AI (Gemini)."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Re-export BaoCao và ThongBao để tương thích ngược 100% với các import cũ
from app.models.bao_cao import BaoCao
from app.models.thong_bao import ThongBao


class AIConfig(Base):
    __tablename__ = 'AIConfig'
    
    ai_config_id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    api_key_encrypted = Column(String(500), nullable=True)
    prompt_template = Column(Text, nullable=True)
    trang_thai = Column(String(20), default='active')
    
    # Relationships
    ai_requests = relationship("AIRequest", back_populates="ai_config", cascade="save-update, merge")


class AIRequest(Base):
    __tablename__ = 'AIRequest'
    
    ai_request_id = Column(Integer, primary_key=True, autoincrement=True)
    ai_config_id = Column(Integer, ForeignKey('AIConfig.ai_config_id'), nullable=True)
    tai_khoan_id = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=True)
    kieu_goi = Column(String(30), nullable=False)  # CONSULT, NOTIFY, REPORT
    prompt_input = Column(Text, nullable=False)
    ket_qua = Column(Text, nullable=True)
    thoi_gian_xu_ly_ms = Column(Integer, nullable=True)
    trang_thai = Column(String(20), default='success')  # success, error, timeout
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    ai_config = relationship("AIConfig", back_populates="ai_requests")
    nguoi_yeu_cau = relationship("TaiKhoan")


__all__ = ['AIConfig', 'AIRequest', 'BaoCao', 'ThongBao']
