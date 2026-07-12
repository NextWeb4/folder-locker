param(
    [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ReleaseDir = Join-Path $Root "release-assets"
$ExePath = Join-Path $ReleaseDir "folder-locker-v1.0.0-windows-x64.exe"
$ZipPath = Join-Path $ReleaseDir "folder-locker-v1.0.0-windows-x64.zip"

if (!(Test-Path -LiteralPath $ExePath)) {
    throw "Missing EXE: $ExePath"
}
if (!(Test-Path -LiteralPath $ZipPath)) {
    throw "Missing ZIP: $ZipPath"
}

$TempRoot = Join-Path $env:TEMP ("folder-locker-smoke-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempRoot | Out-Null
try {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $TempRoot -Force
    $ExtractedExe = Get-ChildItem -LiteralPath $TempRoot -Recurse -Filter "folder-locker.exe" | Select-Object -First 1
    if ($null -eq $ExtractedExe) {
        throw "Portable ZIP does not contain folder-locker.exe"
    }

    if (!$SkipLaunch) {
        $Process = Start-Process -FilePath $ExtractedExe.FullName -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 4
        if ($Process.HasExited) {
            throw "Smoke launch exited too early with code $($Process.ExitCode)"
        }
        Stop-Process -Id $Process.Id -Force
    }
}
finally {
    Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
