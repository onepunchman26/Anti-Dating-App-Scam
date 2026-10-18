# Stable packaged entry point. The runtime validates account/slot binding and inputs.
# The source-checkout route is explicit developer compatibility, never an install fallback.
$ErrorActionPreference = 'Stop'
$taskArguments = @($args)

if ($taskArguments.Count -gt 0 -and $taskArguments[0] -eq '--developer-source') {
    $taskArguments = @($taskArguments | Select-Object -Skip 1)
    try {
        $taskRuntimePath = Join-Path $env:LOCALAPPDATA 'AI-SlowMatch\work-runtime.json'
        $taskRuntime = Get-Content -LiteralPath $taskRuntimePath -Raw | ConvertFrom-Json
        if ($taskRuntime.schema_version -ne 1 -or
            -not (Test-Path -LiteralPath $taskRuntime.python -PathType Leaf) -or
            -not (Test-Path -LiteralPath (Join-Path $taskRuntime.source_root 'src\anti_dating_scam\work_cli.py') -PathType Leaf)) {
            throw 'invalid developer runtime'
        }
        $taskPreviousPath = $env:PYTHONPATH
        $env:PYTHONPATH = Join-Path $taskRuntime.source_root 'src'
        try {
            & $taskRuntime.python -X utf8 -m anti_dating_scam.work_cli @taskArguments
            $taskExit = $LASTEXITCODE
        } finally {
            $env:PYTHONPATH = $taskPreviousPath
        }
        exit $taskExit
    } catch {
        Write-Output '{"ok":false,"error":"developer_work_runtime_unavailable"}'
        exit 1
    }
}

try {
    $taskPortableRoot = Join-Path $env:LOCALAPPDATA 'AI-SlowMatch\portable'
    $taskPointerPath = Join-Path $taskPortableRoot 'active.json'
    if (-not (Test-Path -LiteralPath $taskPointerPath -PathType Leaf)) {
        Write-Output '{"ok":false,"error":"portable_runtime_not_installed","next":"run_the_pinned_release_installer"}'
        exit 1
    }
    $taskPointer = Get-Content -LiteralPath $taskPointerPath -Raw | ConvertFrom-Json
    if ($taskPointer.schema_version -ne 1 -or
        $taskPointer.version -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$' -or
        $taskPointer.manifest_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'invalid portable pointer'
    }
    $taskReleasePattern = '^' + [regex]::Escape($taskPointer.version + '-' + $taskPointer.manifest_sha256.Substring(0, 12)) + '(?:-repair-[0-9a-f]{8})?$'
    if ($taskPointer.release -notmatch $taskReleasePattern) { throw 'invalid release identifier' }
    $taskReleaseRoot = Join-Path (Join-Path $taskPortableRoot 'releases') $taskPointer.release
    $taskExecutable = Join-Path $taskReleaseRoot 'SlowMatch-Work.exe'
    foreach ($taskPath in @((Join-Path $env:LOCALAPPDATA 'AI-SlowMatch'), $taskPortableRoot, $taskPointerPath,
            (Join-Path $taskPortableRoot 'releases'), $taskReleaseRoot, $taskExecutable)) {
        $taskItem = Get-Item -LiteralPath $taskPath -Force
        if (($taskItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'redirected portable path'
        }
    }
    if (-not (Test-Path -LiteralPath $taskExecutable -PathType Leaf)) { throw 'missing executable' }
    & $taskExecutable run @taskArguments
    exit $LASTEXITCODE
} catch {
    Write-Output '{"ok":false,"error":"portable_runtime_unavailable","next":"run_release_doctor_then_targeted_repair"}'
    exit 1
}
