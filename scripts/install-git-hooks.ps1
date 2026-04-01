[CmdletBinding()]
param(
    [string]$TargetRepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TemplateRelativePath = "repo-template/.githooks",
    [string]$InstalledHooksPath = ".githooks"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Test-GitRepository {
    param([Parameter(Mandatory = $true)][string]$Path)

    & git -C $Path rev-parse --is-inside-work-tree 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Not a git repository: $Path"
    }
}

function Test-RobocopyResult {
    param([int]$ExitCode)

    if ($ExitCode -ge 8) {
        throw "robocopy failed. ExitCode=$ExitCode"
    }
}

$targetRepoPath = [System.IO.Path]::GetFullPath($TargetRepoPath)
$sourceRoot = [System.IO.Path]::GetFullPath($SourceRoot)
$templatePath = [System.IO.Path]::GetFullPath((Join-Path $sourceRoot $TemplateRelativePath))

if (-not (Test-Path -LiteralPath $targetRepoPath)) {
    throw "Target repository path not found: $targetRepoPath"
}

if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "Git hook template path not found: $templatePath"
}

Test-GitRepository -Path $targetRepoPath

Write-Section "Install git hooks"
Write-Host "Target : $targetRepoPath"
Write-Host "Source : $templatePath"

if ($targetRepoPath -eq $sourceRoot) {
    $hooksPath = $TemplateRelativePath
    & git -C $targetRepoPath config --local core.hooksPath $hooksPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to configure core.hooksPath for $targetRepoPath"
    }

    Write-Host "Configured core.hooksPath to $hooksPath" -ForegroundColor Green
    exit 0
}

$destinationPath = Join-Path $targetRepoPath $InstalledHooksPath
if (-not (Test-Path -LiteralPath $destinationPath)) {
    New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
}

& robocopy $templatePath $destinationPath /MIR /R:2 /W:1 /NFL /NDL /NP /NJH /NJS /XJ
Test-RobocopyResult -ExitCode $LASTEXITCODE

& git -C $targetRepoPath config --local core.hooksPath $InstalledHooksPath
if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure core.hooksPath for $targetRepoPath"
}

Write-Host "Installed hooks to $destinationPath and configured core.hooksPath=$InstalledHooksPath" -ForegroundColor Green
