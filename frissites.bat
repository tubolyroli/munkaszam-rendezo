@echo off
chcp 65001 >nul
rem ============================================================================
rem  A Munkaszám-rendező FRISSÍTÉSE a legújabb verzióra.
rem  Erre a fájlra kell duplán kattintani, ha új verzió érkezett.
rem
rem  A helyi beallitasok (config.json — API kulcs, partnerek, célmappa) NEM
rem  irodnak felul, azok megmaradnak.
rem ============================================================================
cd /d "%~dp0"

where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo A Git nincs telepitve ezen a gepen, igy a frissites nem tud lefutni.
  echo Kerlek, jelezd a fejlesztonek.
  pause
  exit /b 1
)

echo Frissites letoltese...
git pull
if errorlevel 1 (
  echo.
  echo Nem sikerult frissiteni. Ellenorizd az internetkapcsolatot,
  echo es keszits egy kepernyokepet errol az ablakrol.
  pause
  exit /b 1
)

echo Szukseges csomagok ellenorzese...
python -m pip install -r requirements.txt

echo.
echo Kesz! A program a legujabb verziora frissult.
echo Ezt az ablakot bezarhatod, es az inditas.bat-tal indithatod a programot.
pause
