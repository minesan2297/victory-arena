from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Date, Time, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class DatSan(Base):
    __tablename__ = 'DatSan'
    __table_args__ = (
        Index('ix_datsan_ngay_tt', 'ngay_da', 'trang_thai'),
    )
    
    ma_don = Column(String(20), primary_key=True)
    ma_khach_hang = Column(Integer, ForeignKey('TaiKhoan.tai_khoan_id'), nullable=False, index=True)
    ma_san = Column(String(20), ForeignKey('San.ma'), nullable=False, index=True)
    ngay_da = Column(Date, nullable=False)
    gio_bat_dau = Column(Time, nullable=False)
    gio_ket_thuc = Column(Time, nullable=False)
    tien_coc = Column(Integer, default=0)
    trang_thai = Column(String(20), default='cho_coc') # cho_coc, da_xac_nhan, dang_da, hoan_tat, da_huy
    lock_expires_at = Column(DateTime, nullable=True)
    ghi_chu = Column(Text, nullable=True)
    ngay_tao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ngay_cap_nhat = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    khach_hang = relationship("TaiKhoan", back_populates="dat_sans")
    san = relationship("San", back_populates="dat_sans")
    hoa_don = relationship("HoaDon", back_populates="dat_san", uselist=False, cascade="save-update, merge")
    thanh_toans = relationship("ThanhToan", back_populates="dat_san", cascade="save-update, merge")
    check_ins = relationship("CheckIn", back_populates="dat_san", cascade="save-update, merge")
    su_dung_dich_vus = relationship("SuDungDichVu", back_populates="dat_san", cascade="save-update, merge")
    lich_dats = relationship("LichDat", back_populates="dat_san", cascade="save-update, merge")
    thong_baos = relationship("ThongBao", back_populates="dat_san", cascade="save-update, merge")

class LichDat(Base):
    __tablename__ = 'LichDat'
    __table_args__ = (
        Index('ix_lichdat_san_time', 'san_id', 'bat_dau', 'ket_thuc'),
        CheckConstraint('ket_thuc > bat_dau', name='ck_lichdat_time_order'),
    )
    
    lich_dat_id = Column(Integer, primary_key=True, autoincrement=True)
    san_id = Column(String(20), ForeignKey('San.ma'), nullable=False)
    ma_don = Column(String(20), ForeignKey('DatSan.ma_don'), nullable=True)
    bat_dau = Column(DateTime, nullable=False)
    ket_thuc = Column(DateTime, nullable=False)
    loai_lich = Column(String(20), default='thue') # thue, bao_tri
    ghi_chu = Column(String(255), nullable=True)
    
    # Relationships
    san = relationship("San", back_populates="lich_dats")
    dat_san = relationship("DatSan", back_populates="lich_dats")
