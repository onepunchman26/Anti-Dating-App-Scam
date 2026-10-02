# Build a self-contained Windows app; no credentials or automatic downloads.
# Usage: .\packaging\build_windows.ps1 -Target Desktop -Python <python.exe>
param(
    [ValidateSet("Desktop", "Web", "Node")]
    [string]$Target = "Desktop",
    [string]$Python = "python",
    [string]$OutputDirectory,
    [string]$MetadataDirectory,
    [switch]$Console
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$buildId = [guid]::NewGuid().ToString("N")
$buildRoot = Join-Path $repo "build\portable-$Target\$buildId"
$definitions = @{
    Desktop = @("AI-SlowMatch", "run_desktop.py")
    Web = @("AI-SlowMatch-Web", "run_local_app.py")
    Node = @("AI-SlowMatch-Node", "run_rendezvous_node.py")
}
$name, $entry = $definitions[$Target]
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $buildRoot "package" }
$pythonCommand = (Get-Command $Python -ErrorAction Stop).Source
& $pythonCommand -c "import sys; import PyInstaller; assert sys.version_info >= (3, 11)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ and PyInstaller are required. Install them first." }
if ($Target -eq "Desktop") {
    & $pythonCommand -c "import PySide6.QtMultimedia; import vosk"
    if ($LASTEXITCODE -ne 0) { throw "Desktop builds require PySide6 and Vosk. Install .[desktop] first." }
    if (-not $MetadataDirectory) {
        $MetadataDirectory = Join-Path $buildRoot "metadata"
        & $pythonCommand (Join-Path $repo "scripts\release_manager.py") metadata --path $MetadataDirectory
        if ($LASTEXITCODE -ne 0) { throw "Version metadata generation failed." }
    }
}

$arguments = @(
    "-m", "PyInstaller", "--noconfirm", "--onefile",
    "--name", $name,
    "--paths", (Join-Path $repo "src"),
    "--paths", (Join-Path $repo "apps"),
    "--paths", (Join-Path $repo "apps\desktop_pyqt"),
    "--add-data", ((Join-Path $repo "src\anti_dating_scam\schemas") + ";anti_dating_scam/schemas"),
    "--add-data", ((Join-Path $repo "src\anti_dating_scam\licenses") + ";anti_dating_scam/licenses"),
    "--add-data", ((Join-Path $repo "src\anti_dating_scam\skills") + ";anti_dating_scam/skills"),
    "--add-data", ((Join-Path $repo "apps\rendezvous_web\index.html") + ";rendezvous_web"),
    "--hidden-import", "rendezvous_web",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespan.on",
    "--workpath", (Join-Path $buildRoot "work"),
    "--specpath", $buildRoot,
    "--distpath", $OutputDirectory
)
if ($Target -eq "Desktop" -and -not $Console) { $arguments += "--windowed" }
if ($Target -eq "Desktop") {
    # Model ZIPs stay outside the executable and are installed by user click.
    # Vosk's native recognizer DLL and Qt audio input plugin must be bundled.
    $arguments += @(
        "--hidden-import", "vosk",
        "--collect-binaries", "vosk",
        "--hidden-import", "PySide6.QtMultimedia",
        "--hidden-import", "PySide6.QtTextToSpeech",
        "--add-data", ((Join-Path $MetadataDirectory "build_info.json") + ";anti_dating_scam"),
        "--version-file", (Join-Path $MetadataDirectory "version-resource.txt")
    )
}
if ($Target -ne "Desktop") {
    $arguments += @(
        "--exclude-module", "anti_dating_scam_desktop",
        "--exclude-module", "PySide6",
        "--exclude-module", "shiboken6"
    )
}
$arguments += (Join-Path $repo $entry)

Push-Location $repo
$originalPath = $env:PATH
$originalBuildCache = $env:PYINSTALLER_CONFIG_DIR
try {
    # Unrelated native tools on PATH can shadow Windows ICU with incompatible
    # DLL exports. Qt hooks supply their own package directories; restrict the
    # remaining DLL lookup to this interpreter and Windows system libraries.
    $env:PATH = @(
        (Split-Path -Parent $pythonCommand),
        (Join-Path $env:SystemRoot "System32"),
        $env:SystemRoot
    ) -join [IO.Path]::PathSeparator
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $buildRoot "cache"
    & $pythonCommand @arguments
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)." }
    $artifact = Join-Path $OutputDirectory "$name.exe"
    if (-not (Test-Path -LiteralPath $artifact)) { throw "Build did not produce $name.exe." }
    if ($Target -ne "Node") {
        & $pythonCommand (Join-Path $repo "packaging\smoke_executable.py") $artifact --target $Target
        if ($LASTEXITCODE -ne 0) { throw "Portable $Target startup verification failed." }
    }
    Get-Item -LiteralPath $artifact |
        Select-Object Name, @{n = "MB"; e = { [math]::Round($_.Length / 1MB, 1) } }
}
finally {
    $env:PATH = $originalPath
    $env:PYINSTALLER_CONFIG_DIR = $originalBuildCache
    Pop-Location
}
