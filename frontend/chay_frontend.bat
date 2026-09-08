@echo off
chcp 65001 >nul
title Victory Arena v2.0 - Frontend Web Client (Port 3000)
color 0B

echo ========================================================================
echo   VICTORY ARENA v2.0 - PHAN HE FRONTEND WEB CLIENT
echo   Nhom 20 - K23C CNTT - GVHD: ThS. Nguyen Tuan Anh
echo ========================================================================
echo.

cd /d "%~dp0"

echo Dang khoi dong Web Server tren cong 3000...
echo Dia chi truy cap: http://127.0.0.1:3000
echo.
echo Luu y: Dam bao Backend API dang chay tai http://127.0.0.1:8000
echo (De dung server, nhan Ctrl + C hoac dong cua so nay)
echo ========================================================================
echo.

start "" "http://127.0.0.1:3000"

python -m http.server 3000 --bind 127.0.0.1
pause
