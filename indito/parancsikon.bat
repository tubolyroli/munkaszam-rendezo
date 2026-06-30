@echo off
chcp 65001 >nul
rem Asztali parancsikon (ikon) letrehozasa a Munkaszam-rendezohoz.
rem Eleg EGYSZER lefuttatni: dupla kattintas erre a fajlra.
rem Ez a fajl az indito\ mappaban van; a ps1 az eszkozok\ mappaban.
cd /d "%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\eszkozok\parancsikon.ps1"

echo.
echo Ha kesz, ezt az ablakot bezarhatod. Az Asztalon ott a Munkaszam-rendezo ikon -
echo dupla kattintassal indul a program.
pause
