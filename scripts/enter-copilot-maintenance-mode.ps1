#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateRange(1, 120)][int]$Minutes,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Issue,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Reason,
    [string]$Branch = "",
    [string]$StatePath = (Join-Path $HOME ".copilot\maintenance-mode.json")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-CurrentBranch {
    $branch = (& git branch --show-current 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($branch)) {
        return [string]$branch
    }
    return ""
}

$resolvedStatePath = [System.IO.Path]::GetFullPath($StatePath)
$stateDirectory = Split-Path -Parent $resolvedStatePath
if (-not (Test-Path -LiteralPath $stateDirectory)) {
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
}

$now = [DateTimeOffset]::Now
$effectiveBranch = $Branch
if ([string]::IsNullOrWhiteSpace($effectiveBranch)) {
    $effectiveBranch = Get-CurrentBranch
}

$state = [pscustomobject][ordered]@{
    schemaVersion = 1
    enabled = $true
    createdAt = $now.ToString("o")
    expiresAt = $now.AddMinutes($Minutes).ToString("o")
    issue = $Issue
    branch = $effectiveBranch
    reason = $Reason
    scopes = @("protectedPathEdit")
}

$state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resolvedStatePath -Encoding utf8

Write-Host "Copilot maintenance mode enabled." -ForegroundColor Yellow
Write-Host "State: $resolvedStatePath"
Write-Host "Issue: $Issue"
Write-Host "Branch: $effectiveBranch"
Write-Host "ExpiresAt: $($state.expiresAt)"
Write-Host "Scope: protectedPathEdit"
Write-Host "Deny rules for secrets, destructive commands, and hook bypass remain active."
