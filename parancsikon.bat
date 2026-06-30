@echo off
chcp 65001 >nul
rem Asztali parancsikon (ikon) letrehozasa a Munkaszam-rendezohoz.
rem Eleg EGYSZER lefuttatni: dupla kattintas erre a fajlra.
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0parancsikon.ps1"

echo.
echo Ha kesz, ezt az ablakot bezarhatod. Az Asztalon ott a Munkaszam-rendezo ikon -
echo dupla kattintassal indul a program.
pause
