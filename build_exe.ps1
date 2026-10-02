# Compatibility entry: Desktop uses the verified release workflow.
param(
    [string]$Python,
    [ValidateSet("Desktop", "Web", "Node")]
    [string]$Target = "Desktop"
)
$ErrorActionPreference = "Stop"
if ($Target -eq "Desktop") {
    & (Join-Path $PSScriptRoot "release.ps1") -Python $Python
} else {
    if (-not $Python) { $Python = "python" }
    & (Join-Path $PSScriptRoot "packaging\build_windows.ps1") -Python $Python -Target $Target
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
