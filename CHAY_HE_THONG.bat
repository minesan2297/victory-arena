@echo off
chcp 65001 >nul
title Victory Arena v2.0 - Khoi dong May chu va Mo Web
color 0A

echo ========================================================================
echo   VICTORY ARENA v2.0 - HE THONG QUAN LY SAN BONG DA TICH HOP AI
echo   Nhom 20 - K23C CNTT - GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

cd /d "%~dp0"

echo [1/4] Kiem tra moi truong Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

python -c "import sys; print('[OK] Tim thay: Python ' + sys.version.split()[0])"
echo.

echo [2/4] Kiem tra thu vien he thong (requirements.txt)...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, pydantic_settings, dotenv, jose, passlib, multipart, httpx" >nul 2>&1
if errorlevel 1 goto :install_deps
echo [OK] Toan bo thu vien da duoc cai dat day du!
echo.
goto :check_db

:install_deps
echo [THONG BAO] Phat hien thieu thu vien, dang tu dong cai dat bang pip...
echo Xin vui long cho trong giay lat...
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fail
echo [OK] Da cai dat xong toan bo thu vien can thiet!
echo.
goto :check_db

:check_db
echo [3/4] Kiem tra co so du lieu va tai khoan he thong...
if not exist "mini_victory.db" goto :init_db
echo [OK] Co so du lieu mini_victory.db da san sang!
goto :start_web

:init_db
echo [THONG BAO] Khoi tao co so du lieu ban dau (5 san bong va tai khoan mau)...
python seed_data.py
goto :start_web

:start_web
echo.
echo [4/4] Dang mo trinh duyet Web tai http://127.0.0.1:8000 ...
echo [INFO] Tai khoan Quan tri (ADMIN): admin / Mat khau: admin123
echo [INFO] Tai khoan Nhan vien (STAFF): staff / Mat khau: staff123
echo [INFO] Tai khoan Khach hang (CUSTOMER): tuanfc / Mat khau: tuan123
echo [INFO] Tai khoan Test cua ban: test01 / Mat khau: 123456
echo.

start "" "http://127.0.0.1:8000"

echo Dang khoi chay may chu FastAPI tren cong 8000...
echo (De dung may chu, nhan to hop phim Ctrl + C hoac dong cua so nay)
echo ========================================================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:no_python
echo [LOI] May cua ban chua cai dat Python hoac chua them Python vao PATH!
echo Vui long tai va cai dat Python 3.10 tro len tai: https://www.python.org/
echo Luu y: Khi cai dat nho tich vao o Add Python to PATH
echo.
pause
exit /b 1

:pip_fail
echo [LOI] Cai dat thu vien that bai! Vui long kiem tra lai ket noi Internet.
pause
exit /b 1
