from contextlib import asynccontextmanager
import asyncio
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

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

def auto_seed_initial_data():
    """Tự động kiểm tra và nạp dữ liệu mẫu ban đầu nếu cơ sở dữ liệu chưa có tài khoản."""
    try:
        from app.database import SessionLocal
        from app.models.tai_khoan import TaiKhoan
        db = SessionLocal()
        try:
            if not db.query(TaiKhoan).first():
                # Cơ sở dữ liệu rỗng, tự động gọi nạp dữ liệu mẫu
                import importlib.util
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                seed_path = os.path.join(backend_dir, "seed_data.py")
                if os.path.exists(seed_path):
                    spec = importlib.util.spec_from_file_location("seed_data_mod", seed_path)
                    seed_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(seed_mod)
                    if hasattr(seed_mod, "seed_database"):
                        seed_mod.seed_database()
        finally:
            db.close()
    except Exception as e:
        print(f"[Warning] Khong the auto-seed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và tắt ứng dụng."""
    # Khởi tạo các bảng trong Database
    Base.metadata.create_all(bind=engine)
    
    # Đảm bảo có sẵn tài khoản mẫu để người dùng đăng nhập ngay
    auto_seed_initial_data()
    
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

# 1. Cấu hình CORS linh hoạt - Cho phép kết nối từ mọi thiết bị (Localhost, Port 3000, Live Server Port 5500, Mạng LAN/WiFi, file://)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def dynamic_cors_header_middleware(request: Request, call_next):
    """Middleware bổ trợ: Đảm bảo phản hồi CORS luôn hợp lệ và không bao giờ bị trình duyệt chặn."""
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

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

# 2. Đăng ký các API Routers
app.include_router(auth_router)
app.include_router(san_router)
app.include_router(dat_san_router)
app.include_router(van_hanh_router)
app.include_router(dich_vu_router)
app.include_router(khach_hang_router)
app.include_router(ai_router)
app.include_router(bao_cao_router)

# 3. Các Endpoint hệ thống
@app.get("/api/status", tags=["System"])
@app.get("/api/system/info", tags=["System"])
async def api_system_info():
    """Endpoint kiểm tra trạng thái sức khỏe và thông tin hệ thống Backend."""
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

# 4. Phục vụ tĩnh thư mục Frontend (All-in-One: Truy cập thẳng http://localhost:8000 hoặc IP LAN)
frontend_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend")),
]
frontend_dir = next((p for p in frontend_candidates if os.path.isdir(p)), None)

if frontend_dir:
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
