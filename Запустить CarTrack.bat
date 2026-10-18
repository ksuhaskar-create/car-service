@echo off
cd /d "%~dp0"
title CarTrack

where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)

echo Starting CarTrack... Do not close this window.
start "" /min cmd /c "ping -n 4 127.0.0.1 >nul & start http://127.0.0.1:5000"

%PY% app.py

echo.
echo Server stopped. If there is an error above, take a photo of it.
pause