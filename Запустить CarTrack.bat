@echo off
cd /d "%~dp0"
title CarTrack

echo Starting CarTrack...
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)

echo.
echo Server stopped. If there is an error above, take a photo of it.
pause
