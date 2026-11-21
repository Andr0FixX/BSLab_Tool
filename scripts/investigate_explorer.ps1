$p = Get-CimInstance Win32_Process -Filter "ProcessId = 6200"
if ($p) {
    Write-Host "Found PID 6200: $($p.Name)"
    Write-Host "ExecutablePath: $($p.ExecutablePath)"
    Write-Host "CommandLine: $($p.CommandLine)"
    $owner = Invoke-CimMethod -InputObject $p -MethodName GetOwner
    Write-Host "Owner: $($owner.Domain)\$($owner.User)"
} else {
    Write-Host "PID 6200 not found. Checking all explorer processes..."
    Get-CimInstance Win32_Process -Filter "Name LIKE '%explorer%'" | Select-Object ProcessId, Name, ExecutablePath, CommandLine | Format-List
}
