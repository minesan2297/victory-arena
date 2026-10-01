"""Model Báo cáo doanh thu & tỷ lệ lấp đầy sân."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class BaoCao(Base):
    __tablename__ = 'BaoCao'
    __table_args__ = (
        CheckConstraint('den_ngay >= tu_ngay', name='ck_baocao_date_range'),
    )
    
    bao_cao_id = Column(Integer, primary_key=True, autoincrement=True)
    tu_ngay = Column(Date, nullable=False)
    den_ngay = Column(Date, nullable=False)
    tong_doanh_thu = Column(Integer, default=0)
    ty_le_lap_day = Column(Float, default=0.0)
    ket_qua_ai_tom_tat = Column(Text, nullable=True)
    nguoi_tao_id = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=False)
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    nguoi_tao_admin = relationship("TaiKhoan", back_populates="bao_caos")
