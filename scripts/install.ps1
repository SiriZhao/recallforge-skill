param([string]$Target = "", [switch]$Force)
$ErrorActionPreference = "Stop"
$Source = Join-Path (Split-Path -Parent $PSScriptRoot) "recallforge"
if (-not (Test-Path -LiteralPath (Join-Path $Source "SKILL.md"))) { $Source = Join-Path (Split-Path -Parent $PSScriptRoot) "skill\recallforge" }
if (-not $Target) { $Target = Join-Path $env:USERPROFILE ".agents\skills\recallforge" }
if (Test-Path -LiteralPath $Target) {
  if (-not $Force) { throw "RecallForge already exists at: $Target. Re-run with -Force to replace only RecallForge." }
  $Backup = "$Target.backup-$(Get-Date -Format yyyyMMddHHmmss)"; Move-Item -LiteralPath $Target -Destination $Backup; Write-Host "Backup created: $Backup"
}
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Get-ChildItem -LiteralPath $Source -Force | Copy-Item -Destination $Target -Recurse -Force
Write-Host "RecallForge installed successfully."
Write-Host "Location: $Target"
Write-Host "Next: open a new Codex turn and run `$recallforge self-test."
