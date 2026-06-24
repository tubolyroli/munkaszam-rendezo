@echo off
chcp 65001 >nul
rem EGYSZERI TELEPÍTÉS. Ezt csak egyszer kell lefuttatni (vagy frissítéskor).
rem Letölti a programhoz szükséges két csomagot (pymupdf, anthropic).
cd /d "%~dp0"
echo A szukseges csomagok telepitese folyamatban...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Kesz. Ezt az ablakot most bezarhatod.
pause
