@echo off
chcp 65001 >nul
title Victory Arena v2.0 - Khoi dong He thong (Frontend ^& Backend)
color 0A

echo ========================================================================
echo   VICTORY ARENA v2.0 - HE THONG QUAN LY SAN BONG DA TICH HOP AI
echo   Kien truc Tach biet: Frontend (Port 3000) ^& Backend (Port 8000)
echo   Nhom 20 - K23C CNTT - GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

cd /d "%~dp0"

echo [1/4] Kiem tra moi truong Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

python -c "import sys; print('[OK] Tim thay: Python ' + sys.version.split()[0])"
echo.

echo [2/4] Kiem tra thu vien Backend (requirements.txt)...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, pydantic_settings, dotenv, jose, passlib, multipart, httpx" >nul 2>&1
if errorlevel 1 goto :install_deps
echo [OK] Toan bo thu vien Backend da san sang!
echo.
goto :check_db

:install_deps
echo [THONG BAO] Phat hien thieu thu vien, dang tu dong cai dat bang pip...
echo Xin vui long cho trong giay lat...
python -m pip install -r backend\requirements.txt
if errorlevel 1 goto :pip_fail
echo [OK] Da cai dat xong toan bo thu vien can thiet!
echo.
goto :check_db

:check_db
echo [3/4] Kiem tra co so du lieu Backend...
if not exist "backend\mini_victory.db" goto :init_db
echo [OK] Co so du lieu backend\mini_victory.db da san sang!
goto :start_servers

:init_db
echo [THONG BAO] Khoi tao co so du lieu ban dau (5 san bong va tai khoan mau)...
cd /d "%~dp0backend"
python seed_data.py
cd /d "%~dp0"
goto :start_servers

:start_servers
echo.
echo [4/4] Dang khoi dong song song ca 2 tien trinh:
echo  1. Backend RESTful API:  http://127.0.0.1:8000  (Tai lieu: /docs)
echo  2. Frontend Web Client:   http://127.0.0.1:3000
echo.
echo [INFO] Tai khoan Quan tri (ADMIN): admin / Mat khau: admin123
echo [INFO] Tai khoan Nhan vien (STAFF): staff / Mat khau: staff123
echo [INFO] Tai khoan Khach hang (CUSTOMER): tuanfc / Mat khau: tuan123
echo [INFO] Tai khoan Test cua ban: test01 / Mat khau: 123456
echo ========================================================================
echo.

:: Khoi dong Backend Server tren port 8000 o cua so rieng
start "Victory Arena - Backend Server (Port 8000)" cmd /k "cd /d ""%~dp0backend"" && title Backend API (Port 8000) && color 0A && echo Dang chay Backend API tren http://127.0.0.1:8000 ... && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Khoi dong Frontend Server tren port 3000 o cua so rieng
start "Victory Arena - Frontend Web (Port 3000)" cmd /k "cd /d ""%~dp0frontend"" && title Frontend Web (Port 3000) && color 0B && echo Dang phuc vu Frontend tren http://127.0.0.1:3000 ... && python -m http.server 3000 --bind 127.0.0.1"

:: Cho 2 giay de hai server khoi dong on dinh roi mo trinh duyet
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:3000"

echo [HOAN TAT] He thong da khoi dong thanh cong!
echo Trinh duyet web da duoc mo tai http://127.0.0.1:3000.
echo De dung he thong, vui long dong 2 cua so tien trinh Backend va Frontend vua duoc mo.
echo.
pause
exit /b 0

:no_python
echo [LOI] May cua ban chua cai dat Python hoac chua them Python vao PATH!
echo Vui long tai va cai dat Python 3.10 tro len tai: https://www.python.org/
pause
exit /b 1

:pip_fail
echo [LOI] Cai dat thu vien that bai! Vui long kiem tra lai ket noi Internet.
pause
exit /b 1
