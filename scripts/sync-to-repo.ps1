[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepoPath,

    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TemplateRelativePath = "repo-template\.github",
    # 共有用ドキュメントの雛形。target repo の docs/sessions に同期する。
    [string]$DocsSessionsRelativePath = "repo-template\docs\sessions",
    # 母艦の hooks/ を配布先にも展開する。空文字を渡すとスキップ。
    [string]$HooksRelativePath = ".github\hooks",
    # Git client hooks のテンプレート。target repo の .githooks に同期する。
    [string]$GitHooksRelativePath = "repo-template\.githooks",
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

function Warn-IfPathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Warning $Message
    }
}

function Test-RobocopyResult {
    param([int]$ExitCode)

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

    $verboseLogPath = $null

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
        $verboseLogPath = Join-Path ([System.IO.Path]::GetTempPath()) ("happy-env-robocopy-{0}.log" -f [guid]::NewGuid())
        $robocopyArgs += "/UNILOG:$verboseLogPath"
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

    try {
        if ($ShowVerboseLog) {
            & robocopy @robocopyArgs | Out-Null
        }
        else {
            & robocopy @robocopyArgs
        }
        $exitCode = $LASTEXITCODE

        if ($ShowVerboseLog -and $verboseLogPath -and (Test-Path -LiteralPath $verboseLogPath)) {
            $verboseLogContent = Get-Content -LiteralPath $verboseLogPath -Raw -Encoding Unicode
            if (-not [string]::IsNullOrWhiteSpace($verboseLogContent)) {
                Write-Host $verboseLogContent -NoNewline
            }
        }

        Test-RobocopyResult -ExitCode $exitCode

        if ($WhatIfMode) {
            Write-Host "DryRun completed. ExitCode=$exitCode" -ForegroundColor Yellow
        }
        else {
            Write-Host "Sync completed. ExitCode=$exitCode" -ForegroundColor Green
        }
    }
    finally {
        if ($verboseLogPath -and (Test-Path -LiteralPath $verboseLogPath)) {
            Remove-Item -LiteralPath $verboseLogPath -Force
        }
    }

    $global:LASTEXITCODE = 0
}

$targetRepoPath = [System.IO.Path]::GetFullPath($TargetRepoPath)
if (-not (Test-Path -LiteralPath $targetRepoPath)) {
    throw "Target repository path not found: $targetRepoPath"
}

# repo-template では .github/hooks を保持しない。
# repo 用 hooks の正本は母艦 .github/hooks で、Step 2 でのみ配布する。
$excludeDirs = @(
    ".git",
    ".vs",
    "hooks"
)

$excludeFiles = @(
    "*.local.json",
    "*.local.ps1"
)

# --- 1. repo-template/.github/ → 配布先 .github/ ---
Write-Section "Sync repo-template to target repository (.github)"

$sourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $TemplateRelativePath))
$destinationPath = Join-Path $targetRepoPath ".github"

Write-Host "Source      : $sourcePath"
Write-Host "Destination : $destinationPath"
Write-Host "Mirror      : $Mirror"
Write-Host "DryRun      : $DryRun"

$duplicateHooksPath = Join-Path $sourcePath "hooks"
Warn-IfPathExists `
    -Path $duplicateHooksPath `
    -Message "repo-template/.github/hooks is ignored. Use .github/hooks as the single source of truth for repository hooks."

Invoke-Robocopy `
    -Source $sourcePath `
    -Destination $destinationPath `
    -ExcludeDirs $excludeDirs `
    -ExcludeFiles $excludeFiles `
    -MirrorMode:$Mirror `
    -WhatIfMode:$DryRun `
    -ShowVerboseLog:$VerboseLog

# --- 2. .github/hooks/ → 配布先 .github/hooks/ （$HooksRelativePath が空ならスキップ）---
if (-not [string]::IsNullOrWhiteSpace($HooksRelativePath)) {
    Write-Section "Sync hooks to target repository (.github/hooks)"

    $hooksSourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $HooksRelativePath))
    $hooksDestinationPath = Join-Path $targetRepoPath ".github\hooks"

    Write-Host "Source      : $hooksSourcePath"
    Write-Host "Destination : $hooksDestinationPath"

    Invoke-Robocopy `
        -Source $hooksSourcePath `
        -Destination $hooksDestinationPath `
        -ExcludeFiles $excludeFiles `
        -MirrorMode:$Mirror `
        -WhatIfMode:$DryRun `
        -ShowVerboseLog:$VerboseLog
}

# --- 3. repo-template/.githooks/ → 配布先 .githooks/ ---
if (-not [string]::IsNullOrWhiteSpace($GitHooksRelativePath)) {
    Write-Section "Sync git hooks to target repository (.githooks)"

    $gitHooksSourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $GitHooksRelativePath))
    $gitHooksDestinationPath = Join-Path $targetRepoPath ".githooks"

    Write-Host "Source      : $gitHooksSourcePath"
    Write-Host "Destination : $gitHooksDestinationPath"

    Invoke-Robocopy `
        -Source $gitHooksSourcePath `
        -Destination $gitHooksDestinationPath `
        -MirrorMode:$Mirror `
        -WhatIfMode:$DryRun `
        -ShowVerboseLog:$VerboseLog
}

# --- 4. repo-template/docs/sessions/ → 配布先 docs/sessions/ ---
if (-not [string]::IsNullOrWhiteSpace($DocsSessionsRelativePath)) {
    $docsSessionsSourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $DocsSessionsRelativePath))
    if (Test-Path -LiteralPath $docsSessionsSourcePath) {
        Write-Section "Sync session docs scaffold to target repository (docs/sessions)"

        $docsSessionsDestinationPath = Join-Path $targetRepoPath "docs\sessions"

        Write-Host "Source      : $docsSessionsSourcePath"
        Write-Host "Destination : $docsSessionsDestinationPath"

        # docs/sessions は共有セッションログ用の append-only 領域なので、Mirror は使わない。
        if ($Mirror) {
            Write-Warning "docs/sessions sync is always non-mirror (append-only). -Mirror switch is ignored for this step."
        }

        Invoke-Robocopy `
            -Source $docsSessionsSourcePath `
            -Destination $docsSessionsDestinationPath `
            -MirrorMode:$false `
            -WhatIfMode:$DryRun `
            -ShowVerboseLog:$VerboseLog
    }
}
