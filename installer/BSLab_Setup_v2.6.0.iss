; ==============================================================================
; BS Lab Tool v2.6.0 PRO - Enterprise Official Windows Master Installer Script
; Features:
;   - Cloud User Profile, Server Credits & Reseller Hub (CloudResellerPortalWindow)
;   - Direct ISP eMMC / UFS JTAG Flasher & Live Voltage Guard (DirectIspJtagFlasherWindow)
;   - Virtual Phone Hardware Simulator & Loopback Bus (VirtualDeviceSimulatorWindow)
;   - High-Speed Stock Firmware Downloader & ROM Center (OfficialFirmwareDownloaderWindow)
;   - Multi-Language Localization Engine: Urdu, Arabic & English (LocalizationEngine)
;   - Workshop POS, Repair Job Ticket & 80mm Thermal Invoices (WorkshopPosBillingWindow)
;   - Samsung Knox Guard (KG) & PayJoy MDM Killer Suite (SamsungKnoxGuardSuiteWindow)
;   - Cryptographic HWID KeyGen & License Activation (AdminKeyGenWindow & LicensingEngine)
;   - Advanced GPT Partition Manager & Raw Sector Dumper/Flasher
;   - Real-Time Live USB Hex Packet Sniffer & Protocol Radar
;   - In-App Auto-Updater Engine & GitHub Release Synchronizer
;   - 4K Interactive Motherboard TestPoint & ISP Pinout Explorer
;   - Native C++20 Core Subsystem Integration (BSLabCore.dll)
;   - Automated Driver Deployment: MediaTek, Qualcomm 9008, Unisoc, Samsung, Huawei & UsbDk 64-bit
;   - Automated Windows Defender Whitelisting & Authenticode Trusted Publisher Registration
; ==============================================================================

#define MyAppName "BS Lab Tool PRO"
#define MyAppVersion "2.6.1"
#define MyAppPublisher "BS Lab Tool Team"
#define MyAppURL "https://andr0fixx.github.io/BSLab_Tool/"
#define MyAppExeName "BSLabTool.exe"

[Setup]
AppId={{5E97C224-2F6B-48F8-9D27-E8C2B3F78810}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=C:\BSLab_Tool\installer_output
OutputBaseFilename=BSLab_Tool_PRO_v2.6.1_Setup
SetupIconFile=C:\BSLab_Tool\resources\icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
InternalCompressLevel=ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; --- Mandatory Password Protection (AES-256) ---
Password=BsLab
Encryption=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "installdrivers"; Description: "Install & Register USB Drivers (MediaTek, Qualcomm 9008, Unisoc, Samsung, Huawei & UsbDk)"; GroupDescription: "Hardware Driver Subsystems:"; Flags: checkedonce
Name: "installrootcert"; Description: "Register Official BS Lab Authenticode Security Certificate (Removes Windows 'Unknown Publisher' warning)"; GroupDescription: "Windows Security & Clean Installation:"; Flags: checkedonce
Name: "whitelistedefender"; Description: "Auto-whitelist BS Lab Tool in Windows Defender (Prevents false-positive flags on drivers, loaders & adb)"; GroupDescription: "Windows Security & Clean Installation:"; Flags: checkedonce

[Files]
; Public Authenticode Certificate for zero-warning client registration
Source: "C:\BSLab_Tool\resources\certs\BSLabTool_RootCA.cer"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

; Main application binaries, native C++20 core, resources, databases, docs, and drivers
Source: "C:\BSLab_Tool\dist_release_v2.5\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\icons\app_icon.ico"
Name: "{autoprograms}\{#MyAppName}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\icons\app_icon.ico"; Tasks: desktopicon

[Run]
; Silent automated driver deployment via pnputil and msiexec
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\mtk\*.inf"" /install"; StatusMsg: "Configuring MediaTek USB VCOM & Preloader Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\qualcomm\*.inf"" /install"; StatusMsg: "Configuring Qualcomm HS-USB QDLoader 9008 Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\unisoc\*.inf"" /install"; StatusMsg: "Configuring Unisoc / Spreadtrum USB Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\samsung\*.inf"" /install"; StatusMsg: "Configuring Samsung USB Modem Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\huawei\*.inf"" /install"; StatusMsg: "Configuring Huawei USB COM & Handset Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "msiexec.exe"; Parameters: "/i ""{app}\drivers\usbdk\UsbDk_1.0.22_x64.msi"" /quiet /norestart"; StatusMsg: "Installing UsbDk 64-bit Low-Level USB Capture Driver..."; Flags: runhidden; Tasks: installdrivers

; Automated Authenticode Certificate Registration (TrustedPublisher and Root)
Filename: "certutil.exe"; Parameters: "-addstore ""TrustedPublisher"" ""{tmp}\BSLabTool_RootCA.cer"""; StatusMsg: "Registering Official Authenticode Certificate in Trusted Publishers..."; Flags: runhidden; Tasks: installrootcert
Filename: "certutil.exe"; Parameters: "-addstore ""Root"" ""{tmp}\BSLabTool_RootCA.cer"""; StatusMsg: "Registering Official Authenticode Certificate in Trusted Root..."; Flags: runhidden; Tasks: installrootcert

; Automated Windows Defender Exclusion to prevent false-positive virus detections
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionPath '{app}' -ExclusionProcess 'BSLabTool.exe','BSLabUpdater.exe','adb.exe','fastboot.exe' -ErrorAction SilentlyContinue"""; StatusMsg: "Configuring Windows Defender Antivirus Whitelist..."; Flags: runhidden; Tasks: whitelistedefender

; Windows Firewall Bridge Rule
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""BS Lab Tool PRO"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes"; StatusMsg: "Configuring Windows Firewall communication rules..."; Flags: runhidden

; Post-install launch option
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Clean up Windows Defender and Firewall rules on uninstall
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Remove-MpPreference -ExclusionPath '{app}' -ErrorAction SilentlyContinue"""; Flags: runhidden
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""BS Lab Tool PRO"""; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backups"
Type: filesandordirs; Name: "{app}\dumps"
Type: filesandordirs; Name: "{app}\workspace"
Type: filesandordirs; Name: "{app}\screenshots"
Type: files; Name: "{app}\crash.log"
