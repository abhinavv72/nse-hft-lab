$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location "$root\backend"

if (-not (Test-Path ".venv")) {
  throw "Run scripts\setup.ps1 first."
}

$env:PYTHONPATH = "$root\backend"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Pop-Location
