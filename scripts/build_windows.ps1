<#
.SYNOPSIS
    SermonScript Windows portable build (PyInstaller + ZIP).

.DESCRIPTION
    1. Installs dev + runtime dependencies into the current Python environment.
    2. Runs ruff and pytest as a smoke gate (skipped with -SkipChecks).
    3. Builds the PyInstaller bundle from sermonscript.spec.
    4. Calls scripts/make_portable_zip.ps1 to produce
       dist/SermonScript_Portable_{version}.zip.

    FFmpeg binaries and STT model files are intentionally NOT bundled. See
    docs/release/release-checklist.md and THIRD_PARTY_NOTICES.md for the
    user-facing instructions on supplying them.

.PARAMETER SkipChecks
    Skip ruff + pytest before building.

.PARAMETER Version
    Override the version string baked into the ZIP filename. Defaults to
    the project version exposed by ``python -c "import sermonscript"``.
#>

[CmdletBinding()]
param(
    [switch]$SkipChecks,
    [string]$Version
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

Write-Host "[1/5] Installing dependencies" -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e ".[gui,reference]"
python -m pip install pyinstaller

if (-not $SkipChecks) {
    Write-Host "[2/5] ruff check" -ForegroundColor Cyan
    python -m ruff check .

    Write-Host "[3/5] pytest" -ForegroundColor Cyan
    python -m pytest
} else {
    Write-Host "[2-3/5] Skipping ruff + pytest (--SkipChecks)" -ForegroundColor Yellow
}

Write-Host "[4/5] PyInstaller build" -ForegroundColor Cyan
$env:SERMONSCRIPT_ROOT = "$RepoRoot"
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist/SermonScript") { Remove-Item "dist/SermonScript" -Recurse -Force }
python -m PyInstaller --clean --noconfirm sermonscript.spec

Write-Host "[5/5] Packaging portable ZIP" -ForegroundColor Cyan
$portableArgs = @{}
if ($Version) { $portableArgs["Version"] = $Version }
& (Join-Path $PSScriptRoot "make_portable_zip.ps1") @portableArgs

Write-Host "Build complete." -ForegroundColor Green
