<#
.SYNOPSIS
    Automated Authenticode Signing Script for BS Lab Tool PRO Binaries.
    Applies SHA256 digital signature + RFC 3161 Timestamping.
#>
param(
    [string[]]$Targets = @(
        "dist_release_v2.5\BSLabTool.exe",
        "dist_release_v2.5\BSLabCore.dll",
        "dist_release_v2.5\BSLabUpdater.exe",
        "dist_new\BSLabTool.exe",
        "dist_new\BSLabCore.dll",
        "dist_new\BSLabUpdater.exe",
        "installer_output\BSLab_Tool_PRO_v2.5_Setup.exe"
    ),
    [string]$PfxPath = "resources\certs\BSLabTool_CodeSign.pfx",
    [string]$PfxPassword = "BsLab2026!Security",
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Continue"

Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "⚡ BS LAB TOOL PRO — AUTOMATED AUTHENTICODE SIGNING SUITE" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Load Certificate from CurrentUser\My first, or PFX non-interactively
$cert = $null
$existing = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -like "*BS Lab Tool PRO*" }

if ($existing) {
    $cert = $existing[0]
    Write-Host "[+] Loaded certificate from CurrentUser\My: $($cert.Thumbprint)" -ForegroundColor Green
} elseif (Test-Path $PfxPath) {
    Write-Host "[*] Loading certificate from PFX: $PfxPath" -ForegroundColor Gray
    try {
        $flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable -bor [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::PersistKeySet
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPassword, $flags)
    } catch {
        Write-Warning "Failed loading PFX: $_"
    }
}

if (-not $cert) {
    Write-Error "[-] Code signing certificate could not be found! Run scripts\Generate-BSLabCertificate.ps1 first."
    exit 1
}

Write-Host "[+] Signing Authority : $($cert.Subject)" -ForegroundColor Green
Write-Host "[+] Thumbprint        : $($cert.Thumbprint)" -ForegroundColor Green
Write-Host "[+] Timestamp Server  : $TimestampServer" -ForegroundColor Green
Write-Host "──────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

$signedCount = 0
$failCount = 0

foreach ($target in $Targets) {
    if (Test-Path $target) {
        Write-Host "[*] Signing: $target ..." -NoNewline
        try {
            $sig = Set-AuthenticodeSignature -FilePath $target -Certificate $cert -HashAlgorithm SHA256 -TimestampServer $TimestampServer -ErrorAction Stop
            if ($sig.Status -eq "Valid" -or $sig.Status -eq "UnknownError") {
                Write-Host " [SUCCESS - $($sig.Status)]" -ForegroundColor Green
                $signedCount++
            } else {
                # Fallback without timestamp if network/firewall blocks timestamp server
                Write-Host " [RETRY without TS]" -ForegroundColor Yellow -NoNewline
                $sig2 = Set-AuthenticodeSignature -FilePath $target -Certificate $cert -HashAlgorithm SHA256 -ErrorAction Stop
                Write-Host " [$($sig2.Status)]" -ForegroundColor Green
                $signedCount++
            }
        } catch {
            Write-Host " [FAILED: $_]" -ForegroundColor Red
            $failCount++
        }
    } else {
        Write-Host "[-] Skipped (Not found): $target" -ForegroundColor DarkGray
    }
}

Write-Host "──────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "[✓] Authenticode Signing Finished: $signedCount succeeded, $failCount failed." -ForegroundColor Cyan
