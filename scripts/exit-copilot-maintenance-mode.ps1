#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$StatePath = (Join-Path $HOME ".copilot\maintenance-mode.json"),
    [switch]$Remove
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedStatePath = [System.IO.Path]::GetFullPath($StatePath)
if (-not (Test-Path -LiteralPath $resolvedStatePath -PathType Leaf)) {
    Write-Host "Copilot maintenance mode state does not exist: $resolvedStatePath"
    exit 0
}

if ($Remove) {
    Remove-Item -LiteralPath $resolvedStatePath -Force
    Write-Host "Copilot maintenance mode state removed: $resolvedStatePath" -ForegroundColor Green
    exit 0
}

try {
    $state = Get-Content -LiteralPath $resolvedStatePath -Raw | ConvertFrom-Json
}
catch {
    Remove-Item -LiteralPath $resolvedStatePath -Force
    Write-Host "Invalid maintenance mode state was removed: $resolvedStatePath" -ForegroundColor Yellow
    exit 0
}

$state.enabled = $false
$state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resolvedStatePath -Encoding utf8
Write-Host "Copilot maintenance mode disabled: $resolvedStatePath" -ForegroundColor Green
