@echo off
cd /d "%~dp0"
title CarTrack

echo Starting CarTrack...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)

echo.
echo Server stopped. If there is an error above, take a photo of it.
pause
