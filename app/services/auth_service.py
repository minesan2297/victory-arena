from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.tai_khoan import TaiKhoan, VaiTro
from app.models.enums import VaiTroEnum
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from app.auth.security import hash_password, verify_password, create_access_token

class AuthService:
    @staticmethod
    def register(db: Session, data: RegisterRequest) -> TaiKhoan:
        # Kiểm tra tên đăng nhập đã tồn tại chưa
        if db.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == data.ten_dang_nhap).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đăng nhập đã tồn tại"
            )
        
        # Kiểm tra SĐT đã tồn tại chưa
        if db.query(TaiKhoan).filter(TaiKhoan.so_dien_thoai == data.so_dien_thoai).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số điện thoại đã được đăng ký bởi tài khoản khác"
            )
            
        # Lấy vai trò customer
        vai_tro = db.query(VaiTro).filter(VaiTro.ten_vai_tro == VaiTroEnum.CUSTOMER.value.upper()).first()
        if not vai_tro:
            # Tạo nếu chưa có (trong trường hợp chưa seed)
            vai_tro = VaiTro(ten_vai_tro=VaiTroEnum.CUSTOMER.value.upper(), mo_ta="Khách hàng đặt sân")
            db.add(vai_tro)
            db.flush()
            
        new_user = TaiKhoan(
            ten_dang_nhap=data.ten_dang_nhap,
            mat_khau_hash=hash_password(data.mat_khau),
            ho_ten=data.ho_ten,
            so_dien_thoai=data.so_dien_thoai,
            email=data.email,
            vai_tro_id=vai_tro.vai_tro_id,
            diem_uy_tin=100,
            trang_thai='active'
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def login(db: Session, data: LoginRequest) -> TokenResponse:
        user = db.query(TaiKhoan).filter(TaiKhoan.ten_dang_nhap == data.ten_dang_nhap).first()
        if not user or not verify_password(data.mat_khau, user.mat_khau_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không chính xác"
            )
            
        if user.trang_thai != 'active':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đang bị khóa"
            )
            
        # Tạo JWT token
        token_data = {"sub": str(user.tai_khoan_id), "role": user.vai_tro.ten_vai_tro}
        access_token = create_access_token(data=token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type='bearer',
            user_id=user.tai_khoan_id,
            ho_ten=user.ho_ten,
            vai_tro=user.vai_tro.ten_vai_tro
        )
