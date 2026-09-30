# Download FFmpeg essentials ke folder bin/ (tanpa install PATH)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$binDir = Join-Path $root "bin"
$zipPath = Join-Path $env:TEMP "ffmpeg-9.0.2-essentials_build.zip"
$extractDir = Join-Path $env:TEMP "ffmpeg-extract"
$url = "https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.zip"

New-Item -ItemType Directory -Force -Path $binDir | Out-Null

Write-Host "Download FFmpeg essentials dari GitHub..."
curl.exe -L --retry 3 --retry-all-errors -o $zipPath $url
if ($LASTEXITCODE -ne 0) { throw "Download gagal" }

$zip = Get-Item $zipPath
if ($zip.Length -lt 10000000) { throw "File zip terlalu kecil: $($zip.Length) bytes" }

if (Test-Path $extractDir) {
    Remove-Item $extractDir -Recurse -Force
}

Write-Host "Extract zip..."
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

$ffmpeg = Get-ChildItem -Path $extractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
$ffprobe = Get-ChildItem -Path $extractDir -Recurse -Filter "ffprobe.exe" | Select-Object -First 1

if (-not $ffmpeg) {
    throw "ffmpeg.exe tidak ketemu di zip"
}

Copy-Item $ffmpeg.FullName (Join-Path $binDir "ffmpeg.exe") -Force
if ($ffprobe) {
    Copy-Item $ffprobe.FullName (Join-Path $binDir "ffprobe.exe") -Force
}

Write-Host "FFmpeg siap di: $binDir"
Get-ChildItem $binDir | Select-Object Name, Length | Format-Table
