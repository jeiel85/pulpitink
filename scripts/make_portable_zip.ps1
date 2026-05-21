<#
.SYNOPSIS
    Bundles the PyInstaller output into PulpitInk_Portable_{version}.zip.

.DESCRIPTION
    Expects dist/PulpitInk/ to exist (produced by PyInstaller running
    pulpit-ink.spec). Resolves the project version from pyproject.toml
    unless overridden via -Version, then writes the ZIP to dist/.

    The archive intentionally excludes FFmpeg binaries and STT model
    files — users must supply those themselves (see PORTABLE-README.txt
    placed alongside the executable).
#>

[CmdletBinding()]
param(
    [string]$Version
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DistDir = Join-Path $RepoRoot "dist"
$BuildDir = Join-Path $DistDir "PulpitInk"

if (-not (Test-Path $BuildDir)) {
    throw "PyInstaller build directory not found at $BuildDir. Run scripts/build_windows.ps1 first."
}

if (-not $Version) {
    $pyproject = Get-Content (Join-Path $RepoRoot "pyproject.toml") -Raw
    $match = [regex]::Match($pyproject, '(?m)^\s*version\s*=\s*"([^"]+)"')
    if (-not $match.Success) {
        throw "Could not detect version from pyproject.toml. Pass -Version explicitly."
    }
    $Version = $match.Groups[1].Value
}

$ArchiveName = "PulpitInk_Portable_$Version.zip"
$ArchivePath = Join-Path $DistDir $ArchiveName

if (Test-Path $ArchivePath) { Remove-Item $ArchivePath -Force }

# Drop the README + license alongside the executable so the ZIP is
# self-explanatory even when extracted into an arbitrary folder.
Copy-Item -Force (Join-Path $RepoRoot "LICENSE") (Join-Path $BuildDir "LICENSE.txt")
Copy-Item -Force (Join-Path $RepoRoot "THIRD_PARTY_NOTICES.md") (Join-Path $BuildDir "THIRD_PARTY_NOTICES.md")

$readmePath = Join-Path $BuildDir "PORTABLE-README.txt"
@"
설교필기 (PulpitInk) Portable $Version

이 ZIP은 FFmpeg 바이너리와 STT 모델 파일을 포함하지 않습니다.

1. FFmpeg
   - https://www.gyan.dev/ffmpeg/builds/ 또는 https://github.com/BtbN/FFmpeg-Builds
   - ffmpeg.exe, ffprobe.exe 를 이 폴더 또는 PATH 에 두세요.

2. STT 모델
   - faster-whisper 가 처음 실행 시 huggingface 에서 자동으로 다운로드합니다.
   - 오프라인 환경에서는 pulpit-ink settings 명령으로 model_cache_dir 을 지정하세요.

3. 실행
   - PulpitInk.exe (GUI)
   - pulpit-ink (CLI) — 별도 wheel 설치 또는 ``python -m pulpit_ink.cli.main`` 사용

자세한 내용은 docs/release/release-checklist.md 와 THIRD_PARTY_NOTICES.md 를 참고하세요.
"@ | Set-Content -Path $readmePath -Encoding UTF8

Compress-Archive -Path (Join-Path $BuildDir "*") -DestinationPath $ArchivePath -CompressionLevel Optimal

Write-Host "Created $ArchivePath" -ForegroundColor Green
