[CmdletBinding()]
param(
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TemplateRelativePath = "home-template\.copilot",
    [string]$DestinationPath = (Join-Path $HOME ".copilot"),
    [switch]$Mirror,
    [switch]$DryRun,
    [switch]$VerboseLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Test-RobocopyResult {
    param([int]$ExitCode)

    # robocopy exit code:
    # 0: no files copied
    # 1: files copied successfully
    # 2-7: success with extras/mismatches etc.
    # 8+: failure
    if ($ExitCode -ge 8) {
        throw "robocopy failed. ExitCode=$ExitCode"
    }
}

function Invoke-Robocopy {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string[]]$ExcludeDirs = @(),
        [string[]]$ExcludeFiles = @(),
        [switch]$MirrorMode,
        [switch]$WhatIfMode,
        [switch]$ShowVerboseLog
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source path not found: $Source"
    }

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }

    $robocopyArgs = @(
        $Source
        $Destination
        "/E"
        "/R:2"
        "/W:1"
        "/NFL"
        "/NDL"
        "/NP"
        "/NJH"
        "/NJS"
        "/XJ"
    )

    if ($MirrorMode) {
        $robocopyArgs += "/MIR"
    }

    if ($WhatIfMode) {
        $robocopyArgs += "/L"
    }

    if ($ShowVerboseLog) {
        $robocopyArgs = @(
            $Source
            $Destination
            "/E"
            "/R:2"
            "/W:1"
            "/XJ"
        )
        if ($MirrorMode) { $robocopyArgs += "/MIR" }
        if ($WhatIfMode) { $robocopyArgs += "/L" }
    }

    foreach ($dir in $ExcludeDirs) {
        $robocopyArgs += "/XD"
        $robocopyArgs += $dir
    }

    foreach ($file in $ExcludeFiles) {
        $robocopyArgs += "/XF"
        $robocopyArgs += $file
    }

    Write-Host "robocopy $($robocopyArgs -join ' ')" -ForegroundColor DarkGray

    & robocopy @robocopyArgs
    $exitCode = $LASTEXITCODE
    Test-RobocopyResult -ExitCode $exitCode

    if ($WhatIfMode) {
        Write-Host "DryRun completed. ExitCode=$exitCode" -ForegroundColor Yellow
    }
    else {
        Write-Host "Sync completed. ExitCode=$exitCode" -ForegroundColor Green
    }
}

Write-Section "Sync to HOME (.copilot)"

$sourcePath = Join-Path $SourceRoot $TemplateRelativePath
$sourcePath = [System.IO.Path]::GetFullPath($sourcePath)
$destinationPath = [System.IO.Path]::GetFullPath($DestinationPath)

Write-Host "Source      : $sourcePath"
Write-Host "Destination : $destinationPath"
Write-Host "Mirror      : $Mirror"
Write-Host "DryRun      : $DryRun"

# 個人 secrets やローカル override を壊しにくくするため、
# 既定では mcp-config.local.json や *.local.* は除外
$excludeFiles = @(
    "mcp-config.local.json",
    "*.local.json",
    "*.local.ps1"
)

$excludeDirs = @(
    ".git",
    ".vs",
    "node_modules"
)

Invoke-Robocopy `
    -Source $sourcePath `
    -Destination $destinationPath `
    -ExcludeDirs $excludeDirs `
    -ExcludeFiles $excludeFiles `
    -MirrorMode:$Mirror `
    -WhatIfMode:$DryRun `
    -ShowVerboseLog:$VerboseLog
