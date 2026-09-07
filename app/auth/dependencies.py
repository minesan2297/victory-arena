from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tai_khoan import TaiKhoan, VaiTro
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> TaiKhoan:
    """Xác thực token và lấy thông tin người dùng hiện tại"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tai_khoan_id: str = payload.get("sub")
    if not tai_khoan_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa thông tin định danh",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(TaiKhoan).filter(TaiKhoan.tai_khoan_id == tai_khoan_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy người dùng",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

def require_admin(current_user: TaiKhoan = Depends(get_current_user)) -> TaiKhoan:
    """Yêu cầu quyền quản trị viên"""
    if current_user.vai_tro.ten_vai_tro != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền truy cập, yêu cầu quyền ADMIN",
        )
    return current_user

def require_staff_or_admin(current_user: TaiKhoan = Depends(get_current_user)) -> TaiKhoan:
    """Yêu cầu quyền nhân viên hoặc quản trị viên"""
    if current_user.vai_tro.ten_vai_tro not in ["ADMIN", "STAFF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền truy cập, yêu cầu quyền STAFF hoặc ADMIN",
        )
    return current_user
