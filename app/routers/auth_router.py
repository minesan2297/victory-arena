from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.auth.dependencies import get_current_user
from app.models.tai_khoan import TaiKhoan

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService.register(db, data)
    return UserResponse(
        tai_khoan_id=user.tai_khoan_id,
        ten_dang_nhap=user.ten_dang_nhap,
        ho_ten=user.ho_ten,
        so_dien_thoai=user.so_dien_thoai,
        email=user.email,
        vai_tro=user.vai_tro.ten_vai_tro if user.vai_tro else "CUSTOMER",
        diem_uy_tin=user.diem_uy_tin,
        trang_thai=user.trang_thai
    )

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, data)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: TaiKhoan = Depends(get_current_user)):
    # Ánh xạ vai trò sang tên vai trò dạng chuỗi hiển thị
    return UserResponse(
        tai_khoan_id=current_user.tai_khoan_id,
        ten_dang_nhap=current_user.ten_dang_nhap,
        ho_ten=current_user.ho_ten,
        so_dien_thoai=current_user.so_dien_thoai,
        email=current_user.email,
        vai_tro=current_user.vai_tro.ten_vai_tro,
        diem_uy_tin=current_user.diem_uy_tin,
        trang_thai=current_user.trang_thai
    )
