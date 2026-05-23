param(
    [string]$CopilotDir = (Join-Path $env:USERPROFILE '.copilot')
)

$ErrorActionPreference = 'Stop'

$skillDir = Split-Path -Parent $PSScriptRoot
$assetsDir = Join-Path $skillDir 'assets'
$settingsPath = Join-Path $CopilotDir 'settings.json'

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

if ($null -eq $settings.statusLine) {
    $settings | Add-Member -NotePropertyName statusLine -NotePropertyValue ([pscustomobject]@{}) -Force
}

$settings.statusLine | Add-Member -NotePropertyName type -NotePropertyValue 'command' -Force
$settings.statusLine | Add-Member -NotePropertyName command -NotePropertyValue (Join-Path $CopilotDir 'statusline.cmd') -Force
$settings.statusLine | Add-Member -NotePropertyName padding -NotePropertyValue 1 -Force

if ($null -eq $settings.feature_flags) {
    $settings | Add-Member -NotePropertyName feature_flags -NotePropertyValue ([pscustomobject]@{ enabled = @() }) -Force
}

if ($null -eq $settings.feature_flags.enabled) {
    $settings.feature_flags | Add-Member -NotePropertyName enabled -NotePropertyValue @() -Force
}

$enabled = @($settings.feature_flags.enabled)
if ($enabled -notcontains 'STATUS_LINE') {
    $settings.feature_flags.enabled = @($enabled + 'STATUS_LINE')
}

$settings | Add-Member -NotePropertyName experimental -NotePropertyValue $true -Force
$settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8

Write-Host "Installed Copilot statusline to $CopilotDir"
Write-Host "Run /restart in Copilot CLI if it is already open."
