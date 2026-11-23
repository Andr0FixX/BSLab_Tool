<#
.SYNOPSIS
    Generates an official Authenticode Code Signing Certificate for BS Lab Tool PRO.
    Exports public .cer and private .pfx for signing releases and client whitelisting.
#>
param(
    [string]$CertDir = "resources\certs",
    [string]$Password = "BsLab2026!Security"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CertDir)) {
    New-Item -ItemType Directory -Path $CertDir -Force | Out-Null
}

$cerPath = Join-Path $CertDir "BSLabTool_RootCA.cer"
$pfxPath = Join-Path $CertDir "BSLabTool_CodeSign.pfx"

Write-Host "[*] Creating Self-Signed Authenticode Code Signing Certificate..." -ForegroundColor Cyan

# Check if certificate already exists in Cert store
$existing = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -like "*BS Lab Tool PRO*" }

if ($existing) {
    Write-Host "[+] Found existing certificate in CurrentUser\My: $($existing[0].Thumbprint)" -ForegroundColor Green
    $cert = $existing[0]
} else {
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject "CN=BS Lab Tool PRO (Syed Bisharat Ali), O=BS Lab Team, L=Lahore, S=Punjab, C=PK" `
        -FriendlyName "BS Lab Tool PRO Authenticode Certificate" `
        -HashAlgorithm "SHA256" `
        -KeyLength 2048 `
        -KeySpec Signature `
        -KeyUsage DigitalSignature `
        -KeyExportPolicy Exportable `
        -NotBefore (Get-Date).AddDays(-1) `
        -NotAfter (Get-Date).AddYears(10) `
        -CertStoreLocation "Cert:\CurrentUser\My"

    Write-Host "[+] Generated new certificate: $($cert.Thumbprint)" -ForegroundColor Green
}

# Export Public Certificate (.cer)
Export-Certificate -Cert $cert -FilePath $cerPath -Force | Out-Null
Write-Host "[+] Exported Public Certificate (.cer): $cerPath" -ForegroundColor Green

# Export PFX Container (.pfx)
$secPassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $secPassword -Force | Out-Null
Write-Host "[+] Exported PKCS#12 Container (.pfx): $pfxPath" -ForegroundColor Green

# Install Public Certificate locally to TrustedPublisher and Root for instant zero-warning testing
try {
    $storePub = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPublisher", "CurrentUser"
    $storePub.Open("ReadWrite")
    $storePub.Add($cert)
    $storePub.Close()
    Write-Host "[+] Certificate registered in CurrentUser\TrustedPublisher store." -ForegroundColor Green
} catch {
    Write-Warning "Could not add to TrustedPublisher store: $_"
}

Write-Host "[✓] Authenticode Certificate Suite successfully generated!" -ForegroundColor Cyan
