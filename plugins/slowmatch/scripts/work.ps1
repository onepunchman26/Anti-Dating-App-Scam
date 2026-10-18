# Invoke the original Python core. No private data, auth, server or model lives here.
$ErrorActionPreference = 'Stop'
$taskRuntimePath = Join-Path $env:LOCALAPPDATA 'AI-SlowMatch\work-runtime.json'
if (-not (Test-Path -LiteralPath $taskRuntimePath -PathType Leaf)) {
    Write-Output '{"ok":false,"error":"work_runtime_not_configured"}'
    exit 1
}
try {
    $taskRuntime = Get-Content -LiteralPath $taskRuntimePath -Raw | ConvertFrom-Json
    if ($taskRuntime.schema_version -ne 1 -or
        -not (Test-Path -LiteralPath $taskRuntime.python -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $taskRuntime.source_root 'src\anti_dating_scam\work_cli.py') -PathType Leaf)) {
        throw 'invalid runtime'
    }
    $taskPreviousPath = $env:PYTHONPATH
    $env:PYTHONPATH = Join-Path $taskRuntime.source_root 'src'
    try {
        & $taskRuntime.python -X utf8 -m anti_dating_scam.work_cli @args
        $taskExit = $LASTEXITCODE
    } finally {
        $env:PYTHONPATH = $taskPreviousPath
    }
    exit $taskExit
} catch {
    Write-Output '{"ok":false,"error":"work_runtime_unavailable"}'
    exit 1
}
