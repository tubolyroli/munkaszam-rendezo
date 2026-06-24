@echo off
chcp 65001 >nul
rem A Munkaszám-rendező elindítása. Erre a fájlra kell duplán kattintani.
cd /d "%~dp0"
python -m munkaszam_rendezo
if errorlevel 1 (
  echo.
  echo Hiba tortent. Kerlek, keszits egy kepernyokepet errol az ablakrol.
  pause
)
