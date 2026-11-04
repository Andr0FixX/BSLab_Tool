@echo off
title BS Lab Tool v2.0 PRO — MediaTek Servicing Platform
cd /d "%~dp0"
echo ========================================================
echo         Launching BS Lab Tool v2.0 PRO
echo ========================================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong while running the application.
    pause
)
