from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.database import engine, Base
from app.routers import (
    auth_router,
    san_router,
    dat_san_router,
    van_hanh_router,
    dich_vu_router,
    khach_hang_router,
    ai_router,
    bao_cao_router
)
from app.services import start_lock_expiry_scheduler

# Đảm bảo các models đã được nạp
import app.models  # noqa: F401

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và tắt ứng dụng."""
    # Khởi tạo các bảng trong Database
    Base.metadata.create_all(bind=engine)
    
    # Khởi động Background Task quét Lock giữ sân 10 phút
    task = asyncio.create_task(start_lock_expiry_scheduler())
    
    yield
    
    # Hủy Task khi dừng server
    task.cancel()

app = FastAPI(
    title=settings.app_name,
    description="Hệ thống Quản lý Sân Thể thao Cho thuê Tích hợp Trí tuệ Nhân tạo (AI) - RESTful API Backend - Nhóm 20",
    version="2.0.0",
    lifespan=lifespan
)

# Cấu hình CORS - Cho phép kết nối từ Frontend (Port 3000) và các client khác
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Bắt các lỗi validate từ Pydantic và chuyển thành thông báo tiếng Việt thân thiện."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    msg = str(first_error.get("msg", "Dữ liệu gửi lên không hợp lệ"))
    if "Value error, " in msg:
        msg = msg.replace("Value error, ", "")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": msg}
    )

# Đăng ký các API Routers
app.include_router(auth_router)
app.include_router(san_router)
app.include_router(dat_san_router)
app.include_router(van_hanh_router)
app.include_router(dich_vu_router)
app.include_router(khach_hang_router)
app.include_router(ai_router)
app.include_router(bao_cao_router)

@app.get("/", tags=["System"])
async def api_root():
    """Endpoint gốc kiểm tra trạng thái sức khỏe và tài liệu API Backend."""
    return {
        "system": "Victory Arena v2.0 - Sports Court Management API",
        "status": "online",
        "version": "2.0.0",
        "environment": settings.app_env,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "team": "Nhóm 20 - K23C CNTT",
        "instructor": "ThS. Nguyễn Tuấn Anh"
    }

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    """Trả về favicon quả bóng đá ⚽ giúp trình duyệt hiển thị icon và không báo lỗi 404."""
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚽</text></svg>"""
    return Response(content=svg_icon, media_type="image/svg+xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
