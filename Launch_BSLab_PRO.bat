@echo off
:: ========================================================
::  BS Lab Tool v2.0 PRO - Portable Workstation Launcher
::  Syed Bisharat Ali | BS Lab & Mobile Traders
:: ========================================================
title BS Lab Tool v2.0 PRO - Starting...
cd /d "%~dp0"

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [*] Requesting Administrator Privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title BS Lab Tool v2.0 PRO - Workstation
echo ========================================================
echo        Launching BS Lab Tool v2.0 PRO Workstation
echo ========================================================
echo [*] Location: %CD%
echo [*] Mode: Standalone Portable (Zero Python Required)
echo [*] Starting Engine...

start "" "%~dp0BSLab_Tool.exe"
exit
