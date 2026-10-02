# Local developer release / 本地开发发布。No scheduler or network updater.
param(
    [ValidateSet("build", "promote", "rollback", "backup", "restore")]
    [string]$Command = "build",
    [string]$Python,
    [string]$Path,
    [string]$Destination,
    [string]$BuildId,
    [switch]$StageOnly
)
$ErrorActionPreference = "Stop"
if (-not $Python) {
    $Python = Join-Path $PSScriptRoot ".venv-rehab\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }
}
$releaseArgs = @((Join-Path $PSScriptRoot "scripts\release_manager.py"), $Command)
if ($Path) { $releaseArgs += @("--path", $Path) }
if ($Destination) { $releaseArgs += @("--destination", $Destination) }
if ($BuildId) { $releaseArgs += @("--build-id", $BuildId) }
if ($StageOnly) { $releaseArgs += "--stage-only" }
& $Python @releaseArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
