import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional


class LoginRequest(BaseModel):
    ten_dang_nhap: str
    mat_khau: str

    @field_validator('ten_dang_nhap')
    @classmethod
    def validate_login_username(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError('Tên đăng nhập không được để trống')
        return v_clean

    @field_validator('mat_khau')
    @classmethod
    def validate_login_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Mật khẩu không được để trống hoặc chỉ chứa khoảng trắng')
        return v


class RegisterRequest(BaseModel):
    ten_dang_nhap: str = Field(..., min_length=3, max_length=50)
    mat_khau: str = Field(..., min_length=6, max_length=100)
    ho_ten: str = Field(..., min_length=2, max_length=100)
    so_dien_thoai: str
    email: Optional[str] = None

    @field_validator('ten_dang_nhap')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v_clean = v.strip()
        # Kiểm tra khoảng trắng
        if ' ' in v_clean:
            raise ValueError('Tên đăng nhập không được chứa khoảng trắng')
        # Kiểm tra chỉ cho phép chữ cái thường, hoa, số, gạch dưới, gạch ngang (không dấu tiếng Việt, không ký tự đặc biệt)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v_clean):
            raise ValueError('Tên đăng nhập chỉ được chứa chữ cái không dấu (a-z, A-Z), chữ số (0-9), dấu gạch dưới (_) hoặc gạch ngang (-)')
        return v_clean.lower()

    @field_validator('mat_khau')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError('Mật khẩu không được chứa khoảng trắng')
        if len(v.strip()) < 6:
            raise ValueError('Mật khẩu phải có độ dài tối thiểu 6 ký tự không tính khoảng trắng')
        return v

    @field_validator('ho_ten')
    @classmethod
    def validate_fullname(cls, v: str) -> str:
        v_clean = re.sub(r'\s+', ' ', v.strip())
        if len(v_clean) < 2:
            raise ValueError('Họ và tên phải có ít nhất 2 ký tự')
        return v_clean

    @field_validator('so_dien_thoai')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v_clean = v.strip()
        # Chuẩn số điện thoại di động Việt Nam: 10 chữ số, bắt đầu bằng 03, 05, 07, 08, 09
        if not re.match(r'^(03|05|07|08|09)\d{8}$', v_clean):
            raise ValueError('Số điện thoại không hợp lệ (phải gồm 10 chữ số hợp lệ của Việt Nam, ví dụ 0988123456)')
        return v_clean

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v_clean):
            raise ValueError('Địa chỉ email không đúng định dạng')
        return v_clean.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id: int
    ho_ten: str
    vai_tro: str


class UserResponse(BaseModel):
    tai_khoan_id: int
    ten_dang_nhap: str
    ho_ten: str
    so_dien_thoai: str
    email: Optional[str] = None
    vai_tro: str
    diem_uy_tin: int
    trang_thai: str

    model_config = ConfigDict(from_attributes=True)


class DoiMatKhauRequest(BaseModel):
    """Schema yêu cầu đổi mật khẩu — khớp với 7 test case trong tài liệu kiểm thử."""
    mat_khau_hien_tai: str
    mat_khau_moi: str
    xac_nhan_mat_khau_moi: str

    # TC7: Mật khẩu hiện tại để trống
    @field_validator('mat_khau_hien_tai')
    @classmethod
    def validate_mat_khau_hien_tai(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Vui lòng nhập mật khẩu hiện tại')
        return v

    # TC4: Mật khẩu mới để trống | TC5: Mật khẩu mới không hợp lệ (< 6 ký tự)
    @field_validator('mat_khau_moi')
    @classmethod
    def validate_mat_khau_moi(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Vui lòng nhập mật khẩu mới')
        if len(v.strip()) < 6:
            raise ValueError('Mật khẩu mới không hợp lệ (phải có ít nhất 6 ký tự)')
        return v

    # TC3: Xác nhận mật khẩu để trống
    @field_validator('xac_nhan_mat_khau_moi')
    @classmethod
    def validate_xac_nhan(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Vui lòng nhập xác nhận mật khẩu mới')
        return v

    # TC2: Xác nhận mật khẩu không khớp
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'DoiMatKhauRequest':
        if (self.mat_khau_moi and self.xac_nhan_mat_khau_moi
                and self.mat_khau_moi != self.xac_nhan_mat_khau_moi):
            raise ValueError('Xác nhận mật khẩu mới không khớp với mật khẩu mới')
        return self


class DoiMatKhauResponse(BaseModel):
    """Phản hồi sau khi đổi mật khẩu thành công."""
    message: str = 'Đổi mật khẩu thành công'
