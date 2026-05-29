[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$TaskName = "BrokerProjectManagerAutoUpdate",
    [string]$Branch = "main",
    [int]$IntervalMinutes = 5
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$updateScript = Join-Path $ProjectRoot "scripts\deploy\update-from-github.ps1"
if (-not (Test-Path $updateScript)) {
    throw "Update script not found: $updateScript"
}

if ($IntervalMinutes -lt 1) {
    throw "IntervalMinutes must be at least 1."
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$updateScript`" -ProjectRoot `"$ProjectRoot`" -Branch `"$Branch`""

Write-Host "Creating scheduled task: $TaskName"
Write-Host "ProjectRoot: $ProjectRoot"
Write-Host "Interval: every $IntervalMinutes minutes"

& schtasks.exe /Create /TN $TaskName /SC MINUTE /MO $IntervalMinutes /TR $taskCommand /F | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create scheduled task."
}

Write-Host ""
Write-Host "Scheduled task created."
Write-Host "Run once now with:"
Write-Host "schtasks /Run /TN $TaskName"
Write-Host ""
Write-Host "View recent logs at:"
Write-Host "$env:LOCALAPPDATA\BrokerProjectManager\auto-update.log"

