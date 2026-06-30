# setup_windows.ps1 - one-shot environment setup for Windows.
# Run from the project root:  .\setup_windows.ps1
# Requires Python 3.11+ (project uses datetime.UTC and enum.StrEnum).
# (Bilingual instructions live in docs/ENVIRONMENT_SETUP.md; this script is
#  kept ASCII-only so Windows PowerShell 5.1 parses it reliably.)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Write-Step($msg) {
    Write-Host ""
    Write-Host ">> $msg" -ForegroundColor Cyan
}

# --- Find a Python 3.11+ interpreter ---
Write-Step "Looking for Python 3.11+ ..."
$candidates = @(
    @("py", "-3"),
    @("python"),
    @("py"),
    @("py", "-3.13"),
    @("py", "-3.12"),
    @("py", "-3.11")
)

$pyExe = $null
$pyPre = @()
foreach ($c in $candidates) {
    $exe = $c[0]
    $pre = @()
    if ($c.Length -gt 1) { $pre = $c[1..($c.Length - 1)] }
    try {
        $ver = & $exe @pre -c "import sys; print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))" 2>$null
    } catch {
        $ver = $null
    }
    if ($ver) {
        $bits = "$ver".Trim().Split(".")
        $maj = [int]$bits[0]
        $min = [int]$bits[1]
        if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 11)) {
            $pyExe = $exe
            $pyPre = $pre
            Write-Host ("   Found: {0} {1} -> Python {2}" -f $exe, ($pre -join ' '), "$ver".Trim()) -ForegroundColor Green
            break
        }
    }
}

if (-not $pyExe) {
    Write-Host ""
    Write-Host "ERROR: No Python 3.11+ found on PATH or via the 'py' launcher." -ForegroundColor Red
    Write-Host "Install it, then re-run this script:" -ForegroundColor Yellow
    Write-Host "    winget install Python.Python.3.12" -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 1
}

# --- Create venv ---
Write-Step "Creating virtual environment (.venv) ..."
if (Test-Path ".venv") {
    Write-Host "   .venv already exists, reusing it." -ForegroundColor DarkGray
} else {
    & $pyExe @pyPre -m venv .venv
}

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "ERROR: venv python not found at $venvPy" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

# --- Install dependencies ---
Write-Step "Upgrading pip ..."
& $venvPy -m pip install --upgrade pip

Write-Step "Installing project + desktop + dev dependencies (this downloads PySide6, may take a few minutes) ..."
& $venvPy -m pip install -e ".[desktop,dev]"

# --- Verify ---
Write-Step "Compiling sources ..."
& $venvPy -m compileall src

Write-Step "Running tests ..."
& $venvPy -m pytest -q

Write-Step "Linting ..."
& $venvPy -m ruff check src tests

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Activate the environment with:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "Then launch the app with:" -ForegroundColor Green
Write-Host "    python run_desktop.py" -ForegroundColor White
Read-Host "Press Enter to close"
