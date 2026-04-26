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
    
    # robocopy ログの最後から統計情報を抽出（ロケール対応）
    # フォーマット例（英語）:
    #   Files : 123 copied, 45 updated, 6 deleted
    #   Extras : 3
    # フォーマット例（日本語）:
    #   ファイル:       248         1       247         0         0      8238
    
    $lines = $RobocopyOutput -split "`r?`n"
    
    foreach ($line in $lines) {
        # 英語パターン: "Files : 123 copied"
        if ($line -match "Files\s*:\s*(\d+)\s+copied") {
            $stats.Added = [int]$matches[1]
        }
        # 英語パターン: "123 updated"
        if ($line -match "updated[,\s]+(\d+)") {
            $stats.Updated = [int]$matches[1]
        }
        
        # 日本語パターン: "ファイル:       248         1       247         0         0      8238"
        # コピー済み（第2列目）を読む
        if ($line -match "^\s*ファイル:") {
            $parts = @($line -split "\s+" | Where-Object { $_ -and $_ -ne "ファイル:" })
            if ($parts.Count -ge 2) {
                # parts[0]=合計, parts[1]=コピー済み
                $stats.Added = [int]$parts[1]
            }
        }
        
        # 英語または日本語の "Extras" 行（削除ファイル）
        if ($line -match "Extras\s*:\s*(\d+)") {
            $stats.Deleted = [int]$matches[1]
        }
    }
    
    # 統計行が見つからない場合は、行ごとのカウントにフォールバック
    if ($stats.Added -eq 0 -and $stats.Updated -eq 0 -and $stats.Deleted -eq 0) {
        foreach ($line in $lines) {
            # 英語と日本語の両パターンに対応
            if ($line -match "^\s+(New File|新しいファイル)\s+") {
                $stats.Added++
            }
            elseif ($line -match "^\s+(Newer|新しい)\s+") {
                $stats.Updated++
            }
            elseif ($line -match "^\s+(EXTRA File|EXTRA)\s+") {
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

        # ドライラン時は統計情報とファイルリストをログファイルから抽出
        if ($WhatIfMode -and $statsLogPath -and (Test-Path -LiteralPath $statsLogPath)) {
            $logContent = Get-Content -LiteralPath $statsLogPath -Raw -Encoding UTF8
            $stats = Get-RobocopyStats -RobocopyOutput $logContent
            Write-SyncSummary -Added $stats.Added -Updated $stats.Updated -Deleted $stats.Deleted -DryRun:$true

            # ドライラン時のみファイル詳細を抽出
            $addedFiles = @()
            $updatedFiles = @()
            $deletedFiles = @()

            foreach ($line in $logContent -split "`n") {
                # robocopy ドライランログ形式: "New File", "Newer", "EXTRA File"
                if ($line -match "^\s+New File\s+") {
                    # New File の行からパスを抽出（最後のカラムがパス）
                    $parts = $line -split "\s{2,}" | Where-Object { $_ -and $_.Trim() }
                    if ($parts.Count -gt 1) {
                        $filePath = $parts[-1].Trim()
                        if ($filePath -and $filePath.Length -gt 0) {
                            $addedFiles += $filePath
                        }
                    }
                }
                elseif ($line -match "^\s+Newer\s+") {
                    # Newer の行からパスを抽出
                    $parts = $line -split "\s{2,}" | Where-Object { $_ -and $_.Trim() }
                    if ($parts.Count -gt 1) {
                        $filePath = $parts[-1].Trim()
                        if ($filePath -and $filePath.Length -gt 0) {
                            $updatedFiles += $filePath
                        }
                    }
                }
                elseif ($line -match "^\s+EXTRA File\s+") {
                    # EXTRA File の行からパスを抽出
                    $parts = $line -split "\s{2,}" | Where-Object { $_ -and $_.Trim() }
                    if ($parts.Count -gt 1) {
                        $filePath = $parts[-1].Trim()
                        if ($filePath -and $filePath.Length -gt 0) {
                            $deletedFiles += $filePath
                        }
                    }
                }
            }

            # ファイルリストを JSON 形式で出力（truncate）
            $addedTruncated = $addedFiles | Select-Object -First 20
            $updatedTruncated = $updatedFiles | Select-Object -First 20
            $deletedTruncated = $deletedFiles | Select-Object -First 20

            $addedJson = @($addedTruncated) | ConvertTo-Json -Compress
            $updatedJson = @($updatedTruncated) | ConvertTo-Json -Compress
            $deletedJson = @($deletedTruncated) | ConvertTo-Json -Compress

            Write-Host "SYNC_STATS:ADDED=$($stats.Added),UPDATED=$($stats.Updated),DELETED=$($stats.Deleted)"
            Write-Host "SYNC_FILES_DRY:ADDED=$addedJson"
            Write-Host "SYNC_FILES_DRY:UPDATED=$updatedJson"
            Write-Host "SYNC_FILES_DRY:DELETED=$deletedJson"

            # Overflow counters
            if ($addedFiles.Count -gt 20) {
                Write-Host "SYNC_FILES_OVERFLOW:ADDED_MORE=$($addedFiles.Count - 20)"
            }
            if ($updatedFiles.Count -gt 20) {
                Write-Host "SYNC_FILES_OVERFLOW:UPDATED_MORE=$($updatedFiles.Count - 20)"
            }
            if ($deletedFiles.Count -gt 20) {
                Write-Host "SYNC_FILES_OVERFLOW:DELETED_MORE=$($deletedFiles.Count - 20)"
            }
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
