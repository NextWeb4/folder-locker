param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ReleaseDir = Join-Path $Root "release-assets"
$ExeName = "folder-locker-v1.0.0-windows-x64.exe"
$ZipName = "folder-locker-v1.0.0-windows-x64.zip"
$PackageDir = Join-Path $ReleaseDir "folder-locker-v1.0.0-windows-x64"

Push-Location $Root
try {
    $env:PYTHONPATH = Join-Path $Root "src"

    & $Python -m unittest discover -s tests -v
    & $Python -m compileall -q src scripts tests

    foreach ($Path in @("build", "dist", "release-assets")) {
        $FullPath = Join-Path $Root $Path
        if (Test-Path -LiteralPath $FullPath) {
            Remove-Item -LiteralPath $FullPath -Recurse -Force
        }
    }
    New-Item -ItemType Directory -Path $ReleaseDir | Out-Null

    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name folder-locker `
        --paths src `
        --version-file resources/folder-locker-version.txt `
        scripts/entry_folder_locker.py

    Copy-Item -LiteralPath (Join-Path $Root "dist\folder-locker.exe") -Destination (Join-Path $ReleaseDir $ExeName)

    New-Item -ItemType Directory -Path $PackageDir | Out-Null
    Copy-Item -LiteralPath (Join-Path $ReleaseDir $ExeName) -Destination (Join-Path $PackageDir "folder-locker.exe")
    Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination $PackageDir
    Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination $PackageDir
    Copy-Item -LiteralPath (Join-Path $Root "THIRD_PARTY_NOTICES.md") -Destination $PackageDir
    Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath (Join-Path $ReleaseDir $ZipName) -Force
    Remove-Item -LiteralPath $PackageDir -Recurse -Force

    $ChecksumLines = Get-ChildItem -LiteralPath $ReleaseDir -File |
        Where-Object { $_.Name -ne "SHA256SUMS.txt" } |
        Sort-Object Name |
        ForEach-Object {
            $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
            "$Hash  $($_.Name)"
        }
    $ChecksumLines | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReleaseDir "SHA256SUMS.txt")
}
finally {
    Pop-Location
}
