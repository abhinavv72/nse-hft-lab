param(
  [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$preferredPython = Join-Path $env:LocalAppData "Programs\Python\Python313\python.exe"
$pythonExe = if (Test-Path $preferredPython) { $preferredPython } else { "python" }

function Invoke-Step {
  param(
    [scriptblock]$Action,
    [string]$Description
  )

  & $Action
  if ($LASTEXITCODE -ne 0) {
    throw "$Description failed with exit code $LASTEXITCODE"
  }
}

Push-Location "$root\backend"
if (-not (Test-Path ".venv")) {
  Invoke-Step { & $pythonExe -m venv .venv } "Virtual environment creation"
}

Invoke-Step { & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip } "Pip upgrade"
Invoke-Step { & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt } "Backend dependency installation"
Pop-Location

Push-Location "$root\engine"
Invoke-Step { cmake -S . -B build } "CMake configure"
Invoke-Step { cmake --build build --config Release } "CMake build"
Pop-Location

if (-not $SkipFrontend) {
  Push-Location "$root\frontend"
  Invoke-Step { npm.cmd install } "Frontend dependency installation"
  Pop-Location
}

Write-Host "Setup complete."
