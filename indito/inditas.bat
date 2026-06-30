@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
rem ============================================================================
rem  A Munkaszám-rendező elindítása. Erre a fájlra (ill. az asztali ikonra) kell
rem  duplán kattintani.
rem
rem  Induláskor csendben FRISSÍT is: ha van git + internet és új verzió érhető el,
rem  letölti. Ha bármi hibázik (nincs net, nincs git), NEM állunk meg — a program a
rem  meglévő verzióval is elindul.
rem
rem  FONTOS (fejlesztőnek): ezt a fájlt jövőbeli frissítésben lehetőleg NE módosítsd,
rem  mert önmagát is frissítheti (egy futó .bat módosítása megzavarhatja a cmd-t).
rem
rem  Ez a fájl az indito\ mappában van; a program gyökere egy szinttel feljebb.
rem ============================================================================
cd /d "%~dp0.."

where git >nul 2>nul
if errorlevel 1 goto inditas

echo Frissites ellenorzese...
for /f "delims=" %%i in ('git rev-parse HEAD 2^>nul') do set "ELOTTE=%%i"
git pull --ff-only --quiet 2>nul
for /f "delims=" %%i in ('git rev-parse HEAD 2^>nul') do set "UTANA=%%i"
if "!ELOTTE!"=="!UTANA!" goto inditas

rem Volt frissites: ha valtozott a requirements.txt, telepitsuk az uj csomagokat.
git diff --name-only "!ELOTTE!" "!UTANA!" 2>nul | findstr /i /c:"requirements.txt" >nul
if not errorlevel 1 (
  echo Uj csomagok telepitese...
  python -m pip install -r requirements.txt
)

:inditas
python -m munkaszam_rendezo
if errorlevel 1 (
  echo.
  echo Hiba tortent. Kerlek, keszits egy kepernyokepet errol az ablakrol.
  pause
)
endlocal
