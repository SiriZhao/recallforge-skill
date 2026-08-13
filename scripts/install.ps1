param(
    [string]$Target = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Source = Split-Path -Parent $PSScriptRoot
if (-not $Target) {
    $Target = Join-Path (Get-Location) "RecallForge"
}

if (Test-Path -LiteralPath $Target) {
    if (-not $Force) {
        throw "Target already exists: $Target. Choose -Target <path> or rerun with -Force."
    }
    $Backup = "$Target.backup-$(Get-Date -Format yyyyMMddHHmmss)"
    Move-Item -LiteralPath $Target -Destination $Backup
    Write-Host "Existing RecallForge copied to: $Backup"
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Get-ChildItem -LiteralPath $Source -Force | Where-Object { $_.Name -notin @('.git', '.venv', 'dist', 'build', '.pytest_cache') } | Copy-Item -Destination $Target -Recurse -Force
Write-Host "RecallForge files copied to: $Target"
Write-Host "Next: cd `"$Target`"; python -m pip install .; recallforge --help"
