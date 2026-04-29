[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepoPath,

    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TemplateRelativePath = "repo-template\.github",
    # 共有用ふりかえりドキュメントの雛形。target repo の docs/furikaeri に同期する。
    [Alias("DocsSessionsRelativePath")]
    [string]$DocsFurikaeriRelativePath = "repo-template\docs\furikaeri",
    # 母艦の hooks/ を配布先にも展開する。空文字を渡すとスキップ。
    [string]$HooksRelativePath = ".github\hooks",
    # Copilot hooks の配布範囲。sessionStart/sessionEnd は既定では封印し、明示時のみ配布する。
    [ValidateSet("SafetyOnly", "All", "None")]
    [string]$HooksMode = "SafetyOnly",
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

function Get-TextFileContent {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite
    )

    try {
        $reader = [System.IO.StreamReader]::new(
            $stream,
            [System.Text.UTF8Encoding]::new($false),
            $true
        )
        try {
            return $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-TextFileLines {
    param([Parameter(Mandatory = $true)][string]$Path)

    $content = Get-TextFileContent -Path $Path
    if ([string]::IsNullOrEmpty($content)) {
        return @()
    }

    return $content -split "`r?`n"
}

function Write-TextFileContent {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $directory = Split-Path -Path $Path -Parent
    if (-not [string]::IsNullOrWhiteSpace($directory) -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::Read
    )

    try {
        $writer = [System.IO.StreamWriter]::new(
            $stream,
            [System.Text.UTF8Encoding]::new($false)
        )
        try {
            $writer.Write($Content)
        }
        finally {
            $writer.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Write-TextFileLines {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Lines
    )

    Write-TextFileContent -Path $Path -Content (($Lines -join [System.Environment]::NewLine) + [System.Environment]::NewLine)
}

function Merge-AppendOnlyFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [switch]$WhatIfMode
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source file not found: $Source"
    }

    $sourceLines = @(Get-TextFileLines -Path $Source)

    if ($WhatIfMode) {
        if (Test-Path -LiteralPath $Destination) {
            $destinationLines = @(Get-TextFileLines -Path $Destination)
            $existingLines = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)

            foreach ($line in $destinationLines) {
                if (-not [string]::IsNullOrWhiteSpace($line)) {
                    [void]$existingLines.Add($line)
                }
            }

            $missingCount = 0
            foreach ($line in $sourceLines) {
                if ([string]::IsNullOrWhiteSpace($line)) {
                    continue
                }

                if (-not $existingLines.Contains($line)) {
                    $missingCount += 1
                }
            }

            if ($missingCount -eq 0) {
                Write-Host "No append-only changes needed for $Destination" -ForegroundColor Yellow
            }
            else {
                Write-Host "Would merge $missingCount missing line(s) into $Destination" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "Would create $Destination from $Source" -ForegroundColor Yellow
        }
        return
    }

    if (-not (Test-Path -LiteralPath $Destination)) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        return
    }

    $existingLines = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $destinationLines = @(Get-TextFileLines -Path $Destination)

    foreach ($line in $destinationLines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            [void]$existingLines.Add($line)
        }
    }

    $linesToAppend = New-Object System.Collections.Generic.List[string]
    foreach ($line in $sourceLines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if (-not $existingLines.Contains($line)) {
            [void]$linesToAppend.Add($line)
        }
    }

    if ($linesToAppend.Count -eq 0) {
        return
    }

    $destinationContent = Get-TextFileContent -Path $Destination
    $appendContent = ''
    if ($destinationContent.Length -gt 0 -and -not $destinationContent.EndsWith([System.Environment]::NewLine)) {
        $appendContent += [System.Environment]::NewLine
    }

    $appendContent += (($linesToAppend -join [System.Environment]::NewLine) + [System.Environment]::NewLine)
    [System.IO.File]::AppendAllText($Destination, $appendContent, [System.Text.UTF8Encoding]::new($false))
}

function Remove-SealedSessionContinuityArtifacts {
    param(
        [Parameter(Mandatory = $true)][string]$TargetRepoRoot,
        [switch]$WhatIfMode
    )

    $sealedPaths = @(
        (Join-Path $TargetRepoRoot ".github\hooks\session-continuity.json"),
        (Join-Path $TargetRepoRoot ".github\instructions\session-context.instructions.md")
    )

    foreach ($sealedPath in $sealedPaths) {
        if (-not (Test-Path -LiteralPath $sealedPath -PathType Leaf)) {
            continue
        }

        if ($WhatIfMode) {
            Write-Host "Would remove sealed session continuity artifact: $sealedPath" -ForegroundColor Yellow
            continue
        }

        Remove-Item -LiteralPath $sealedPath -Force
        Write-Host "Removed sealed session continuity artifact: $sealedPath" -ForegroundColor Yellow
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
# sessionStart/sessionEnd の自動保存は封印済みのため、既定では safety guard のみ配布する。
$excludeDirs = @(
    ".git",
    ".vs",
    "hooks"
)

$excludeFiles = @(
    "*.local.json",
    "*.local.ps1",
    # .github/.gitignore は既存内容を壊さず、後段で追記マージする。
    ".gitignore"
)

# --- 1. repo-template/.github/ → 配布先 .github/ ---
Write-Section "Sync repo-template to target repository (.github)"

$sourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $TemplateRelativePath))
$destinationPath = Join-Path $targetRepoPath ".github"

Write-Host "Source      : $sourcePath"
Write-Host "Destination : $destinationPath"
Write-Host "Mirror      : $Mirror"
Write-Host "DryRun      : $DryRun"
Write-Host "HooksMode   : $HooksMode"

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

$githubGitIgnoreSourcePath = [System.IO.Path]::GetFullPath((Join-Path $sourcePath ".gitignore"))
$githubGitIgnoreDestinationPath = Join-Path $destinationPath ".gitignore"

Merge-AppendOnlyFile `
    -Source $githubGitIgnoreSourcePath `
    -Destination $githubGitIgnoreDestinationPath `
    -WhatIfMode:$DryRun

# --- 2. .github/hooks/ → 配布先 .github/hooks/ （$HooksRelativePath が空、または HooksMode=None ならスキップ）---
$shouldSyncHooks = (-not [string]::IsNullOrWhiteSpace($HooksRelativePath)) -and $HooksMode -ne "None"
if ($shouldSyncHooks) {
    Write-Section "Sync hooks to target repository (.github/hooks)"

    $hooksSourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $HooksRelativePath))
    $hooksDestinationPath = Join-Path $targetRepoPath ".github\hooks"
    $hooksExcludeFiles = @($excludeFiles)
    if ($HooksMode -eq "SafetyOnly") {
        $hooksExcludeFiles += "session-continuity.json"
    }

    Write-Host "Source      : $hooksSourcePath"
    Write-Host "Destination : $hooksDestinationPath"
    Write-Host "HooksMode   : $HooksMode"
    if ($HooksMode -eq "SafetyOnly") {
        Write-Host "Note        : sessionStart/sessionEnd continuity hooks are sealed and excluded by default." -ForegroundColor Yellow
    }

    Invoke-Robocopy `
        -Source $hooksSourcePath `
        -Destination $hooksDestinationPath `
        -ExcludeFiles $hooksExcludeFiles `
        -MirrorMode:$Mirror `
        -WhatIfMode:$DryRun `
        -ShowVerboseLog:$VerboseLog

}

if ($shouldSyncHooks -and $HooksMode -eq "SafetyOnly") {
    Remove-SealedSessionContinuityArtifacts `
        -TargetRepoRoot $targetRepoPath `
        -WhatIfMode:$DryRun
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

# --- 4. repo-template/docs/furikaeri/ → 配布先 docs/furikaeri/ ---
if (-not [string]::IsNullOrWhiteSpace($DocsFurikaeriRelativePath)) {
    $docsFurikaeriSourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $DocsFurikaeriRelativePath))
    if (Test-Path -LiteralPath $docsFurikaeriSourcePath) {
        Write-Section "Sync furikaeri docs scaffold to target repository (docs/furikaeri)"

        $docsFurikaeriDestinationPath = Join-Path $targetRepoPath "docs\furikaeri"

        Write-Host "Source      : $docsFurikaeriSourcePath"
        Write-Host "Destination : $docsFurikaeriDestinationPath"

        # docs/furikaeri は共有ふりかえりログ用の append-only 領域なので、Mirror は使わない。
        if ($Mirror) {
            Write-Warning "docs/furikaeri sync is always non-mirror (append-only). -Mirror switch is ignored for this step."
        }

        Invoke-Robocopy `
            -Source $docsFurikaeriSourcePath `
            -Destination $docsFurikaeriDestinationPath `
            -MirrorMode:$false `
            -WhatIfMode:$DryRun `
            -ShowVerboseLog:$VerboseLog
    }
}
