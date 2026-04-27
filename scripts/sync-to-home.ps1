[CmdletBinding()]
param(
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TemplateRelativePath = "home-template\.copilot",
    [string]$DestinationPath = (Join-Path $HOME ".copilot"),
    [string]$ArchiveRoot = (Join-Path $HOME "copilot_archives"),
    [string]$PythonExecutable = "",
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
        [bool]$DryRunMode
    )

    $summary = "追加 $Added 個 / 更新 $Updated 個 / 削除 $Deleted 個"

    Write-Host ""
    if ($DryRunMode) {
        Write-Host "✓ ドライラン確認: $summary" -ForegroundColor Green
    }
    else {
        Write-Host "✓ 同期完了: $summary" -ForegroundColor Green
    }
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
    Write-Warning "${prefix}: -Mirror は互換オプションです。home sync の managed surface はスクリプト定義どおりに同期されます。"
}

function Resolve-HomeTemplateRoot {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRootPath,
        [Parameter(Mandatory = $true)][string]$TemplatePath
    )

    $nestedTemplatePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRootPath $TemplatePath))
    if (Test-Path -LiteralPath $nestedTemplatePath) {
        return $nestedTemplatePath
    }

    $packagedIndicators = @(
        (Join-Path $SourceRootPath "skills"),
        (Join-Path $SourceRootPath "agents"),
        (Join-Path $SourceRootPath "copilot-instructions.md")
    )
    $isPackagedRoot = $true
    foreach ($path in $packagedIndicators) {
        if (-not (Test-Path -LiteralPath $path)) {
            $isPackagedRoot = $false
            break
        }
    }

    if ($isPackagedRoot) {
        return [System.IO.Path]::GetFullPath($SourceRootPath)
    }

    throw "Home template root not found. SourceRoot=$SourceRootPath TemplateRelativePath=$TemplatePath"
}

function Resolve-PythonCommand {
    param([string]$RequestedExecutable)

    if (-not [string]::IsNullOrWhiteSpace($RequestedExecutable)) {
        return @($RequestedExecutable)
    }

    foreach ($candidate in @("python", "python3")) {
        $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($resolved) {
            return @($resolved.Source)
        }
    }

    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @($pyLauncher.Source, "-3")
    }

    throw "Python executable not found. Pass -PythonExecutable or install python/py launcher."
}

function New-PreviewState {
    return @{
        Added = New-Object System.Collections.Generic.List[string]
        Updated = New-Object System.Collections.Generic.List[string]
        Deleted = New-Object System.Collections.Generic.List[string]
    }
}

function Add-PreviewItems {
    param(
        [Parameter(Mandatory = $true)]$PreviewState,
        [Parameter(Mandatory = $true)][ValidateSet("Added", "Updated", "Deleted")][string]$Bucket,
        [AllowEmptyCollection()][string[]]$Items = @()
    )

    foreach ($item in $Items) {
        [void]$PreviewState[$Bucket].Add($item)
    }
}

function Normalize-PreviewPath {
    param(
        [string]$RootPrefix,
        [string]$RelativePath
    )

    $normalizedRelative = $RelativePath.Replace('\', '/')
    if ([string]::IsNullOrWhiteSpace($RootPrefix)) {
        return $normalizedRelative
    }
    if ([string]::IsNullOrWhiteSpace($normalizedRelative)) {
        return $RootPrefix.Replace('\', '/')
    }
    return ("{0}/{1}" -f $RootPrefix.Replace('\', '/').TrimEnd('/'), $normalizedRelative.TrimStart('/'))
}

function Ensure-ParentDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    $parent = Split-Path -Path $Path -Parent
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

function Remove-PathItem {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer) {
        Remove-Item -LiteralPath $Path -Recurse -Force
        return
    }

    Remove-Item -LiteralPath $Path -Force
}

function Copy-PathItem {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $sourceItem = Get-Item -LiteralPath $Source -Force
    Ensure-ParentDirectory -Path $Destination

    if ($sourceItem.PSIsContainer) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
        return
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Backup-PathItem {
    param(
        [Parameter(Mandatory = $true)][string]$ExistingPath,
        [Parameter(Mandatory = $true)][string]$ArchivePath
    )

    Remove-PathItem -Path $ArchivePath
    if (-not (Test-Path -LiteralPath $ExistingPath)) {
        return
    }

    Copy-PathItem -Source $ExistingPath -Destination $ArchivePath
}

function Get-PathFileMap {
    param([Parameter(Mandatory = $true)][string]$Root)

    $map = @{}
    if (-not (Test-Path -LiteralPath $Root)) {
        return $map
    }

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    foreach ($file in Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File) {
        $relative = [System.IO.Path]::GetRelativePath($resolvedRoot, $file.FullName)
        $map[$relative] = $file.FullName
    }
    return $map
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-DirectorySyncPlan {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$PreviewRoot,
        [switch]$MirrorMode
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source path not found: $Source"
    }

    $actions = New-Object System.Collections.Generic.List[object]
    $added = New-Object System.Collections.Generic.List[string]
    $updated = New-Object System.Collections.Generic.List[string]
    $deleted = New-Object System.Collections.Generic.List[string]

    $sourceFiles = Get-PathFileMap -Root $Source
    $destinationFiles = Get-PathFileMap -Root $Destination

    foreach ($relativePath in $sourceFiles.Keys | Sort-Object) {
        $sourceFile = $sourceFiles[$relativePath]
        $destinationFile = Join-Path $Destination $relativePath
        $previewPath = Normalize-PreviewPath -RootPrefix $PreviewRoot -RelativePath $relativePath
        if (-not $destinationFiles.ContainsKey($relativePath)) {
            [void]$added.Add($previewPath)
            [void]$actions.Add([pscustomobject]@{
                    Kind = "copy-file"
                    Source = $sourceFile
                    Destination = $destinationFile
                })
            continue
        }

        if ((Get-FileSha256 -Path $sourceFile) -ne (Get-FileSha256 -Path $destinationFiles[$relativePath])) {
            [void]$updated.Add($previewPath)
            [void]$actions.Add([pscustomobject]@{
                    Kind = "copy-file"
                    Source = $sourceFile
                    Destination = $destinationFile
                })
        }
    }

    if ($MirrorMode) {
        foreach ($relativePath in $destinationFiles.Keys | Sort-Object) {
            if ($sourceFiles.ContainsKey($relativePath)) {
                continue
            }

            [void]$deleted.Add((Normalize-PreviewPath -RootPrefix $PreviewRoot -RelativePath $relativePath))
            [void]$actions.Add([pscustomobject]@{
                    Kind = "delete-file"
                    Source = $null
                    Destination = $destinationFiles[$relativePath]
                })
        }
    }

    return [pscustomobject]@{
        Label = $PreviewRoot
        Actions = $actions.ToArray()
        Added = $added.ToArray()
        Updated = $updated.ToArray()
        Deleted = $deleted.ToArray()
        MirrorMode = $MirrorMode.IsPresent
        DestinationRoot = $Destination
    }
}

function Get-TrackedFilePlan {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$PreviewPath
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source file not found: $Source"
    }

    $actions = New-Object System.Collections.Generic.List[object]
    $added = New-Object System.Collections.Generic.List[string]
    $updated = New-Object System.Collections.Generic.List[string]

    if (-not (Test-Path -LiteralPath $Destination)) {
        [void]$added.Add($PreviewPath)
        [void]$actions.Add([pscustomobject]@{
                Kind = "copy-file"
                Source = $Source
                Destination = $Destination
            })
    }
    elseif ((Get-FileSha256 -Path $Source) -ne (Get-FileSha256 -Path $Destination)) {
        [void]$updated.Add($PreviewPath)
        [void]$actions.Add([pscustomobject]@{
                Kind = "copy-file"
                Source = $Source
                Destination = $Destination
            })
    }

    return [pscustomobject]@{
        Label = $PreviewPath
        Actions = $actions.ToArray()
        Added = $added.ToArray()
        Updated = $updated.ToArray()
        Deleted = @()
        MirrorMode = $false
        DestinationRoot = Split-Path -Path $Destination -Parent
    }
}

function Remove-EmptyDirectories {
    param([Parameter(Mandatory = $true)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root)) {
        return
    }

    $directories = Get-ChildItem -LiteralPath $Root -Directory -Recurse | Sort-Object FullName -Descending
    foreach ($directory in $directories) {
        $children = @(Get-ChildItem -LiteralPath $directory.FullName -Force)
        if ($children.Count -eq 0) {
            Remove-Item -LiteralPath $directory.FullName -Force
        }
    }
}

function Invoke-FileAction {
    param([Parameter(Mandatory = $true)]$Action)

    switch ($Action.Kind) {
        "copy-file" {
            Remove-PathItem -Path $Action.Destination
            Copy-PathItem -Source $Action.Source -Destination $Action.Destination
        }
        "delete-file" {
            Remove-PathItem -Path $Action.Destination
        }
        default {
            throw "Unsupported file action kind: $($Action.Kind)"
        }
    }
}

function Invoke-PlannerAction {
    param([Parameter(Mandatory = $true)]$Action)

    switch ($Action.kind) {
        "copy-skill" {
            Remove-PathItem -Path $Action.destination
            Copy-PathItem -Source $Action.source -Destination $Action.destination
        }
        "update-skill" {
            Backup-PathItem -ExistingPath $Action.destination -ArchivePath $Action.archive
            Remove-PathItem -Path $Action.destination
            Copy-PathItem -Source $Action.source -Destination $Action.destination
        }
        "preserve-skill-extra" {
            return
        }
        "copy-agent" {
            Remove-PathItem -Path $Action.destination
            Copy-PathItem -Source $Action.source -Destination $Action.destination
        }
        "update-agent" {
            Backup-PathItem -ExistingPath $Action.destination -ArchivePath $Action.archive
            Remove-PathItem -Path $Action.destination
            Copy-PathItem -Source $Action.source -Destination $Action.destination
        }
        "preserve-agent-extra" {
            return
        }
        default {
            throw "Unsupported planner action kind: $($Action.kind)"
        }
    }
}

function Write-SyncMarkers {
    param(
        [Parameter(Mandatory = $true)]$PreviewState,
        [switch]$WhatIfMode
    )

    $added = @($PreviewState.Added)
    $updated = @($PreviewState.Updated)
    $deleted = @($PreviewState.Deleted)

    Write-Host "SYNC_STATS:ADDED=$($added.Count),UPDATED=$($updated.Count),DELETED=$($deleted.Count)"

    if (-not $WhatIfMode) {
        return
    }

    $addedPreviewItems = @($added | Select-Object -First 20)
    $updatedPreviewItems = @($updated | Select-Object -First 20)
    $deletedPreviewItems = @($deleted | Select-Object -First 20)

    $addedPreview = if ($addedPreviewItems.Count -eq 0) { "[]" } else { ConvertTo-Json -InputObject ([object[]]$addedPreviewItems) -Compress }
    $updatedPreview = if ($updatedPreviewItems.Count -eq 0) { "[]" } else { ConvertTo-Json -InputObject ([object[]]$updatedPreviewItems) -Compress }
    $deletedPreview = if ($deletedPreviewItems.Count -eq 0) { "[]" } else { ConvertTo-Json -InputObject ([object[]]$deletedPreviewItems) -Compress }

    Write-Host "SYNC_FILES_DRY:ADDED=$addedPreview"
    Write-Host "SYNC_FILES_DRY:UPDATED=$updatedPreview"
    Write-Host "SYNC_FILES_DRY:DELETED=$deletedPreview"

    if ($added.Count -gt 20) {
        Write-Host "SYNC_FILES_OVERFLOW:ADDED_MORE=$($added.Count - 20)"
    }
    if ($updated.Count -gt 20) {
        Write-Host "SYNC_FILES_OVERFLOW:UPDATED_MORE=$($updated.Count - 20)"
    }
    if ($deleted.Count -gt 20) {
        Write-Host "SYNC_FILES_OVERFLOW:DELETED_MORE=$($deleted.Count - 20)"
    }
}

function Invoke-PythonPlanner {
    param(
        [Parameter(Mandatory = $true)][string]$PlannerScriptPath,
        [Parameter(Mandatory = $true)][string]$PlannerSourceRoot,
        [Parameter(Mandatory = $true)][string]$PlannerDestinationRoot,
        [Parameter(Mandatory = $true)][string]$PlannerArchiveRoot,
        [Parameter(Mandatory = $true)][string[]]$PythonCommand
    )

    if (-not (Test-Path -LiteralPath $PlannerScriptPath)) {
        throw "Planner script not found: $PlannerScriptPath"
    }

    $command = @($PythonCommand + @(
            $PlannerScriptPath,
            "--source-root", $PlannerSourceRoot,
            "--destination-root", $PlannerDestinationRoot,
            "--archive-root", $PlannerArchiveRoot
        ))

    $output = & $command[0] $command[1..($command.Count - 1)] 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "home_sync_planner.py failed.`n$($output -join [System.Environment]::NewLine)"
    }

    return ($output -join [System.Environment]::NewLine) | ConvertFrom-Json -Depth 8
}

Write-Section "ホーム同期"

$sourceRootPath = [System.IO.Path]::GetFullPath($SourceRoot)
$destinationPath = [System.IO.Path]::GetFullPath($DestinationPath)
$templateRoot = Resolve-HomeTemplateRoot -SourceRootPath $sourceRootPath -TemplatePath $TemplateRelativePath
$archiveRoot = [System.IO.Path]::GetFullPath($ArchiveRoot)
$plannerScriptPath = Join-Path (Join-Path $sourceRootPath "scripts") "home_sync_planner.py"
$pythonCommand = Resolve-PythonCommand -RequestedExecutable $PythonExecutable

Write-Host ""
Write-Host "準備完了。skills/ と agents/ は filesystem diff + archive 付きで同期し、"
Write-Host "repo-template/ と .github/hooks/ は managed surface として比較同期します。"
Write-Host "実行中..."
Write-Host ""

$unsupportedHooksPath = Join-Path $templateRoot "hooks"
Warn-IfPathExists `
    -Path $unsupportedHooksPath `
    -Message "home-template/.copilot/hooks is ignored. Officially supported hook configuration is repository-scoped under .github/hooks."

if (-not (Test-Path -LiteralPath $destinationPath)) {
    New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
}

if ($Mirror) {
    Write-HomeMirrorCompatibilityWarning -WhatIfMode:$DryRun
}

$previewState = New-PreviewState

Write-Host ""
Write-Host "◆ skills/ + agents/ (planner-managed)" -ForegroundColor Cyan
$plannerResult = Invoke-PythonPlanner `
    -PlannerScriptPath $plannerScriptPath `
    -PlannerSourceRoot $sourceRootPath `
    -PlannerDestinationRoot $destinationPath `
    -PlannerArchiveRoot $archiveRoot `
    -PythonCommand $pythonCommand

$plannerPreview = $plannerResult.preview
Add-PreviewItems -PreviewState $previewState -Bucket Added -Items @($plannerPreview.added)
Add-PreviewItems -PreviewState $previewState -Bucket Updated -Items @($plannerPreview.updated)
Add-PreviewItems -PreviewState $previewState -Bucket Deleted -Items @($plannerPreview.deleted)

$directoryPlans = @(
    [pscustomobject]@{
        Label = "repo-template/ (managed)"
        Plan = (Get-DirectorySyncPlan -Source (Join-Path $sourceRootPath "repo-template") -Destination (Join-Path $destinationPath "repo-template") -PreviewRoot "repo-template" -MirrorMode)
    },
    [pscustomobject]@{
        Label = ".github/hooks/ (managed)"
        Plan = (Get-DirectorySyncPlan -Source (Join-Path (Join-Path $sourceRootPath ".github") "hooks") -Destination (Join-Path (Join-Path $destinationPath ".github") "hooks") -PreviewRoot ".github/hooks" -MirrorMode)
    },
    [pscustomobject]@{
        Label = "docs/furikaeri (copy-only)"
        Plan = (Get-DirectorySyncPlan -Source (Join-Path (Join-Path $templateRoot "docs") "furikaeri") -Destination (Join-Path (Join-Path $destinationPath "docs") "furikaeri") -PreviewRoot "docs/furikaeri")
    }
)

$trackedFilePlans = @(
    [pscustomobject]@{
        Label = "copilot-instructions.md"
        Plan = (Get-TrackedFilePlan -Source (Join-Path $templateRoot "copilot-instructions.md") -Destination (Join-Path $destinationPath "copilot-instructions.md") -PreviewPath "copilot-instructions.md")
    },
    [pscustomobject]@{
        Label = "mcp-config.sample.json"
        Plan = (Get-TrackedFilePlan -Source (Join-Path $templateRoot "mcp-config.sample.json") -Destination (Join-Path $destinationPath "mcp-config.sample.json") -PreviewPath "mcp-config.sample.json")
    },
    [pscustomobject]@{
        Label = "scripts/sync-to-repo.ps1"
        Plan = (Get-TrackedFilePlan -Source (Join-Path (Join-Path $sourceRootPath "scripts") "sync-to-repo.ps1") -Destination (Join-Path (Join-Path $destinationPath "scripts") "sync-to-repo.ps1") -PreviewPath "scripts/sync-to-repo.ps1")
    },
    [pscustomobject]@{
        Label = "scripts/install-git-hooks.ps1"
        Plan = (Get-TrackedFilePlan -Source (Join-Path (Join-Path $sourceRootPath "scripts") "install-git-hooks.ps1") -Destination (Join-Path (Join-Path $destinationPath "scripts") "install-git-hooks.ps1") -PreviewPath "scripts/install-git-hooks.ps1")
    },
    [pscustomobject]@{
        Label = "scripts/repo-secure-check.ps1"
        Plan = (Get-TrackedFilePlan -Source (Join-Path (Join-Path $sourceRootPath "scripts") "repo-secure-check.ps1") -Destination (Join-Path (Join-Path $destinationPath "scripts") "repo-secure-check.ps1") -PreviewPath "scripts/repo-secure-check.ps1")
    },
    [pscustomobject]@{
        Label = "scripts/home_sync_planner.py"
        Plan = (Get-TrackedFilePlan -Source (Join-Path (Join-Path $sourceRootPath "scripts") "home_sync_planner.py") -Destination (Join-Path (Join-Path $destinationPath "scripts") "home_sync_planner.py") -PreviewPath "scripts/home_sync_planner.py")
    }
)

foreach ($entry in $directoryPlans) {
    Write-Host ""
    Write-Host "◆ $($entry.Label)" -ForegroundColor Cyan
    Add-PreviewItems -PreviewState $previewState -Bucket Added -Items @($entry.Plan.Added)
    Add-PreviewItems -PreviewState $previewState -Bucket Updated -Items @($entry.Plan.Updated)
    Add-PreviewItems -PreviewState $previewState -Bucket Deleted -Items @($entry.Plan.Deleted)
}

foreach ($entry in $trackedFilePlans) {
    Add-PreviewItems -PreviewState $previewState -Bucket Added -Items @($entry.Plan.Added)
    Add-PreviewItems -PreviewState $previewState -Bucket Updated -Items @($entry.Plan.Updated)
}

if (-not $DryRun) {
    foreach ($action in @($plannerResult.actions)) {
        Invoke-PlannerAction -Action $action
    }

    foreach ($entry in $directoryPlans) {
        foreach ($action in @($entry.Plan.Actions)) {
            Invoke-FileAction -Action $action
        }

        if ($entry.Plan.MirrorMode) {
            Remove-EmptyDirectories -Root $entry.Plan.DestinationRoot
        }
    }

    foreach ($entry in $trackedFilePlans) {
        foreach ($action in @($entry.Plan.Actions)) {
            Invoke-FileAction -Action $action
        }
    }
}

Write-SyncSummary `
    -Added $previewState.Added.Count `
    -Updated $previewState.Updated.Count `
    -Deleted $previewState.Deleted.Count `
    -DryRunMode:$DryRun

Write-SyncMarkers -PreviewState $previewState -WhatIfMode:$DryRun

$mcpSamplePath = Join-Path $destinationPath "mcp-config.sample.json"
$mcpLivePath = Join-Path $destinationPath "mcp-config.json"
if (-not (Test-Path -LiteralPath $mcpLivePath) -and (Test-Path -LiteralPath $mcpSamplePath)) {
    Write-Warning "mcp-config.json is user-owned and was not synced. Copy mcp-config.sample.json to mcp-config.json in $destinationPath and fill your API keys."
}
