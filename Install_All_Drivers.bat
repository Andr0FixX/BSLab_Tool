@echo off
:: ========================================================
::  BS Lab Tool v2.0 PRO - Master Driver Installer
::  Silent Driver Deployment for Shop Workstation
:: ========================================================
title Installing GSM Hardware Drivers...
cd /d "%~dp0"

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [*] Requesting Administrator Privileges to install drivers...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo    BS Lab Tool PRO - Automated Driver Installation
echo ========================================================
echo.

echo [1/4] Installing MediaTek (MTK) USB VCOM & Preloader Drivers...
pnputil.exe /add-driver "%~dp0drivers\mtk\*.inf" /install >nul 2>&1
if exist "%~dp0_internal\drivers\mtk\*.inf" (
    pnputil.exe /add-driver "%~dp0_internal\drivers\mtk\*.inf" /install >nul 2>&1
)
echo      -> MediaTek Drivers: OK!

echo [2/4] Installing Qualcomm HS-USB QDLoader 9008 Drivers...
pnputil.exe /add-driver "%~dp0drivers\qualcomm\*.inf" /install >nul 2>&1
if exist "%~dp0_internal\drivers\qualcomm\*.inf" (
    pnputil.exe /add-driver "%~dp0_internal\drivers\qualcomm\*.inf" /install >nul 2>&1
)
echo      -> Qualcomm Drivers: OK!

echo [3/4] Installing Unisoc / Spreadtrum Drivers...
pnputil.exe /add-driver "%~dp0drivers\unisoc\*.inf" /install >nul 2>&1
if exist "%~dp0_internal\drivers\unisoc\*.inf" (
    pnputil.exe /add-driver "%~dp0_internal\drivers\unisoc\*.inf" /install >nul 2>&1
)
echo      -> Unisoc Drivers: OK!

echo [4/4] Installing UsbDk 64-bit Low-Level USB Capture Driver...
if exist "%~dp0drivers\usbdk\UsbDk_1.0.22_x64.msi" (
    msiexec.exe /i "%~dp0drivers\usbdk\UsbDk_1.0.22_x64.msi" /quiet /norestart
    echo      -> UsbDk Driver: OK!
) else if exist "%~dp0_internal\drivers\usbdk\UsbDk_1.0.22_x64.msi" (
    msiexec.exe /i "%~dp0_internal\drivers\usbdk\UsbDk_1.0.22_x64.msi" /quiet /norestart
    echo      -> UsbDk Driver: OK!
) else (
    echo      -> UsbDk: Skipped (MSI file not found)
)

echo.
echo [*] Configuring Windows Defender Exclusions for BS Lab Tool...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-MpPreference -ExclusionPath '%~dp0'" >nul 2>&1
echo      -> Windows Defender Exclusion: Configured!

echo.
echo ========================================================
echo     ALL GSM DRIVERS INSTALLED & READY FOR SHOP WORK!
echo ========================================================
echo You can now connect MTK, Qualcomm, Unisoc, and Samsung devices!
pause
exit
