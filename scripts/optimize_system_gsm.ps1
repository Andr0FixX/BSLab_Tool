# BS LAB TOOL - ENTERPRISE WORKSTATION GSM OPTIMIZATION SCRIPT
# Target: Zero-Interruption Flashing, Windows Defender Exclusion, Drivers and Cache

Write-Host "=============================================================="
Write-Host "BS LAB TOOL - SYSTEM AND HARDWARE OPTIMIZER ENGINE"
Write-Host "Syed Bisharat Ali | Hamza Block, Arif Center, Hall Road, Lahore"
Write-Host "=============================================================="

# STEP 1: WINDOWS DEFENDER EXCLUSIONS
Write-Host "`n[STEP 1] Configuring Windows Defender Exclusions..."

$exclusionPaths = @(
    "C:\BSLab_Tool",
    "C:\platform-tools",
    "C:\Program Files\dotnet"
)

foreach ($p in $exclusionPaths) {
    if (Test-Path $p) {
        try {
            Add-MpPreference -ExclusionPath $p -ErrorAction SilentlyContinue
            Write-Host "  [+] Excluded Folder: $p"
        } catch {
            Write-Host "  [-] Failed to exclude $p"
        }
    }
}

$exclusionProcesses = @("BSLabTool.exe", "adb.exe", "fastboot.exe", "python.exe")
foreach ($proc in $exclusionProcesses) {
    try {
        Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
        Write-Host "  [+] Excluded Process: $proc"
    } catch {
        Write-Host "  [-] Failed to exclude process $proc"
    }
}

# STEP 2: POWER AND SLEEP PLAN (ZERO-INTERRUPTION FLASHING)
Write-Host "`n[STEP 2] Configuring High-Performance Power Plan and USB Stability..."

# Set High Performance scheme (8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
Write-Host "  [+] Active Power Scheme: High Performance"

# Disable Standby and Hibernate timeouts (Never sleep during EDL or Flashing)
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0
powercfg -change -hibernate-timeout-ac 0
powercfg -change -hibernate-timeout-dc 0
Write-Host "  [+] Sleep / Standby / Hibernate: DISABLED (Always Awake)"

# Disable USB Selective Suspend
powercfg /setacvalueindex scheme_current 2a737441-1930-4402-8687-b6e4478729bf 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setdcvalueindex scheme_current 2a737441-1930-4402-8687-b6e4478729bf 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
# Disable PCI Express Link State Power Management
powercfg /setacvalueindex scheme_current 501a4d13-42af-4429-9e86-e8eb7312b88e ee12f58e-7053-40f4-ab87-04c66b086337 0
powercfg /setdcvalueindex scheme_current 501a4d13-42af-4429-9e86-e8eb7312b88e ee12f58e-7053-40f4-ab87-04c66b086337 0
powercfg /setactive scheme_current
Write-Host "  [+] USB Selective Suspend: DISABLED (Zero Port Drop Protection)"
Write-Host "  [+] PCIe Link Power Management: MAXIMUM PERFORMANCE"

# STEP 3: DRIVERS AND HARDWARE VERIFICATION
Write-Host "`n[STEP 3] Verifying GSM and Chipset Drivers in DriverStore..."

$drivers = pnputil /enum-drivers
$checkChips = @(
    @{ Name = "MediaTek USB VCOM / DA"; Patterns = @("cdc-acm", "mediatek") },
    @{ Name = "Qualcomm EDL 9008 (QCSER)"; Patterns = @("qcser", "qcfilter", "qdbusb") },
    @{ Name = "Huawei PCUI / Manufacture"; Patterns = @("hw_usbvcom", "diagswitchdrv", "hw_ctrlfakedev") },
    @{ Name = "Unisoc / Spreadtrum (SPRD)"; Patterns = @("sprdvcom", "rdavcom") },
    @{ Name = "Samsung Mobile USB / Modem"; Patterns = @("ssadbus", "ssadsdm", "ssudmdm") }
)

foreach ($c in $checkChips) {
    $found = $false
    foreach ($pat in $c.Patterns) {
        if ($drivers -match $pat) {
            $found = $true
            break
        }
    }
    if ($found) {
        Write-Host "  [+] $($c.Name) : REGISTERED AND READY"
    } else {
        Write-Host "  [!] $($c.Name) : Not detected in DriverStore"
    }
}

# STEP 4: SYSTEM ENVIRONMENT PATH CONFIGURATION
Write-Host "`n[STEP 4] Configuring System Environment PATH..."

$targetPaths = @(
    "C:\BSLab_Tool\resources\platform-tools",
    "C:\Program Files\dotnet"
)

$currentMachinePath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$machinePathArray = New-Object System.Collections.ArrayList
foreach ($p in $currentMachinePath.Split(';')) {
    $trimmed = $p.Trim()
    if ($trimmed -ne "" -and -not $machinePathArray.Contains($trimmed)) {
        [void]$machinePathArray.Add($trimmed)
    }
}

$pathModified = $false
foreach ($tp in $targetPaths) {
    if (Test-Path $tp) {
        if (-not $machinePathArray.Contains($tp)) {
            [void]$machinePathArray.Add($tp)
            $pathModified = $true
            Write-Host "  [+] Added to System PATH: $tp"
        } else {
            Write-Host "  [+] Already in System PATH: $tp"
        }
    }
}

if ($pathModified) {
    $newMachinePath = ($machinePathArray.ToArray() -join ';')
    [Environment]::SetEnvironmentVariable("PATH", $newMachinePath, "Machine")
    Write-Host "  [+] System Environment Variable PATH updated successfully."
}

# STEP 5: DISK AND TEMP CACHE CLEANUP
Write-Host "`n[STEP 5] Cleaning Temp Files, Dumps and Caches..."

$tempLocations = @(
    "$env:LOCALAPPDATA\Temp",
    "C:\Windows\Temp",
    "C:\ProgramData\Microsoft\Windows\WER\ReportArchive",
    "C:\ProgramData\Microsoft\Windows\WER\ReportQueue"
)

$totalCleanedBytes = 0
$cleanedFilesCount = 0

foreach ($tl in $tempLocations) {
    if (Test-Path $tl) {
        Write-Host "  Cleaning: $tl..."
        $items = Get-ChildItem -Path $tl -Recurse -Force -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            if (-not $item.PSIsContainer) {
                try {
                    $sz = $item.Length
                    Remove-Item -Path $item.FullName -Force -ErrorAction Stop
                    $totalCleanedBytes += $sz
                    $cleanedFilesCount++
                } catch {
                    # Skip files locked by running apps
                }
            }
        }
    }
}

$cleanedMB = [math]::Round($totalCleanedBytes / 1MB, 2)
Write-Host "  [+] Cleaned $cleanedFilesCount temporary files ($cleanedMB MB freed)!"

# Remove debug crash.log if present
$crashLog = "C:\BSLab_Tool\src\ui\BSLabTool.UI\bin\Debug\net8.0-windows\crash.log"
if (Test-Path $crashLog) {
    Remove-Item $crashLog -Force -ErrorAction SilentlyContinue
    Write-Host "  [+] Removed stale crash.log"
}

Write-Host "`n=============================================================="
Write-Host "SUCCESS: ALL 5 GSM OPTIMIZATION MODULES COMPLETED!"
Write-Host "=============================================================="
