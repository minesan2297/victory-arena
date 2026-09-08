from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    # App
    app_name: str = 'Hệ thống Quản lý Sân Bóng Mini Victory Tích Hợp AI'
    app_env: str = 'development'
    debug: bool = True
    host: str = '0.0.0.0'
    port: int = 8000
    
    # Database
    database_url: str = 'sqlite:///./mini_victory.db'
    
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
