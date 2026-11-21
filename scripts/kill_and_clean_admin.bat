@echo off
set LOG="C:\BSLab_Tool\scripts\cleanup_output.log"
echo ======================================================== > %LOG%
echo BS LAB TOOL - SURGICAL ELEVATED TROJAN ERADICATION >> %LOG%
echo Execution Time: %DATE% %TIME% >> %LOG%
echo ======================================================== >> %LOG%

echo [*] Step 1: Querying and Killing Rogue Processes... >> %LOG%

:: Use WMIC to specifically target only the malicious processes by ExecutablePath
wmic process where "ExecutablePath like 'C:\\Windows\\Resources\\Themes\\explorer.exe'" call terminate >> %LOG% 2>&1
wmic process where "ExecutablePath like 'C:\\Windows\\Resources\\svchost.exe'" call terminate >> %LOG% 2>&1
wmic process where "ExecutablePath like 'C:\\Windows\\Resources\\spoolsv.exe'" call terminate >> %LOG% 2>&1
taskkill /F /IM icsys.icn.exe >> %LOG% 2>&1

timeout /t 1 /nobreak > nul

echo [*] Step 2: Deleting Malicious Registry Persistence... >> %LOG%
reg delete "HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce" /v Explorer /f >> %LOG% 2>&1
reg delete "HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce" /v Svchost /f >> %LOG% 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Explorer /f >> %LOG% 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Svchost /f >> %LOG% 2>&1
reg delete "HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run" /v Explorer /f >> %LOG% 2>&1
reg delete "HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run" /v Svchost /f >> %LOG% 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v Explorer /f >> %LOG% 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v Svchost /f >> %LOG% 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Explorer /f >> %LOG% 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Svchost /f >> %LOG% 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Explorer /f >> %LOG% 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Svchost /f >> %LOG% 2>&1

echo [*] Step 3: Taking Ownership, Modifying ACLs and Deleting Malware Files... >> %LOG%

set "T1=C:\Windows\Resources\Themes\explorer.exe"
if exist "%T1%" (
    echo Processing %T1% >> %LOG%
    takeown /F "%T1%" /A >> %LOG% 2>&1
    icacls "%T1%" /grant:r Administrators:F /grant:r Everyone:F /Q >> %LOG% 2>&1
    attrib -r -s -h "%T1%" >> %LOG% 2>&1
    del /f /q /a "%T1%" >> %LOG% 2>&1
)

set "T2=C:\Windows\Resources\Themes\icsys.icn.exe"
if exist "%T2%" (
    echo Processing %T2% >> %LOG%
    takeown /F "%T2%" /A >> %LOG% 2>&1
    icacls "%T2%" /grant:r Administrators:F /grant:r Everyone:F /Q >> %LOG% 2>&1
    attrib -r -s -h "%T2%" >> %LOG% 2>&1
    del /f /q /a "%T2%" >> %LOG% 2>&1
)

set "T3=C:\Windows\Resources\Themes\icsys.icn"
if exist "%T3%" (
    echo Processing %T3% >> %LOG%
    takeown /F "%T3%" /A >> %LOG% 2>&1
    icacls "%T3%" /grant:r Administrators:F /grant:r Everyone:F /Q >> %LOG% 2>&1
    attrib -r -s -h "%T3%" >> %LOG% 2>&1
    del /f /q /a "%T3%" >> %LOG% 2>&1
)

set "T4=C:\Windows\Resources\svchost.exe"
if exist "%T4%" (
    echo Processing %T4% >> %LOG%
    takeown /F "%T4%" /A >> %LOG% 2>&1
    icacls "%T4%" /grant:r Administrators:F /grant:r Everyone:F /Q >> %LOG% 2>&1
    attrib -r -s -h "%T4%" >> %LOG% 2>&1
    del /f /q /a "%T4%" >> %LOG% 2>&1
)

set "T5=C:\Windows\Resources\spoolsv.exe"
if exist "%T5%" (
    echo Processing %T5% >> %LOG%
    takeown /F "%T5%" /A >> %LOG% 2>&1
    icacls "%T5%" /grant:r Administrators:F /grant:r Everyone:F /Q >> %LOG% 2>&1
    attrib -r -s -h "%T5%" >> %LOG% 2>&1
    del /f /q /a "%T5%" >> %LOG% 2>&1
)

echo [*] Step 4: Verification of files status... >> %LOG%
if exist "%T1%" ( echo [!] ERROR: %T1% STILL EXISTS >> %LOG% ) else ( echo [+] SUCCESS: %T1% DELETED >> %LOG% )
if exist "%T2%" ( echo [!] ERROR: %T2% STILL EXISTS >> %LOG% ) else ( echo [+] SUCCESS: %T2% DELETED >> %LOG% )
if exist "%T3%" ( echo [!] ERROR: %T3% STILL EXISTS >> %LOG% ) else ( echo [+] SUCCESS: %T3% DELETED >> %LOG% )
if exist "%T4%" ( echo [!] ERROR: %T4% STILL EXISTS >> %LOG% ) else ( echo [+] SUCCESS: %T4% DELETED >> %LOG% )
if exist "%T5%" ( echo [!] ERROR: %T5% STILL EXISTS >> %LOG% ) else ( echo [+] SUCCESS: %T5% DELETED >> %LOG% )

echo ======================================================== >> %LOG%
echo ALL OPERATIONS COMPLETE >> %LOG%
echo ======================================================== >> %LOG%
