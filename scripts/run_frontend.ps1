$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location "$root\frontend"

if (-not (Test-Path "node_modules")) {
  npm.cmd install
}

npm.cmd run dev -- --host 0.0.0.0 --port 5173
Pop-Location
