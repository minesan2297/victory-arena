from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

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
    kieu_goi = Column(String(30), nullable=False) # CONSULT, NOTIFY, REPORT
    prompt_input = Column(Text, nullable=False)
    ket_qua = Column(Text, nullable=True)
    thoi_gian_xu_ly_ms = Column(Integer, nullable=True)
    trang_thai = Column(String(20), default='success') # success, error, timeout
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    ai_config = relationship("AIConfig", back_populates="ai_requests")
    nguoi_yeu_cau = relationship("TaiKhoan")

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

class ThongBao(Base):
    __tablename__ = 'ThongBao'
    __table_args__ = (
        Index('ix_thongbao_tk', 'tai_khoan_id'),
    )
    
    thong_bao_id = Column(Integer, primary_key=True, autoincrement=True)
    tai_khoan_id = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=False)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=True)
    noi_dung = Column(Text, nullable=False)
    kenh_gui = Column(String(20), default='web') # web, zalo, sms
    trang_thai_gui = Column(String(20), default='da_gui') # cho_gui, da_gui, loi
    da_doc = Column(Boolean, default=False)
    ngay_gui = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tai_khoan = relationship("TaiKhoan", back_populates="thong_baos")
    dat_san = relationship("DatSan", back_populates="thong_baos")
