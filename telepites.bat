@echo off
chcp 65001 >nul
rem EGYSZERI TELEPÍTÉS. Ezt csak egyszer kell lefuttatni (vagy frissítéskor).
rem Letölti a programhoz szükséges két csomagot (pymupdf, anthropic).
cd /d "%~dp0"
echo A szukseges csomagok telepitese folyamatban...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Asztali parancsikon letrehozasa...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0parancsikon.ps1"

echo.
echo Kesz. Ezt az ablakot most bezarhatod. Az Asztalon ott a Munkaszam-rendezo ikon.
pause
