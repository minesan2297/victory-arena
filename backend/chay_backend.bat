@echo off
chcp 65001 >nul
title Victory Arena v2.0 - Backend REST API (Port 8000)
color 0A

echo ========================================================================
echo   VICTORY ARENA v2.0 - PHAN HE BACKEND RESTFUL API
echo   Nhom 20 - K23C CNTT - GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

cd /d "%~dp0"

echo [1/3] Kiem tra moi truong Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

python -c "import sys; print('[OK] Tim thay: Python ' + sys.version.split()[0])"
echo.

echo [2/3] Kiem tra co so du lieu...
if not exist "mini_victory.db" (
    echo [THONG BAO] Khoi tao co so du lieu mini_victory.db...
    python seed_data.py
) else (
    echo [OK] Co so du lieu mini_victory.db da san sang!
)
echo.

echo [3/3] Khoi dong May chu FastAPI tren cong 8000...
echo - API Base URL:      http://127.0.0.1:8000
echo - OpenAPI Swagger:   http://127.0.0.1:8000/docs
echo - ReDoc Spec:        http://127.0.0.1:8000/redoc
echo.
echo (De dung may chu, nhan Ctrl + C hoac dong cua so nay)
echo ========================================================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
exit /b 0

:no_python
echo [LOI] Chua cai dat Python hoac chua them vao PATH!
pause
exit /b 1
