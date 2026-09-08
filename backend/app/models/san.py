from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Time, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class LoaiSan(Base):
    __tablename__ = 'LoaiSan'
    
    loai_san_id = Column(Integer, primary_key=True, autoincrement=True)
    ten_loai = Column(String(50), unique=True, nullable=False) # Sân 5, Sân 7, Sân 11, Futsal
    so_nguoi_tieu_chuan = Column(Integer, nullable=False)
    mo_ta = Column(String(255), nullable=True)
    
    # Relationships
    sans = relationship("San", back_populates="loai_san", cascade="save-update, merge")

class San(Base):
    __tablename__ = 'San'
    
    ma = Column(String(20), primary_key=True) # E.g., 'SAN5-001'
    ten_san = Column(String(255), nullable=False)
    loai_san_id = Column(Integer, ForeignKey('LoaiSan.loai_san_id'), nullable=False)
    vi_tri = Column(String(255), nullable=True)
    trang_thai = Column(String(20), default='active') # active, maintenance, inactive
    mo_ta_ai = Column(Text, nullable=True)
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    loai_san = relationship("LoaiSan", back_populates="sans")
    bang_gias = relationship("BangGia", back_populates="san", cascade="save-update, merge")
    dat_sans = relationship("DatSan", back_populates="san")
    lich_dats = relationship("LichDat", back_populates="san", cascade="save-update, merge")

class BangGia(Base):
    __tablename__ = 'BangGia'
    __table_args__ = (
        Index('ix_banggia_san_loai', 'san_id', 'loai_ngay'),
        CheckConstraint('don_gia >= 0', name='ck_banggia_dongia_positive'),
    )
    
    bang_gia_id = Column(Integer, primary_key=True, autoincrement=True)
    san_id = Column(String(20), ForeignKey('San.ma'), nullable=False)
    gio_bat_dau = Column(Time, nullable=False)
    gio_ket_thuc = Column(Time, nullable=False)
    don_gia = Column(Integer, nullable=False)
    loai_ngay = Column(String(20), default='thuong') # thuong, cuoi_tuan, le
    
    # Relationships
    san = relationship("San", back_populates="bang_gias")
