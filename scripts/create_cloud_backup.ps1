# BS Lab Tool - Cloud Backup Generator
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\BSLab_Tool\backups\cloud_export"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$zipPath = Join-Path $backupDir "BSLab_Tool_Full_Backup_$timestamp.zip"
Write-Host "Creating archive: $zipPath"

$sourceItems = @(
    "C:\BSLab_Tool\src",
    "C:\BSLab_Tool\resources",
    "C:\BSLab_Tool\config",
    "C:\BSLab_Tool\scripts",
    "C:\BSLab_Tool\engines",
    "C:\BSLab_Tool\utils",
    "C:\BSLab_Tool\tools",
    "C:\BSLab_Tool\core",
    "C:\BSLab_Tool\main.py",
    "C:\BSLab_Tool\Launch_BSLab_PRO.bat",
    "C:\BSLab_Tool\BSLab_Complete_Roadmap.html"
)

# Verify items exist before compressing
$validItems = $sourceItems | Where-Object { Test-Path $_ }

Compress-Archive -Path $validItems -DestinationPath $zipPath -CompressionLevel Optimal -Force

if (Test-Path $zipPath) {
    $item = Get-Item $zipPath
    Write-Host "SUCCESS: Archive created successfully."
    Write-Host "File: $($item.FullName)"
    Write-Host "Size: $([math]::Round($item.Length / 1MB, 2)) MB"
    Write-Host "Timestamp: $timestamp"
    # Output path for gdrive to consume
    Write-Output $item.FullName
} else {
    Write-Error "Failed to generate backup archive."
}
