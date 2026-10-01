from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

# Xác định đường dẫn thư mục backend và CSDL mặc định tuyệt đối (lưu trong backend/data/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_FILE = DATA_DIR / "mini_victory.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    # App
    app_name: str = 'Hệ thống Quản lý Sân Bóng Mini Victory Tích Hợp AI'
    app_env: str = 'development'
    debug: bool = True
    host: str = '0.0.0.0'
    port: int = 8000
    
    # Database - Sử dụng đường dẫn tuyệt đối ổn định, tránh tạo DB rỗng khi chạy từ thư mục khác
    database_url: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"
    
    # JWT Auth
    jwt_secret_key: str = 'footy-arena-secret-key-nhom20-2026'
    jwt_expiry_minutes: int = 60
    
    # Lock Expiry
    lock_expiry_minutes: int = 10
    
    # AI / Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = 'gemini-1.5-flash'

@lru_cache()
def get_settings() -> Settings:
    return Settings()
