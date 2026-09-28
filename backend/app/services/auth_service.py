from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.tai_khoan import TaiKhoan, VaiTro
from app.models.enums import VaiTroEnum
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, DoiMatKhauRequest
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

    @staticmethod
    def doi_mat_khau(db: Session, current_user: TaiKhoan, data: DoiMatKhauRequest) -> dict:
        """Đổi mật khẩu — xử lý đầy đủ 7 test case trong tài liệu kiểm thử.
        
        TC1: Thành công (C1=T, C2=T, C3=T)
        TC2: Xác nhận không khớp (C3=F) — bị chặn tại schema validator
        TC3: Xác nhận để trống (C3=B) — bị chặn tại schema validator
        TC4: Mật khẩu mới để trống (C2=B) — bị chặn tại schema validator
        TC5: Mật khẩu mới không hợp lệ (C2=F) — bị chặn tại schema validator
        TC6: Mật khẩu hiện tại sai (C1=F) — xử lý tại đây
        TC7: Mật khẩu hiện tại để trống (C1=B) — bị chặn tại schema validator

        LƯU Ý: current_user được lấy từ get_current_user dependency (session riêng).
        Phải re-fetch qua db session hiện tại để tránh lỗi DetachedInstanceError
        và đảm bảo db.commit() lưu đúng vào database.
        """
        # Re-fetch user qua db session hiện tại để tránh session mismatch
        user = db.query(TaiKhoan).filter(
            TaiKhoan.tai_khoan_id == current_user.tai_khoan_id
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản không tồn tại"
            )

        # TC6: Kiểm tra mật khẩu hiện tại có đúng không
        if not verify_password(data.mat_khau_hien_tai, user.mat_khau_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng"
            )

        # TC1: Tất cả hợp lệ — cập nhật mật khẩu và lưu vào database
        user.mat_khau_hash = hash_password(data.mat_khau_moi)
        db.commit()
        db.refresh(user)
        return {"message": "Đổi mật khẩu thành công"}


