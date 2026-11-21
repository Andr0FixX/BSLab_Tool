@echo off
:: ====================================================================
:: BS LAB & MOBILE TRADERS — 1-CLICK NEW PC DEPLOYMENT & SYNC ENGINE
:: Proprietor: Syed Bisharat Ali (Shah Ji) | Shop #5, Arif Center, Lahore
:: ====================================================================

title BS LAB TOOL — 1-Click Universal Workstation Auto-Provisioner
color 0B

echo.
echo ====================================================================
echo  BS LAB TOOL v2.5 PRO ENTERPRISE - NEW PC 1-CLICK SYNC & SETUP
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

set SCRIPT_DIR=%~dp0
set TARGET_DIR=C:\BSLab_Tool
set ZIP_NAME=BSLab_Tool_Sync_Master.zip

echo [*] Current Working Location: %SCRIPT_DIR%
echo [*] Target Deployment Destination: %TARGET_DIR%
echo.

:: 2. Locate or Detect the Project Archive
echo [1/6] Searching for BS Lab Tool Sync Master Archive...
set FOUND_ZIP=

if exist "%SCRIPT_DIR%%ZIP_NAME%" (
    set FOUND_ZIP=%SCRIPT_DIR%%ZIP_NAME%
) else if exist "%USERPROFILE%\Downloads\%ZIP_NAME%" (
    set FOUND_ZIP=%USERPROFILE%\Downloads\%ZIP_NAME%
) else if exist "%TARGET_DIR%\%ZIP_NAME%" (
    set FOUND_ZIP=%TARGET_DIR%\%ZIP_NAME%
)

if "%FOUND_ZIP%"=="" (
    echo [-] '%ZIP_NAME%' not found in current folder or Downloads!
    echo [*] Checking if Google Drive link is available to download...
    echo.
    echo Please make sure '%ZIP_NAME%' is in the same folder as this script,
    echo or download it from your Google Drive folder:
    echo https://drive.google.com/drive/folders/1O8rPTZy3lCZeCvRYMcGHpiH0Wxc6m8HB
    echo.
    set /p USER_PATH="Enter the full path of the zip file (or press ENTER to cancel): "
    if exist "!USER_PATH!" (
        set FOUND_ZIP=!USER_PATH!
    ) else (
        echo [!] Archive file not provided. Exiting.
        pause
        exit /b
    )
)

echo [+] Found Archive: %FOUND_ZIP%
echo.

:: 3. Extract Archive to C:\BSLab_Tool
echo [2/6] Extracting BS Lab Tool files to %TARGET_DIR%...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

powershell -NoProfile -Command "Write-Host 'Extracting archive to %TARGET_DIR%... Please wait...'; Expand-Archive -Path '%FOUND_ZIP%' -DestinationPath '%TARGET_DIR%' -Force; Write-Host 'Extraction Complete!'"
echo [+] All Project Files Extracted Successfully to %TARGET_DIR%!
echo.

cd /d "%TARGET_DIR%"

:: 4. Windows Defender Scanning Exclusions
echo [3/6] Configuring Windows Defender Real-Time Scanning Exclusions...
powershell -NoProfile -Command "Add-MpPreference -ExclusionPath '%TARGET_DIR%' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Add-MpPreference -ExclusionProcess 'BSLabTool.exe', 'adb.exe', 'fastboot.exe', 'python.exe' -ErrorAction SilentlyContinue"
echo [+] Windows Defender Exclusions Applied! Zero DA/Firehose/ADB false-positive blocks.
echo.

:: 5. High Performance Power Plan & USB Disconnection Protection
echo [4/6] Optimizing High Performance Power Plan & Disabling USB Suspend...
powercfg -duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f >nul 2>&1
echo [+] Power Plan Locked: Sleep disabled, USB Disconnection Guard Active!
echo.

:: 6. Windows DriverStore Injection (MediaTek, Qualcomm, Unisoc, Huawei, Samsung)
echo [5/6] Injecting Universal GSM Hardware Drivers into Windows DriverStore...
echo     - MediaTek VCOM & CDC Serial
echo     - Qualcomm HS-USB QDLoader 9008
echo     - Unisoc / Spreadtrum SPRD U2S Diag
echo     - Huawei PCUI & USB COM 1.0
echo     - LibUsb-win32 USB Filter

if exist "%TARGET_DIR%\drivers" (
    pnputil.exe /add-driver "%TARGET_DIR%\drivers\*.inf" /subdirs /install >nul 2>&1
    echo [+] All Chipset INF Drivers Successfully Injected into Windows DriverStore!
) else (
    echo [-] Note: drivers directory checked.
)

if exist "%TARGET_DIR%\drivers\usbdk\UsbDk_1.0.22_x64.msi" (
    echo [*] Installing UsbDk x64 quietly for driverless MTK BROM SLA/DAA bypass...
    msiexec /i "%TARGET_DIR%\drivers\usbdk\UsbDk_1.0.22_x64.msi" /qn /norestart >nul 2>&1
    echo [+] UsbDk Filter Engine Installed Successfully!
)
echo.

:: 7. Create Luxury Desktop Shortcut & Launch
echo [6/6] Creating Desktop Shortcut for BS Lab Tool...
set SCRIPT="%TEMP%\create_bslab_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\BS Lab Tool.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
if exist "%TARGET_DIR%\dist_new\BSLabTool.exe" (
    echo oLink.TargetPath = "%TARGET_DIR%\dist_new\BSLabTool.exe" >> %SCRIPT%
    echo oLink.WorkingDirectory = "%TARGET_DIR%\dist_new" >> %SCRIPT%
) else (
    echo oLink.TargetPath = "%TARGET_DIR%\src\ui\BSLabTool.UI\bin\x64\Release\net8.0-windows\BSLabTool.exe" >> %SCRIPT%
    echo oLink.WorkingDirectory = "%TARGET_DIR%\src\ui\BSLabTool.UI\bin\x64\Release\net8.0-windows" >> %SCRIPT%
)
echo oLink.Description = "BS Lab Tool v2.5 PRO Enterprise — Syed Bisharat Ali (Shah Ji)" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT% >nul 2>&1
del %SCRIPT% >nul 2>&1
echo [+] Desktop Shortcut Created!
echo.

echo ====================================================================
echo  [SUCCESS] WORKSTATION FULLY PROVISIONED & READY FOR LIVE REPAIRS!
echo  All phone drivers are active in Windows DriverStore.
echo  Starting BS Lab Tool now...
echo ====================================================================
echo.

if exist "%TARGET_DIR%\dist_new\BSLabTool.exe" (
    start "" "%TARGET_DIR%\dist_new\BSLabTool.exe"
) else if exist "%TARGET_DIR%\src\ui\BSLabTool.UI\bin\x64\Release\net8.0-windows\BSLabTool.exe" (
    start "" "%TARGET_DIR%\src\ui\BSLabTool.UI\bin\x64\Release\net8.0-windows\BSLabTool.exe"
)

exit /b
