@echo off
title Victory Arena v2.0 - Khoi dong may chu va Mo Web
echo ========================================================================
echo   VICTORY ARENA v2.0 - HE THONG QUAN LY SAN BONG DA TICH HOP AI
echo   Nhom 20 - K23C CNTT ^| GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

cd /d "C:\Users\ADMIN\.gemini\antigravity\scratch\sports_court_ai_mgmt\chuong_trinh_he_thong"
if errorlevel 1 (
    echo [ERROR] Khong tim thay thu muc chuong trinh!
    pause
    exit /b 1
)

echo [1/3] Kiem tra du lieu va khoi tao tai khoan Admin, Staff...
python seed_data.py

echo.
echo [2/3] Tu dong mo trinh duyet Web tai http://127.0.0.1:8000 ...
echo [INFO] Tai khoan Admin: admin / Mat khau: admin123
echo [INFO] Tai khoan Staff: staff / Mat khau: staff123
echo.

start "" "http://127.0.0.1:8000"

echo [3/3] Dang chay may chu FastAPI...
python -m uvicorn app.main:app --app-dir "C:\Users\ADMIN\.gemini\antigravity\scratch\sports_court_ai_mgmt\chuong_trinh_he_thong" --host 127.0.0.1 --port 8000

pause
