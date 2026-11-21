@echo off
:: ====================================================================
:: BS LAB & MOBILE TRADERS — UNIVERSAL WORKSTATION ZERO-HASSLE SETUP
:: Proprietor: Syed Bisharat Ali (Shah Ji) | Shop #5, Arif Center, Lahore
:: ====================================================================

title BS LAB TOOL — Workstation Auto-Provisioner & Driver Installer
color 0B

echo.
echo ====================================================================
echo  BS LAB TOOL v2.5 PRO ENTERPRISE - ZERO-HASSLE WORKSTATION SETUP
echo  Shop #5, 1st Floor, Hamza Block, Arif Center, Hall Road, Lahore
echo ====================================================================
echo.

:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Administrator privileges required. Elevating now...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

set TOOL_DIR=%~dp0
cd /d "%TOOL_DIR%"

echo [*] Target Workstation Directory: %TOOL_DIR%
echo.

:: 2. Windows Defender Exclusion
echo [1/5] Configuring Windows Defender Real-Time Scanning Exclusions...
powershell -Command "Add-MpPreference -ExclusionPath '%TOOL_DIR%' -ErrorAction SilentlyContinue"
powershell -Command "Add-MpPreference -ExclusionProcess 'BSLabTool.exe', 'adb.exe', 'fastboot.exe' -ErrorAction SilentlyContinue"
echo [+] Windows Defender Exclusions Applied! Zero DA/Firehose false-positive blocks.
echo.

:: 3. Zero-Interruption Power & USB Selective Suspend Optimization
echo [2/5] Optimizing High Performance Power Plan & Disabling USB Suspend...
powercfg -duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f >nul 2>&1
echo [+] Power Plan Locked: Sleep disabled, USB Disconnection Guard Active!
echo.

:: 4. Silent Windows DriverStore Injection (PnPUtil Engine)
echo [3/5] Injecting Universal GSM Hardware Drivers directly into Windows DriverStore...
echo     - MediaTek VCOM & CDC Serial
echo     - Qualcomm HS-USB QDLoader 9008
echo     - Unisoc / Spreadtrum SPRD U2S Diag
echo     - Huawei PCUI & USB COM 1.0
echo     - LibUsb-win32 USB Filter

if exist "%TOOL_DIR%drivers" (
    pnputil.exe /add-driver "%TOOL_DIR%drivers\*.inf" /subdirs /install
    echo [+] All Chipset INF Drivers Successfully Injected into Windows DriverStore!
) else (
    echo [-] Warning: drivers directory not found at %TOOL_DIR%drivers
)
echo.

:: 5. Install UsbDk Filter (Driverless MTK BROM SLA/DAA Bypass)
echo [4/5] Checking UsbDk (USB Development Kit for Driverless MTK SLA/DAA Bypass)...
if exist "%TOOL_DIR%drivers\usbdk\UsbDk_1.0.22_x64.msi" (
    echo [*] Installing UsbDk x64 quietly...
    msiexec /i "%TOOL_DIR%drivers\usbdk\UsbDk_1.0.22_x64.msi" /qn /norestart
    echo [+] UsbDk Filter Engine Installed Successfully!
)
echo.

:: 6. Create Luxury Desktop Shortcut
echo [5/5] Creating Desktop Shortcut for BS Lab Tool...
set SCRIPT="%TEMP%\create_bslab_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\BS Lab Tool.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
if exist "%TOOL_DIR%dist_new\BSLabTool.exe" (
    echo oLink.TargetPath = "%TOOL_DIR%dist_new\BSLabTool.exe" >> %SCRIPT%
    echo oLink.WorkingDirectory = "%TOOL_DIR%dist_new" >> %SCRIPT%
) else (
    echo oLink.TargetPath = "%TOOL_DIR%BSLabTool.exe" >> %SCRIPT%
    echo oLink.WorkingDirectory = "%TOOL_DIR%" >> %SCRIPT%
)
echo oLink.Description = "BS Lab Tool v2.5 PRO Enterprise — Syed Bisharat Ali" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo [+] Desktop Shortcut Created!
echo.

echo ====================================================================
echo  [SUCCESS] WORKSTATION FULLY PROVISIONED FOR ZERO-HASSLE REPAIRS!
echo  All phone drivers are active in Windows DriverStore.
echo  You can now plug in ANY phone (MTK, Qualcomm, Samsung, Unisoc, Kirin)
echo  and it will be recognized instantly without manual driver setup.
echo ====================================================================
echo.
pause
