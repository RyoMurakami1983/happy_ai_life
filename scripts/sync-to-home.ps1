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

function Warn-IfPathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Warning $Message
    }
}

function Write-HomeMirrorCompatibilityWarning {
    param([Parameter(Mandatory = $true)][switch]$WhatIfMode)

    $prefix = if ($WhatIfMode) { "DRY-RUN WARNING" } else { "WARNING" }
    Write-Warning "${prefix}: home sync では skills/、agents/、repo-template/、.github/hooks/ を常に template 一致の mirror-managed directory として扱います。"
    Write-Warning "${prefix}: -Mirror は互換オプションとして受け付けますが、home sync では追加効果を持ちません。"
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

function Copy-TrackedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [switch]$WhatIfMode
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source file not found: $Source"
    }

    $destinationDir = Split-Path -Parent $Destination
    if (-not [string]::IsNullOrWhiteSpace($destinationDir) -and -not (Test-Path -LiteralPath $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }

    if ($WhatIfMode) {
        Write-Host "Would copy $Source -> $Destination" -ForegroundColor Yellow
        return
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    Write-Host "Copied $Source -> $Destination" -ForegroundColor Green
}

Write-Section "Sync to HOME (.copilot)"

$sourcePath = Join-Path $SourceRoot $TemplateRelativePath
$sourcePath = [System.IO.Path]::GetFullPath($sourcePath)
$destinationPath = [System.IO.Path]::GetFullPath($DestinationPath)

Write-Host "Source      : $sourcePath"
Write-Host "Destination : $destinationPath"
Write-Host "Mirror      : $Mirror"
Write-Host "DryRun      : $DryRun"

$trackedDirectories = @(
    @{
        Source = (Join-Path $sourcePath "skills")
        Destination = (Join-Path $destinationPath "skills")
        MirrorMode = $true
        Label = "skills/ (mirror-managed)"
    },
    @{
        Source = (Join-Path $sourcePath "agents")
        Destination = (Join-Path $destinationPath "agents")
        MirrorMode = $true
        Label = "agents/ (mirror-managed)"
    },
    @{
        Source = (Join-Path $SourceRoot "repo-template")
        Destination = (Join-Path $destinationPath "repo-template")
        MirrorMode = $true
        Label = "repo-template/ (mirror-managed)"
    },
    @{
        Source = (Join-Path (Join-Path $SourceRoot ".github") "hooks")
        Destination = (Join-Path (Join-Path $destinationPath ".github") "hooks")
        MirrorMode = $true
        Label = ".github/hooks/ (mirror-managed)"
    },
    # Shared furikaeri archives are part of the writable home template.
    @{
        Source = (Join-Path (Join-Path $sourcePath "docs") "furikaeri")
        Destination = (Join-Path (Join-Path $destinationPath "docs") "furikaeri")
        MirrorMode = $false
        Label = "docs/furikaeri (copy-only)"
    }
)

$trackedFiles = @(
    @{ Source = (Join-Path $sourcePath "copilot-instructions.md"); Destination = (Join-Path $destinationPath "copilot-instructions.md") },
    @{ Source = (Join-Path $sourcePath "mcp-config.sample.json"); Destination = (Join-Path $destinationPath "mcp-config.sample.json") },
    @{ Source = (Join-Path (Join-Path $SourceRoot "scripts") "sync-to-repo.ps1"); Destination = (Join-Path (Join-Path $destinationPath "scripts") "sync-to-repo.ps1") },
    @{ Source = (Join-Path (Join-Path $SourceRoot "scripts") "install-git-hooks.ps1"); Destination = (Join-Path (Join-Path $destinationPath "scripts") "install-git-hooks.ps1") },
    @{ Source = (Join-Path (Join-Path $SourceRoot "scripts") "repo-secure-check.ps1"); Destination = (Join-Path (Join-Path $destinationPath "scripts") "repo-secure-check.ps1") }
)

$unsupportedHooksPath = Join-Path $sourcePath "hooks"
Warn-IfPathExists `
    -Path $unsupportedHooksPath `
    -Message "home-template/.copilot/hooks is ignored. Officially supported hook configuration is repository-scoped under .github/hooks."

if (-not (Test-Path -LiteralPath $destinationPath)) {
    New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
}

if ($Mirror) {
    Write-HomeMirrorCompatibilityWarning -WhatIfMode:$DryRun
}

foreach ($entry in $trackedDirectories) {
    Write-Host "Directory   : $($entry.Label)" -ForegroundColor DarkGray
    Invoke-Robocopy `
        -Source $entry.Source `
        -Destination $entry.Destination `
        -MirrorMode:$entry.MirrorMode `
        -WhatIfMode:$DryRun `
        -ShowVerboseLog:$VerboseLog
}

foreach ($entry in $trackedFiles) {
    Copy-TrackedFile `
        -Source $entry.Source `
        -Destination $entry.Destination `
        -WhatIfMode:$DryRun
}

$mcpSamplePath = Join-Path $destinationPath "mcp-config.sample.json"
$mcpLivePath = Join-Path $destinationPath "mcp-config.json"
if (-not (Test-Path -LiteralPath $mcpLivePath) -and (Test-Path -LiteralPath $mcpSamplePath)) {
    Write-Warning "mcp-config.json is user-owned and was not synced. Copy mcp-config.sample.json to mcp-config.json in $destinationPath and fill your API keys."
}
