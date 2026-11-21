Get-MpPreference | Select-Object ExclusionPath, ExclusionProcess | Format-List | Out-File -FilePath "C:\BSLab_Tool\scripts\defender_verified.log" -Encoding utf8
