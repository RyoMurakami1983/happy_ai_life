param(
    [string]$CopilotDir = (Join-Path $env:USERPROFILE '.copilot')
)

$ErrorActionPreference = 'Stop'

$skillDir = Split-Path -Parent $PSScriptRoot
$assetsDir = Join-Path $skillDir 'assets'
$settingsPath = Join-Path $CopilotDir 'settings.json'

function Test-JsonObjectLike {
    param([object]$Value)

    return $Value -is [pscustomobject] -or $Value -is [hashtable]
}

function Test-JsonArrayLike {
    param([object]$Value)

    return $Value -is [System.Collections.IList] -and $Value -isnot [string]
}

New-Item -ItemType Directory -Force -Path $CopilotDir | Out-Null

foreach ($fileName in @('statusline.cmd', 'statusline.ps1', 'statusline.omp.json')) {
    Copy-Item -LiteralPath (Join-Path $assetsDir $fileName) -Destination (Join-Path $CopilotDir $fileName) -Force
}

if (Test-Path -LiteralPath $settingsPath) {
    $backup = "$settingsPath.statusline-backup-$(Get-Date -Format 'yyyyMMddTHHmmssK')"
    Copy-Item -LiteralPath $settingsPath -Destination $backup -Force
    $settings = Get-Content -Raw -LiteralPath $settingsPath | ConvertFrom-Json
} else {
    $settings = [pscustomobject]@{}
}

if ($settings -isnot [pscustomobject] -and $settings -isnot [hashtable]) {
    throw "$settingsPath must contain a JSON object."
}

if ($null -eq $settings.statusLine) {
    $settings | Add-Member -NotePropertyName statusLine -NotePropertyValue ([pscustomobject]@{}) -Force
} elseif (-not (Test-JsonObjectLike $settings.statusLine)) {
    throw "$settingsPath statusLine must be a JSON object."
}

$settings.statusLine | Add-Member -NotePropertyName type -NotePropertyValue 'command' -Force
$settings.statusLine | Add-Member -NotePropertyName command -NotePropertyValue (Join-Path $CopilotDir 'statusline.cmd') -Force
$settings.statusLine | Add-Member -NotePropertyName padding -NotePropertyValue 1 -Force

if ($null -eq $settings.feature_flags) {
    $settings | Add-Member -NotePropertyName feature_flags -NotePropertyValue ([pscustomobject]@{ enabled = @() }) -Force
} elseif (-not (Test-JsonObjectLike $settings.feature_flags)) {
    throw "$settingsPath feature_flags must be a JSON object."
}

if ($null -eq $settings.feature_flags.enabled) {
    $settings.feature_flags | Add-Member -NotePropertyName enabled -NotePropertyValue @() -Force
} elseif (-not (Test-JsonArrayLike $settings.feature_flags.enabled)) {
    throw "$settingsPath feature_flags.enabled must be a JSON array."
}

$enabled = @($settings.feature_flags.enabled)
if ($enabled -notcontains 'STATUS_LINE') {
    $settings.feature_flags.enabled = @($enabled + 'STATUS_LINE')
}

$settings | Add-Member -NotePropertyName experimental -NotePropertyValue $true -Force
$settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8

Write-Host "Installed Copilot statusline to $CopilotDir"
Write-Host "Run /restart in Copilot CLI if it is already open."
