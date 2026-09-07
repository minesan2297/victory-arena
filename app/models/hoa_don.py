from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class HoaDon(Base):
    __tablename__ = 'HoaDon'
    
    ma_hoa_don = Column(String(20), primary_key=True)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), unique=True, nullable=False)
    check_in_thuc_te = Column(DateTime, nullable=True)
    check_out_thuc_te = Column(DateTime, nullable=True)
    tien_san = Column(Integer, default=0)
    tong_dich_vu = Column(Integer, default=0)
    tien_coc_da_tru = Column(Integer, default=0)
    tong_thanh_toan = Column(Integer, default=0)
    trang_thai = Column(String(20), default='chua_thanh_toan')
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    dat_san = relationship("DatSan", back_populates="hoa_don")

class ThanhToan(Base):
    __tablename__ = 'ThanhToan'
    __table_args__ = (
        Index('ix_thanhtoan_madon', 'ma_don'),
    )
    
    thanh_toan_id = Column(Integer, primary_key=True, autoincrement=True)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=False)
    so_tien = Column(Integer, nullable=False)
    phuong_thuc = Column(String(20), default='tien_mat') # tien_mat, chuyen_khoan, vnpay, momo
    loai_giao_dich = Column(String(20), default='dat_coc') # dat_coc, thanh_toan_het, hoan_coc
    trang_thai = Column(String(20), default='thanh_cong') # cho_xu_ly, thanh_con, that_bai
    ma_giao_dich_cong = Column(String(100), nullable=True)
    thoi_gian = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    dat_san = relationship("DatSan", back_populates="thanh_toans")

class CheckIn(Base):
    __tablename__ = 'CheckIn'
    
    checkin_id = Column(Integer, primary_key=True, autoincrement=True)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=False, unique=True)
    thoi_gian_checkin = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    nhan_vien_id = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=False)
    ghi_chu = Column(Text, nullable=True)
    
    # Relationships
    dat_san = relationship("DatSan", back_populates="check_ins")
    nhan_vien = relationship("TaiKhoan", back_populates="check_ins")
