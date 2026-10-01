"""Model Thông báo hệ thống gửi tới người dùng."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ThongBao(Base):
    __tablename__ = 'ThongBao'
    __table_args__ = (
        Index('ix_thongbao_tk', 'tai_khoan_id'),
    )
    
    thong_bao_id = Column(Integer, primary_key=True, autoincrement=True)
    tai_khoan_id = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=False)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=True)
    noi_dung = Column(Text, nullable=False)
    kenh_gui = Column(String(20), default='web')  # web, zalo, sms
    trang_thai_gui = Column(String(20), default='da_gui')  # cho_gui, da_gui, loi
    da_doc = Column(Boolean, default=False)
    ngay_gui = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tai_khoan = relationship("TaiKhoan", back_populates="thong_baos")
    dat_san = relationship("DatSan", back_populates="thong_baos")
