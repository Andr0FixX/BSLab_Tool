@echo off
:: ========================================================
:: BS Lab Tool PRO v2.0 - Windows Defender Exclusion Tool
:: Run as Administrator to prevent Windows Defender from 
:: blocking GSM exploit payloads, ADB/Fastboot, or loaders.
:: ========================================================
echo ========================================================
echo   BS LAB TOOL PRO v2.0 - WINDOWS DEFENDER EXCLUSION
echo ========================================================
echo.
echo Adding BS Lab Tool folder to Windows Defender Exclusions...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command Add-MpPreference -ExclusionPath ''%~dp0'''"
echo.
echo [+] Success! BS Lab Tool directory has been whitelisted.
echo [+] No more false-positive virus detections or auto-deletions.
echo.
pause
