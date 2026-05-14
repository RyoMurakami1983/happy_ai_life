#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateRange(1, 120)][int]$Minutes,
    [string]$Issue = "",
    [string]$Reason = "",
    [string]$Branch = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-CurrentBranch {
    try {
        $branch = (& git branch --show-current 2>$null | Select-Object -First 1)
        if (-not [string]::IsNullOrWhiteSpace($branch)) {
            return [string]$branch
        }
    }
    catch {
        return ""
    }

    return ""
}

$resolvedStatePath = [System.IO.Path]::GetFullPath((Join-Path $HOME ".copilot\maintenance-mode.json"))
$stateDirectory = Split-Path -Parent $resolvedStatePath
if (-not (Test-Path -LiteralPath $stateDirectory)) {
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
}

$now = [DateTimeOffset]::Now
$effectiveBranch = $Branch
if ([string]::IsNullOrWhiteSpace($effectiveBranch)) {
    $effectiveBranch = Get-CurrentBranch
}

$stateProperties = [ordered]@{
    schemaVersion = 1
    enabled = $true
    createdAt = $now.ToString("o")
    expiresAt = $now.AddMinutes($Minutes).ToString("o")
    scopes = @("protectedPathEdit")
}

if (-not [string]::IsNullOrWhiteSpace($Issue)) {
    $stateProperties.issue = $Issue
}

if (-not [string]::IsNullOrWhiteSpace($effectiveBranch)) {
    $stateProperties.branch = $effectiveBranch
}

if (-not [string]::IsNullOrWhiteSpace($Reason)) {
    $stateProperties.reason = $Reason
}

$state = [pscustomobject]$stateProperties

$state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resolvedStatePath -Encoding utf8

Write-Host "Copilot maintenance mode enabled." -ForegroundColor Yellow
Write-Host "State: $resolvedStatePath"
if (-not [string]::IsNullOrWhiteSpace($Issue)) {
    Write-Host "Issue: $Issue"
}
if (-not [string]::IsNullOrWhiteSpace($effectiveBranch)) {
    Write-Host "Branch: $effectiveBranch"
}
if (-not [string]::IsNullOrWhiteSpace($Reason)) {
    Write-Host "Reason: $Reason"
}
Write-Host "ExpiresAt: $($state.expiresAt)"
Write-Host "Scope: protectedPathEdit"
Write-Host "Deny rules for secrets, destructive commands, and hook bypass remain active."
