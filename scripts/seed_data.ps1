$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $root "data"

Get-ChildItem $dataDir -Filter "*_sample.csv" | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
Write-Host "Bundled seed data is already present under $dataDir."
