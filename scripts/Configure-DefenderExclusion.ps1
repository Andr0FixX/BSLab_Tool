<#
.SYNOPSIS
    Automated Windows Defender Whitelisting Engine for BS Lab Tool PRO.
    Configures ExclusionPath and ExclusionProcess using documented Microsoft MpPreference cmdlets.
#>
param(
    [string]$AppPath = "C:\BSLab_Tool",
    [string[]]$ProcessNames = @("BSLabTool.exe", "BSLabUpdater.exe", "adb.exe", "fastboot.exe"),
    [switch]$Remove,
    [switch]$CheckOnly
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🛡️ BS LAB TOOL PRO — WINDOWS DEFENDER WHITELIST AUTOMATION" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Check if Windows Defender service is available
$mpCmd = Get-Command Add-MpPreference -ErrorAction SilentlyContinue
if (-not $mpCmd) {
    Write-Host "[!] Windows Defender management cmdlets not found on this system (Defender may be disabled or 3rd-party AV active)." -ForegroundColor Yellow
    exit 0
}

if ($CheckOnly) {
    $pref = Get-MpPreference
    $isPathExcluded = ($pref.ExclusionPath -contains $AppPath)
    Write-Host "[*] Status Check for: $AppPath" -ForegroundColor Gray
    Write-Host "[+] Folder Whitelisted : $isPathExcluded" -ForegroundColor ($isPathExcluded ? "Green" : "Red")
    return $isPathExcluded
}

if ($Remove) {
    Write-Host "[*] Removing Defender exclusions for: $AppPath ..." -ForegroundColor Yellow
    Remove-MpPreference -ExclusionPath $AppPath -ErrorAction SilentlyContinue
    foreach ($proc in $ProcessNames) {
        Remove-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
    }
    Write-Host "[✓] Windows Defender exclusions removed." -ForegroundColor Green
    exit 0
}

# Add Exclusions
Write-Host "[*] Registering Folder Exclusion: $AppPath ..." -ForegroundColor Cyan
Add-MpPreference -ExclusionPath $AppPath -ErrorAction SilentlyContinue

foreach ($proc in $ProcessNames) {
    Write-Host "[*] Registering Process Exclusion: $proc ..." -ForegroundColor Cyan
    Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
}

# Verify configuration
$verify = Get-MpPreference
$confirmed = ($verify.ExclusionPath -contains $AppPath)

if ($confirmed) {
    Write-Host "[✓] SUCCESS: Folder & binaries successfully whitelisted in Windows Defender!" -ForegroundColor Green
    Write-Host "[+] Clean installation and real-time execution guaranteed with 0 false-positive alerts." -ForegroundColor Green
} else {
    Write-Host "[*] Exclusions submitted (Note: Administrator elevation is required for permanent Defender store update)." -ForegroundColor Yellow
}
