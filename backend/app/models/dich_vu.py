from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class DanhMucDichVu(Base):
    __tablename__ = 'DanhMucDichVu'
    
    dich_vu_id = Column(Integer, primary_key=True, autoincrement=True)
    ten_dich_vu = Column(String(100), nullable=False)
    don_vi_tinh = Column(String(20), nullable=False)
    don_gia = Column(Integer, nullable=False)
    danh_muc = Column(String(20), default='NUOC_UONG') # NUOC_UONG, TRANG_BI, KHAC
    trang_thai = Column(String(20), default='active') # active, inactive
    
    # Relationships
    su_dung_dich_vus = relationship("SuDungDichVu", back_populates="dich_vu", cascade="save-update, merge")

class SuDungDichVu(Base):
    __tablename__ = 'SuDungDichVu'
    __table_args__ = (
        Index('ix_sddv_madon', 'ma_don'),
        CheckConstraint('so_luong > 0', name='ck_sddv_soluong_positive'),
    )
    
    su_dung_id = Column(Integer, primary_key=True, autoincrement=True)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=False)
    dich_vu_id = Column(Integer, ForeignKey('DanhMucDichVu.dich_vu_id'), nullable=False)
    so_luong = Column(Integer, default=1)
    don_gia_tai_ban = Column(Integer, nullable=False)
    thanh_tien = Column(Integer, nullable=False)
    
    # Relationships
    dat_san = relationship("DatSan", back_populates="su_dung_dich_vus")
    dich_vu = relationship("DanhMucDichVu", back_populates="su_dung_dich_vus")
