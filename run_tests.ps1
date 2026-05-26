# run_tests.ps1 - Run the project test suite

param(
    [switch]$Verbose,
    [switch]$Coverage,
    [string]$Test = ""
)

$Root = $PSScriptRoot
$Venv = Join-Path $Root ".venv\Scripts\Activate.ps1"

# Activate virtual environment if present
if (Test-Path $Venv) {
    & $Venv
}

$Args = @()

if ($Verbose) { $Args += "-v" }

if ($Coverage) {
    $Args += "--cov=app"
    $Args += "--cov-report=term-missing"
}

if ($Test -ne "") {
    $Args += $Test
}

Write-Host "Running test suite..." -ForegroundColor Cyan
python -m pytest @Args

exit $LASTEXITCODE
