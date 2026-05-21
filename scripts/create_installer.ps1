<#
.SYNOPSIS
    Builds the PulpitInk Windows Setup Installer EXE using Inno Setup (ISCC).

.DESCRIPTION
    1. Detects the version from pyproject.toml if not passed via -Version.
    2. Verifies that dist/PulpitInk/ exists (PyInstaller output).
    3. Locates Inno Setup's command line compiler (ISCC.exe) in PATH or standard Program Files locations.
    4. Compiles scripts/pulpit-ink.iss into dist/PulpitInk_Setup_{version}.exe.
#>

[CmdletBinding()]
param(
    [string]$Version
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DistDir = Join-Path $RepoRoot "dist"
$BuildDir = Join-Path $DistDir "PulpitInk"
$IssScript = Join-Path $PSScriptRoot "pulpit-ink.iss"

# 1. Verify build directory exists
if (-not (Test-Path $BuildDir)) {
    throw "PyInstaller build directory not found at $BuildDir. Run scripts/build_windows.ps1 first."
}

# 2. Resolve version
if (-not $Version) {
    $pyproject = Get-Content (Join-Path $RepoRoot "pyproject.toml") -Raw
    $match = [regex]::Match($pyproject, '(?m)^\s*version\s*=\s*"([^"]+)"')
    if (-not $match.Success) {
        throw "Could not detect version from pyproject.toml. Pass -Version explicitly."
    }
    $Version = $match.Groups[1].Value
}

Write-Host "PulpitInk Installer Builder - Version $Version" -ForegroundColor Cyan

# 3. Locate ISCC.exe
$IsccPath = $null
$CommonLocations = @(
    "iscc",
    "iscc.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

foreach ($loc in $CommonLocations) {
    $resolved = Get-Command $loc -ErrorAction SilentlyContinue
    if ($resolved) {
        $IsccPath = $resolved.Source
        break
    }
    if (Test-Path $loc) {
        $IsccPath = $loc
        break
    }
}

if (-not $IsccPath) {
    Write-Host ""
    Write-Host "WARNING: Inno Setup command-line compiler (ISCC.exe) not found!" -ForegroundColor Yellow
    Write-Host "To automatically build the setup installer, please download and install Inno Setup:" -ForegroundColor Yellow
    Write-Host "👉 https://jrsoftware.org/isdownload.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The Inno Setup script was successfully created at:" -ForegroundColor Yellow
    Write-Host "   $IssScript" -ForegroundColor Yellow
    Write-Host "You can manually compile this script using the Inno Setup GUI after installing it." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found Inno Setup Compiler at: $IsccPath" -ForegroundColor Green
Write-Host "Compiling setup installer..." -ForegroundColor Cyan

# Run ISCC
& $IsccPath "/DMyAppVersion=$Version" $IssScript

$ExpectedInstaller = Join-Path $DistDir "PulpitInk_Setup_$Version.exe"
if (Test-Path $ExpectedInstaller) {
    Write-Host ""
    Write-Host "Successfully generated installer setup:" -ForegroundColor Green
    Write-Host "   $ExpectedInstaller" -ForegroundColor Green
} else {
    throw "Installer generation seemed to succeed but target file not found at $ExpectedInstaller"
}
