[CmdletBinding()]
param(
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

function Resolve-Executable {
    param(
        [string[]]$Candidates,
        [string]$Label
    )

    foreach ($candidate in $Candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }

        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }

    throw "Cannot find $Label. Please install it or set the proper path."
}

function Test-ListeningPort {
    param([int]$Port)

    try {
        $null = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $true
    } catch {
        return $false
    }
}

function Wait-HttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSec = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 800
            continue
        }
    }

    return $false
}

$pythonExe = Resolve-Executable -Candidates @(
    $env:BPM_PYTHON,
    "D:\python\python3.8\ths\python.exe",
    "python"
) -Label "Python"

$npmCmd = Resolve-Executable -Candidates @("npm.cmd", "npm") -Label "npm"

if (-not (Test-Path $BackendDir)) {
    throw "Backend directory not found: $BackendDir"
}

if (-not (Test-Path $FrontendDir)) {
    throw "Frontend directory not found: $FrontendDir"
}

if (Test-ListeningPort -Port 8000) {
    Write-Host "Backend is already running on port 8000."
} else {
    Start-Process `
        -FilePath $pythonExe `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -WindowStyle Hidden | Out-Null
    Write-Host "Starting backend service..."
}

if (Test-ListeningPort -Port 5173) {
    Write-Host "Frontend is already running on port 5173."
} else {
    Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList @("/c", "`"$npmCmd`" run dev -- --host 0.0.0.0 --port 5173") `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Hidden | Out-Null
    Write-Host "Starting frontend service..."
}

$frontendReady = Wait-HttpReady -Url "http://127.0.0.1:5173" -TimeoutSec 45
$backendReady = Wait-HttpReady -Url "http://127.0.0.1:8000/docs" -TimeoutSec 45
$lanAddress = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
    Select-Object -First 1 -ExpandProperty IPAddress)

Write-Host ""
Write-Host "Start result:"
Write-Host ("Frontend: " + ($(if ($frontendReady) { "http://127.0.0.1:5173" } else { "startup timed out" })))
if ($frontendReady -and $lanAddress) {
    Write-Host ("Frontend LAN: http://" + $lanAddress + ":5173")
}
Write-Host ("Backend: " + ($(if ($backendReady) { "http://127.0.0.1:8000/docs" } else { "startup timed out" })))

if ($OpenBrowser -and $frontendReady) {
    Start-Process "http://127.0.0.1:5173"
}
