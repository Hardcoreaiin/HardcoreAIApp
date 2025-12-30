@echo off
title Hardcore.ai - Desktop Mode
echo ========================================
echo   Hardcore.ai Desktop Launcher
echo ========================================
echo.
echo Starting backend server...
echo.

REM Start Python backend
cd /d "%~dp0Hardcore.ai\orchestrator"
start "Hardcore.ai Backend" cmd /k "python main.py"

timeout /t 3 /nobreak >nul

echo.
echo Opening desktop app...
echo.

REM Open in app mode (no browser UI)
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8000/web/chat.html --window-size=1400,900

echo.
echo Desktop app launched!
echo Close this window to stop the backend.
echo.
pause
