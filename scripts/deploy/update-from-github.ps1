[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$ForceBuild,
    [string]$FrontendHealthUrl = "http://127.0.0.1:5173",
    [string]$BackendHealthUrl = "http://127.0.0.1:8000/docs",
    [string]$LogPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $logRoot = if ($env:LOCALAPPDATA) {
        Join-Path $env:LOCALAPPDATA "BrokerProjectManager"
    } else {
        Join-Path $ProjectRoot ".deploy"
    }
    $LogPath = Join-Path $logRoot "auto-update.log"
}

$logDir = Split-Path -Parent $LogPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$lockPath = Join-Path $logDir "auto-update.lock"

function Write-Log {
    param([string]$Message)

    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogPath -Value $line
}

function Invoke-Logged {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    Write-Log ("> " + $FilePath + " " + ($Arguments -join " "))
    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($output) {
        foreach ($line in $output) {
            Write-Log $line
        }
    }
    if ($exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}: $FilePath"
    }
}

function Test-HttpReady {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 8
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    } catch {
        return $false
    }
}

if (Test-Path $lockPath) {
    $lockAge = (Get-Date) - (Get-Item $lockPath).LastWriteTime
    if ($lockAge.TotalMinutes -lt 30) {
        Write-Log "Another update process is already running. Skip this run."
        exit 0
    }
    Write-Log "Found stale lock file. Removing it."
    Remove-Item -LiteralPath $lockPath -Force
}

try {
    New-Item -ItemType File -Path $lockPath -Force | Out-Null
    Write-Log "Starting auto update in $ProjectRoot"

    Push-Location $ProjectRoot

    $isRepo = (& git rev-parse --is-inside-work-tree 2>$null)
    if ($isRepo -ne "true") {
        throw "ProjectRoot is not a git repository: $ProjectRoot"
    }

    $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($currentBranch -ne $Branch) {
        throw "Deployment checkout is on branch '$currentBranch'. Expected '$Branch'. Use a separate directory for B-machine development."
    }

    $dirty = (& git status --porcelain)
    if ($dirty) {
        throw "Deployment checkout has local changes. Commit/stash them or keep development in a separate clone."
    }

    Invoke-Logged -FilePath "git" -Arguments @("fetch", $Remote, $Branch)

    $localHead = (& git rev-parse HEAD).Trim()
    $remoteHead = (& git rev-parse "$Remote/$Branch").Trim()

    if ($localHead -eq $remoteHead -and -not $ForceBuild) {
        Write-Log "No new commit found. Local HEAD is $localHead."
    } else {
        if ($localHead -ne $remoteHead) {
            Write-Log "Updating $Branch from $localHead to $remoteHead."
            Invoke-Logged -FilePath "git" -Arguments @("merge", "--ff-only", "$Remote/$Branch")
        } else {
            Write-Log "ForceBuild enabled. Rebuilding current commit $localHead."
        }

        Invoke-Logged -FilePath "docker" -Arguments @("compose", "up", "-d", "--build", "--remove-orphans")
    }

    if (-not (Test-HttpReady -Url $BackendHealthUrl) -or -not (Test-HttpReady -Url $FrontendHealthUrl)) {
        Write-Log "Services are not healthy yet. Ensuring docker compose services are running."
        Invoke-Logged -FilePath "docker" -Arguments @("compose", "up", "-d", "--remove-orphans")
        Start-Sleep -Seconds 5
    }

    if (-not (Test-HttpReady -Url $BackendHealthUrl)) {
        throw "Backend health check failed: $BackendHealthUrl"
    }

    if (-not (Test-HttpReady -Url $FrontendHealthUrl)) {
        throw "Frontend health check failed: $FrontendHealthUrl"
    }

    Write-Log "Auto update finished successfully."
} catch {
    Write-Log ("Auto update failed: " + $_.Exception.Message)
    exit 1
} finally {
    Pop-Location -ErrorAction SilentlyContinue
    if (Test-Path $lockPath) {
        Remove-Item -LiteralPath $lockPath -Force
    }
}
