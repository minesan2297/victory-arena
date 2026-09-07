from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class VaiTro(Base):
    __tablename__ = 'VaiTro'
    
    vai_tro_id = Column(Integer, primary_key=True, autoincrement=True)
    ten_vai_tro = Column(String(50), unique=True, nullable=False) # admin, staff, customer
    mo_ta = Column(String(255), nullable=True)
    
    # Relationships
    tai_khoans = relationship("TaiKhoan", back_populates="vai_tro", cascade="save-update, merge")

class TaiKhoan(Base):
    __tablename__ = 'TaiKhoan'
    __table_args__ = (
        CheckConstraint('diem_uy_tin >= 0 AND diem_uy_tin <= 100', name='ck_diem_uy_tin_range'),
    )
    
    tai_khoan_id = Column(Integer, primary_key=True, autoincrement=True)
    ten_dang_nhap = Column(String(50), unique=True, nullable=False)
    mat_khau_hash = Column(String(255), nullable=False)
    ho_ten = Column(String(100), nullable=False)
    so_dien_thoai = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    vai_tro_id = Column(Integer, ForeignKey('VaiTro.vai_tro_id'), nullable=False)
    diem_uy_tin = Column(Integer, default=100)
    trang_thai = Column(String(20), default='active')
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ngay_cap_nhat = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    vai_tro = relationship("VaiTro", back_populates="tai_khoans")
    dat_sans = relationship("DatSan", back_populates="khach_hang", cascade="save-update, merge")
    check_ins = relationship("CheckIn", back_populates="nhan_vien")
    bao_caos = relationship("BaoCao", back_populates="nguoi_tao_admin")
    thong_baos = relationship("ThongBao", back_populates="tai_khoan", cascade="save-update, merge")
