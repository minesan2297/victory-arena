from app.routers.auth_router import router as auth_router
from app.routers.san_router import router as san_router
from app.routers.dat_san_router import router as dat_san_router
from app.routers.van_hanh_router import router as van_hanh_router
from app.routers.dich_vu_router import router as dich_vu_router
from app.routers.khach_hang_router import router as khach_hang_router
from app.routers.ai_router import router as ai_router
from app.routers.bao_cao_router import router as bao_cao_router

__all__ = [
    "auth_router",
    "san_router",
    "dat_san_router",
    "van_hanh_router",
    "dich_vu_router",
    "khach_hang_router",
    "ai_router",
    "bao_cao_router"
]
