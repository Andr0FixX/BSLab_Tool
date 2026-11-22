# PowerShell Automated Build Script for BSLabCore.dll
# Milestone 1: Native Engine C++ Build Pipeline

[CmdletBinding()]
param(
    [switch]$ForceRebuild,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$NativeDir = Join-Path $ScriptRoot "src\native\BSLabCore"
$NativeSrcDir = Join-Path $NativeDir "src"
$NativeIncludeDir = Join-Path $NativeDir "include"

$TargetDllName = "BSLabCore.dll"
$BuildOutputDir = Join-Path $NativeDir "build_output"
$OutputDll = Join-Path $BuildOutputDir $TargetDllName

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   BSLabCore Native Build Pipeline (Milestone 1)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[*] Script Root      : $ScriptRoot"
Write-Host "[*] Native Source Dir: $NativeDir"

# Ensure output directory exists
if (-not (Test-Path $BuildOutputDir)) {
    New-Item -ItemType Directory -Path $BuildOutputDir -Force | Out-Null
}

$Sources = @(
    (Join-Path $NativeSrcDir "BSLabCore.cpp"),
    (Join-Path $NativeSrcDir "WinSerialPort.cpp"),
    (Join-Path $NativeSrcDir "MtkEngine.cpp"),
    (Join-Path $NativeSrcDir "DaParser.cpp"),
    (Join-Path $NativeSrcDir "GptParser.cpp"),
    (Join-Path $NativeSrcDir "MtkStreamFlasher.cpp"),
    (Join-Path $NativeSrcDir "MtkServiceEngine.cpp"),
    (Join-Path $NativeSrcDir "QcSahara.cpp"),
    (Join-Path $NativeSrcDir "QcFirehose.cpp"),
    (Join-Path $NativeSrcDir "QcEngine.cpp"),
    (Join-Path $NativeSrcDir "NativeTarReader.cpp"),
    (Join-Path $NativeSrcDir "NativeMd5.cpp"),
    (Join-Path $NativeSrcDir "SamsungPitReader.cpp"),
    (Join-Path $NativeSrcDir "SamsungModemEngine.cpp"),
    (Join-Path $NativeSrcDir "SamsungOdinEngine.cpp"),
    (Join-Path $NativeSrcDir "SpdBslProtocol.cpp"),
    (Join-Path $NativeSrcDir "SpdPacParser.cpp"),
    (Join-Path $NativeSrcDir "SpdFdlEngine.cpp"),
    (Join-Path $NativeSrcDir "UnisocEngine.cpp"),
    (Join-Path $NativeSrcDir "KirinRescueEngine.cpp"),
    (Join-Path $NativeSrcDir "HuaweiPcuiEngine.cpp"),
    (Join-Path $NativeSrcDir "HuaweiFastboot.cpp")
)

foreach ($src in $Sources) {
    if (-not (Test-Path $src)) {
        throw "Required source file not found: $src"
    }
}

# -------------------------------------------------------------
# Function: Discover Compiler
# -------------------------------------------------------------
function Find-Compiler {
    # 1. Check PATH for g++, clang++, cl
    $gccCmd = Get-Command g++ -ErrorAction SilentlyContinue
    if ($gccCmd) {
        return @{ Type = "GCC"; Path = $gccCmd.Source }
    }

    $clangCmd = Get-Command clang++ -ErrorAction SilentlyContinue
    if ($clangCmd) {
        return @{ Type = "Clang"; Path = $clangCmd.Source }
    }

    $clCmd = Get-Command cl -ErrorAction SilentlyContinue
    if ($clCmd) {
        return @{ Type = "MSVC"; Path = $clCmd.Source }
    }

    # 2. Check well-known MinGW / LLVM installation paths
    $candidateGccs = @(
        (Join-Path $ScriptRoot "tools\w64devkit\bin\g++.exe"),
        "C:\ProgramData\chocolatey\bin\g++.exe",
        "C:\ProgramData\chocolatey\lib\mingw\tools\install\mingw64\bin\g++.exe",
        "C:\tools\mingw64\bin\g++.exe",
        "C:\msys64\mingw64\bin\g++.exe",
        "C:\msys64\ucrt64\bin\g++.exe",
        "C:\MinGW\bin\g++.exe",
        "$env:LOCALAPPDATA\Programs\mingw64\bin\g++.exe"
    )

    foreach ($cand in $candidateGccs) {
        if (Test-Path $cand) {
            # Add containing directory to PATH so ld.exe and DLLs are resolved
            $binDir = Split-Path -Parent $cand
            $env:PATH = "$binDir;$env:PATH"
            return @{ Type = "GCC"; Path = $cand }
        }
    }

    # 3. Check for Visual Studio via vswhere or standard directories
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsInstallPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($vsInstallPath -and (Test-Path $vsInstallPath)) {
            $vcvars = Join-Path $vsInstallPath "VC\Auxiliary\Build\vcvars64.bat"
            if (Test-Path $vcvars) {
                return @{ Type = "MSVC_VCVARS"; Path = $vcvars }
            }
        }
    }

    return $null
}

$compilerInfo = Find-Compiler

if (-not $compilerInfo -and -not $SkipInstall) {
    Write-Host "[!] No C++ compiler found on PATH or standard locations." -ForegroundColor Yellow
    $chocoCmd = Get-Command choco -ErrorAction SilentlyContinue
    if ($chocoCmd) {
        Write-Host "[*] Chocolatey found. Installing MinGW (x64 GCC)..." -ForegroundColor Cyan
        & choco install mingw -y
        # Refresh PATH from Registry
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $compilerInfo = Find-Compiler
    } else {
        Write-Host "[!] Chocolatey is not installed. Unable to auto-install MinGW." -ForegroundColor Red
    }
}

if (-not $compilerInfo) {
    throw "Fatal: No compatible C++ compiler (MSVC, MinGW GCC, or Clang) could be found or installed."
}

Write-Host "[+] Using C++ Compiler: $($compilerInfo.Type) ($($compilerInfo.Path))" -ForegroundColor Green

# -------------------------------------------------------------
# Compilation
# -------------------------------------------------------------
Write-Host "[*] Compiling $TargetDllName as unmanaged x64 Release DLL..." -ForegroundColor Cyan

if ($compilerInfo.Type -in @("GCC", "Clang")) {
    $compilerExe = $compilerInfo.Path
    $compileArgs = @(
        "-std=c++20",
        "-O3",
        "-shared",
        "-DBSLABCORE_EXPORTS",
        "-I$NativeIncludeDir",
        "-I$NativeSrcDir",
        "-o", "$OutputDll",
        "-static-libgcc",
        "-static-libstdc++",
        "-Wl,--out-implib,$BuildOutputDir\libBSLabCore.a"
    )
    foreach ($s in $Sources) {
        $compileArgs += $s
    }
    $compileArgs += "-lkernel32"
    $compileArgs += "-luser32"
    $compileArgs += "-ladvapi32"
    $compileArgs += "-lsetupapi"

    Write-Host "[*] Executing: $compilerExe $($compileArgs -join ' ')"
    & $compilerExe @compileArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Compilation failed with exit code $LASTEXITCODE"
    }
}
elseif ($compilerInfo.Type -eq "MSVC") {
    $compileArgs = @(
        "/std:c++20",
        "/O2",
        "/MD",
        "/LD",
        "/DBSLABCORE_EXPORTS",
        "/I`"$NativeIncludeDir`"",
        "/I`"$NativeSrcDir`"",
        "/Fe:`"$OutputDll`""
    )
    foreach ($s in $Sources) {
        $compileArgs += "`"$s`""
    }
    $compileArgs += "kernel32.lib"
    $compileArgs += "user32.lib"
    $compileArgs += "advapi32.lib"
    $compileArgs += "setupapi.lib"

    $process = Start-Process -FilePath $compilerInfo.Path -ArgumentList $compileArgs -WorkingDirectory $BuildOutputDir -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -ne 0) {
        throw "MSVC compilation failed with exit code $($process.ExitCode)"
    }
}
elseif ($compilerInfo.Type -eq "MSVC_VCVARS") {
    $vcvarsBat = $compilerInfo.Path
    $srcList = ($Sources | ForEach-Object { "`"$_`"" }) -join " "
    $cmdString = "call `"$vcvarsBat`" && cl.exe /std:c++20 /O2 /MD /LD /DBSLABCORE_EXPORTS /I`"$NativeIncludeDir`" /I`"$NativeSrcDir`" /Fe:`"$OutputDll`" $srcList kernel32.lib user32.lib advapi32.lib setupapi.lib"
    
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $cmdString" -WorkingDirectory $BuildOutputDir -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -ne 0) {
        throw "MSVC vcvars compilation failed with exit code $($process.ExitCode)"
    }
}

if (-not (Test-Path $OutputDll)) {
    throw "Compilation completed but output file not found at: $OutputDll"
}

$fileInfo = Get-Item $OutputDll
$fileHash = (Get-FileHash -Path $OutputDll -Algorithm SHA256).Hash
Write-Host "[+] Build SUCCESSFUL!" -ForegroundColor Green
Write-Host "    File Size: $($fileInfo.Length) bytes"
Write-Host "    SHA-256  : $fileHash"

# -------------------------------------------------------------
# Deployment Targets
# -------------------------------------------------------------
$DeployTargets = @(
    (Join-Path $ScriptRoot "src\ui\BSLabTool.UI\BSLabCore.dll"),
    (Join-Path $ScriptRoot "src\ui\BSLabTool.UI\bin\Release\net8.0-windows\BSLabCore.dll"),
    (Join-Path $ScriptRoot "dist_new\BSLabCore.dll")
)

Write-Host "`n[*] Deploying BSLabCore.dll to target destinations..." -ForegroundColor Cyan

foreach ($target in $DeployTargets) {
    $targetDir = Split-Path -Parent $target
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    Copy-Item -Path $OutputDll -Destination $target -Force
    Write-Host "    -> Deployed to: $target" -ForegroundColor Green
}

Write-Host "`n[+] Native build and deployment completed with 0 errors!" -ForegroundColor Green
