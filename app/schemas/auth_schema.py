from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class LoginRequest(BaseModel):
    ten_dang_nhap: str
    mat_khau: str

class RegisterRequest(BaseModel):
    ten_dang_nhap: str = Field(..., min_length=3)
    mat_khau: str = Field(..., min_length=6)
    ho_ten: str
    so_dien_thoai: str
    email: Optional[str] = None

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
