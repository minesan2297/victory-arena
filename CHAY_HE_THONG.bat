@echo off
chcp 65001 >nul
title Victory Arena v2.0 - Khởi động Máy chủ và Mở Web
color 0A

echo ========================================================================
echo   VICTORY ARENA v2.0 - HE THONG QUAN LY SAN BONG DA TICH HOP AI
echo   Nhom 20 - K23C CNTT ^| GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

REM Chuyển đến thư mục chứa file .bat này bất kể người dùng giải nén ở đâu
cd /d "%~dp0"

echo [1/5] Kiem tra moi truong Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [LOI] May cua ban chua cai dat Python hoac chua them Python vao PATH!
    echo Vui long tai va cai dat Python 3.10 tro len tai: https://www.python.org/
    echo (Luu y: Khi cai dat nho tich vao o 'Add Python to PATH')
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Tim thay: %PY_VER%
echo.

echo [2/5] Kiem tra va cai dat thu vien phu thuoc (requirements.txt)...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, pydantic_settings, dotenv, jose, passlib, multipart, httpx" >nul 2>&1
if errorlevel 1 (
    echo [THONG BAO] Phat hien thieu thu vien, dang tu dong cai dat bang pip...
    echo (Qua trinh nay chi dien ra trong lan chay dau tien, xin vui long cho...)
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [LOI] Cai dat thu vien that bai! Vui long kiem tra lai ket noi Internet.
        pause
        exit /b 1
    )
    echo [OK] Da cai dat xong toan bo thu vien can thiet!
) else (
    echo [OK] Toan bo thu vien da duoc cai dat day du!
)
echo.

echo [3/5] Kiem tra co so du lieu va tai khoan he thong...
if not exist "mini_victory.db" (
    echo [THONG BAO] Khoi tao co so du lieu ban dau (5 san bong, tai khoan mau)...
    python seed_data.py
) else (
    echo [OK] Co so du lieu mini_victory.db da san sang!
)
echo.

echo [4/5] Tu dong mo trinh duyet Web tai http://127.0.0.1:8000 ...
echo [INFO] Tai khoan Quan tri (ADMIN): admin / Mat khau: admin123
echo [INFO] Tai khoan Nhan vien (STAFF): staff / Mat khau: staff123
echo [INFO] Tai khoan Khach hang (CUSTOMER): tuanfc / Mat khau: tuan123
echo.

start "" "http://127.0.0.1:8000"

echo [5/5] Dang khoi chay may chu FastAPI tren cong 8000...
echo (De dung may chu, nhan to hop phim Ctrl + C hoac dong cua so nay)
echo ========================================================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
