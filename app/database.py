"""Module cấu hình kết nối Cơ sở dữ liệu SQLAlchemy.

Hỗ trợ SQLite và cung cấp generator cấp phát session cho FastAPI.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import get_settings

settings = get_settings()

# Với SQLite cần check_same_thread=False khi dùng đa luồng trong FastAPI
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False
)

# BẬT kiểm tra ràng buộc Foreign Key cho SQLite (mặc định SQLite TẮT)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Cung cấp phiên làm việc (Session) với CSDL cho mỗi request và tự đóng."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
