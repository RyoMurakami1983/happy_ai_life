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

function Write-SyncSummary {
    param(
        [int]$Added,
        [int]$Updated,
        [int]$Deleted,
        [bool]$DryRun
    )
    
    $summary = "追加 $Added 個 / 更新 $Updated 個 / 削除 $Deleted 個"
    
    if ($DryRun) {
        Write-Host ""
        Write-Host "✓ ドライラン確認: $summary" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "✓ 同期完了: $summary" -ForegroundColor Green
    }
}

function Write-SyncError {
    param([string]$ErrorMessage)
    
    Write-Host ""
    Write-Host "✗ 同期失敗: $ErrorMessage" -ForegroundColor Red
}

function Get-RobocopyStats {
    param([string]$RobocopyOutput)
    
    $stats = @{ Added = 0; Updated = 0; Deleted = 0 }
    
    # robocopy ログの最後から統計情報を抽出
    # フォーマット例:
    #   Files : 123 copied, 45 updated, 6 deleted
    #   Extras : 3
    
    $lines = $RobocopyOutput -split "`r?`n"
    
    foreach ($line in $lines) {
        # "Files :" という行を探す
        if ($line -match "Files\s*:\s*(\d+)\s+copied") {
            $stats.Added = [int]$matches[1]
        }
        if ($line -match "updated[,\s]+(\d+)") {
            $stats.Updated = [int]$matches[1]
        }
        
        # "Extras :" という行を削除ファイル数として扱う
        if ($line -match "Extras\s*:\s*(\d+)") {
            $stats.Deleted = [int]$matches[1]
        }
    }
    
    # 統計行が見つからない場合は、行ごとのカウントにフォールバック
    if ($stats.Added -eq 0 -and $stats.Updated -eq 0 -and $stats.Deleted -eq 0) {
        foreach ($line in $lines) {
            if ($line -match "^\s+New File\s+") {
                $stats.Added++
            }
            elseif ($line -match "^\s+Newer\s+") {
                $stats.Updated++
            }
            elseif ($line -match "^\s+EXTRA File\s+") {
                $stats.Deleted++
            }
        }
    }
    
    return $stats
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
        "/XJ"
    )

    if ($MirrorMode) {
        $robocopyArgs += "/MIR"
    }

    if ($WhatIfMode) {
        $robocopyArgs += "/L"
        # ドライラン時は統計情報を取得するため、抑制フラグを使わない
    }
    else {
        # 実行時のみ冗長出力を抑制（本運用）
        $robocopyArgs += "/NFL"
        $robocopyArgs += "/NDL"
        $robocopyArgs += "/NP"
        $robocopyArgs += "/NJH"
        $robocopyArgs += "/NJS"
    }

    $verboseLogPath = $null
    $statsLogPath = $null

    # ドライラン時はログファイルを出力して統計抽出
    if ($WhatIfMode -and -not $ShowVerboseLog) {
        $statsLogPath = Join-Path ([System.IO.Path]::GetTempPath()) ("happy-env-robocopy-stats-{0}.log" -f [guid]::NewGuid())
        # 統計用ログは UNILOG で正確なエンコーディング保証
        $robocopyArgs += "/UNILOG:$statsLogPath"
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
        $verboseLogPath = Join-Path ([System.IO.Path]::GetTempPath()) ("happy-env-robocopy-{0}.log" -f [guid]::NewGuid())
        $robocopyArgs += "/UNILOG:$verboseLogPath"
    }

    try {
        if ($ShowVerboseLog) {
            & robocopy @robocopyArgs | Out-Null
        }
        else {
            # 通常モード：robocopy を実行
            & robocopy @robocopyArgs | Out-Null
        }
        $exitCode = $LASTEXITCODE

        if ($ShowVerboseLog -and $verboseLogPath -and (Test-Path -LiteralPath $verboseLogPath)) {
            $verboseLogContent = Get-Content -LiteralPath $verboseLogPath -Raw -Encoding UTF8
            if (-not [string]::IsNullOrWhiteSpace($verboseLogContent)) {
                Write-Host $verboseLogContent -NoNewline
            }
        }

        Test-RobocopyResult -ExitCode $exitCode

        # ドライラン時は統計情報をログファイルから抽出
        if ($WhatIfMode -and $statsLogPath -and (Test-Path -LiteralPath $statsLogPath)) {
            $logContent = Get-Content -LiteralPath $statsLogPath -Raw -Encoding UTF8
            $stats = Get-RobocopyStats -RobocopyOutput $logContent
            Write-SyncSummary -Added $stats.Added -Updated $stats.Updated -Deleted $stats.Deleted -DryRun:$true
        }
        else {
            # ログが取得できなかった場合のフォールバック
            if ($WhatIfMode) {
                Write-Host ""
                Write-Host "✓ ドライラン完了" -ForegroundColor Green
            }
            else {
                Write-Host ""
                Write-Host "✓ 同期完了" -ForegroundColor Green
            }
        }
    }
    finally {
        if ($verboseLogPath -and (Test-Path -LiteralPath $verboseLogPath)) {
            Remove-Item -LiteralPath $verboseLogPath -Force -ErrorAction SilentlyContinue
        }
        if ($statsLogPath -and (Test-Path -LiteralPath $statsLogPath)) {
            Remove-Item -LiteralPath $statsLogPath -Force -ErrorAction SilentlyContinue
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

Write-Section "ホーム同期"

$sourcePath = Join-Path $SourceRoot $TemplateRelativePath
$sourcePath = [System.IO.Path]::GetFullPath($sourcePath)
$destinationPath = [System.IO.Path]::GetFullPath($DestinationPath)

Write-Host ""
Write-Host "準備完了。ホーム同期は managed directory を template 一致へ同期し、"
Write-Host "mcp-config.json や docs/furikaeri など user-owned 領域は保護します。"
Write-Host "実行中..."
Write-Host ""

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
    Write-Host ""
    Write-Host "◆ $($entry.Label)" -ForegroundColor Cyan
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
