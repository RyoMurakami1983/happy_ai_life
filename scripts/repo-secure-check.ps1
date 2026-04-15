[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepoPath,

    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,

    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function New-CheckResult {
    param(
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][bool]$Ok,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Details
    )

    return [ordered]@{
        key = $Key
        label = $Label
        ok = $Ok
        path = $Path
        details = $Details
    }
}

function Test-DirectoryHasEntries {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return $false
    }

    return $null -ne (Get-ChildItem -LiteralPath $Path -Force | Select-Object -First 1)
}

function Test-DirectoryHasJsonFiles {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return $false
    }

    return $null -ne (Get-ChildItem -LiteralPath $Path -File -Filter "*.json" -Force | Select-Object -First 1)
}

function Test-GitRepository {
    param([Parameter(Mandatory = $true)][string]$Path)

    & git -C $Path rev-parse --is-inside-work-tree 1>$null 2>$null
    return $LASTEXITCODE -eq 0
}

$targetRepoPath = [System.IO.Path]::GetFullPath($TargetRepoPath)
if (-not (Test-Path -LiteralPath $targetRepoPath)) {
    throw "Target repository path not found: $targetRepoPath"
}

$instructionsPath = Join-Path $targetRepoPath ".github\copilot-instructions.md"
$copilotHooksPath = Join-Path $targetRepoPath ".github\hooks"
$gitHooksPath = Join-Path $targetRepoPath ".githooks"
$sourceRootPath = [System.IO.Path]::GetFullPath($SourceRoot)

$isGitRepo = Test-GitRepository -Path $targetRepoPath
$coreHooksConfigured = ""
$coreHooksResolvedPath = ""
$expectedGitHooksPaths = New-Object System.Collections.Generic.List[string]
[void]$expectedGitHooksPaths.Add([System.IO.Path]::GetFullPath($gitHooksPath))
if ($targetRepoPath -eq $sourceRootPath) {
    [void]$expectedGitHooksPaths.Add([System.IO.Path]::GetFullPath((Join-Path $targetRepoPath "repo-template\.githooks")))
}

if ($isGitRepo) {
    $coreHooksRaw = & git -C $targetRepoPath config --local --get core.hooksPath 2>$null
    if ($LASTEXITCODE -eq 0) {
        $coreHooksConfigured = (($coreHooksRaw | Select-Object -First 1) | Out-String).Trim()
    }

    if (-not [string]::IsNullOrWhiteSpace($coreHooksConfigured)) {
        if ([System.IO.Path]::IsPathRooted($coreHooksConfigured)) {
            $coreHooksResolvedPath = [System.IO.Path]::GetFullPath($coreHooksConfigured)
        }
        else {
            $coreHooksResolvedPath = [System.IO.Path]::GetFullPath((Join-Path $targetRepoPath $coreHooksConfigured))
        }
    }
}

$instructionsOk = Test-Path -LiteralPath $instructionsPath -PathType Leaf
$copilotHooksOk = Test-DirectoryHasJsonFiles -Path $copilotHooksPath
$gitHooksOk = Test-DirectoryHasEntries -Path $gitHooksPath
$coreHooksOk = $false
$coreHooksDetails = ""

if (-not $isGitRepo) {
    $coreHooksDetails = "Git repository として初期化されていません。"
}
elseif ([string]::IsNullOrWhiteSpace($coreHooksConfigured)) {
    $coreHooksDetails = "core.hooksPath が設定されていません。"
}
elseif ($expectedGitHooksPaths.Contains($coreHooksResolvedPath)) {
    $coreHooksOk = $true
    $coreHooksDetails = "core.hooksPath は許可された git hooks path を指しています。"
}
else {
    $coreHooksDetails = "core.hooksPath は '$coreHooksConfigured' を指しており、許可された git hooks path と一致しません。"
}

$checks = @(
    (New-CheckResult `
        -Key "repoInstructions" `
        -Label "repo instructions" `
        -Ok $instructionsOk `
        -Path $instructionsPath `
        -Details ($(if ($instructionsOk) { "repo-wide instructions が存在します。" } else { "repo-wide instructions がありません。" }))),
    (New-CheckResult `
        -Key "copilotHooks" `
        -Label "Copilot hooks" `
        -Ok $copilotHooksOk `
        -Path $copilotHooksPath `
        -Details ($(if ($copilotHooksOk) { "Copilot hooks の JSON 設定が存在します。" } else { "Copilot hooks の JSON 設定がありません。" }))),
    (New-CheckResult `
        -Key "gitHooksDirectory" `
        -Label ".githooks" `
        -Ok $gitHooksOk `
        -Path $gitHooksPath `
        -Details ($(if ($gitHooksOk) { ".githooks が存在します。" } else { ".githooks がありません。" }))),
    (New-CheckResult `
        -Key "coreHooksPath" `
        -Label "core.hooksPath" `
        -Ok $coreHooksOk `
        -Path $(if ([string]::IsNullOrWhiteSpace($coreHooksResolvedPath)) { $gitHooksPath } else { $coreHooksResolvedPath }) `
        -Details $coreHooksDetails)
)

$missing = New-Object System.Collections.Generic.List[string]
foreach ($check in $checks) {
    if (-not $check.ok) {
        [void]$missing.Add([string]$check.key)
    }
}

$warnings = New-Object System.Collections.Generic.List[string]
[void]$warnings.Add("Branch Protection / Ruleset はローカルでは確認できません。")
if (-not $isGitRepo) {
    [void]$warnings.Add("Git repository として初期化されていないため、core.hooksPath は不足として扱います。")
}

$report = [ordered]@{
    targetRepoPath = $targetRepoPath
    isGitRepo = $isGitRepo
    missing = @($missing)
    warnings = @($warnings)
    checks = $checks
}

if ($AsJson) {
    $report | ConvertTo-Json -Depth 5
    exit 0
}

Write-Section "Repo secure check"
Write-Host "Target : $targetRepoPath"
Write-Host "Git    : $isGitRepo"

foreach ($check in $checks) {
    $status = if ($check.ok) { "OK" } else { "MISSING" }
    $color = if ($check.ok) { "Green" } else { "Yellow" }
    Write-Host ("[{0}] {1}" -f $status, $check.label) -ForegroundColor $color
    Write-Host ("  Path    : {0}" -f $check.path)
    Write-Host ("  Details : {0}" -f $check.details)
}

if ($missing.Count -eq 0) {
    Write-Host "All local safety valves are present." -ForegroundColor Green
}
else {
    Write-Warning ("Missing local safety valves: {0}" -f ($missing -join ", "))
}

foreach ($warning in $warnings) {
    Write-Warning $warning
}

exit 0
