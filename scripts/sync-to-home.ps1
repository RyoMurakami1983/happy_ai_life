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
            Copy-PathItem -Source $Action.Source -Destination $Action.Destination
        }
        "delete-file" {
            Remove-PathItem -Path $Action.Destination
        }
        "write-text" {
            Ensure-ParentDirectory -Path $Action.Destination
            Set-Content -LiteralPath $Action.Destination -Value $Action.Content -Encoding UTF8
        }
        default {
            throw "Unsupported file action kind: $($Action.Kind)"
        }
    }
}

function Set-JsonProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$Value
    )

    $property = $Object.PSObject.Properties[$Name]
    if ($property) {
        $property.Value = $Value
        return
    }

    $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
}

function New-ManagedHomeHookEntry {
    param([Parameter(Mandatory = $true)][string]$ScriptPath)

    return [pscustomobject][ordered]@{
        type = "command"
        powershell = ('powershell -NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $ScriptPath)
        cwd = "."
        timeoutSec = 10
        env = [pscustomobject][ordered]@{
            HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"
        }
    }
}

function Get-HomeConfigHookPlan {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string]$ScriptPath
    )

    $configExists = Test-Path -LiteralPath $ConfigPath -PathType Leaf
    if ($configExists) {
        $raw = Get-Content -LiteralPath $ConfigPath -Raw
        if ([string]::IsNullOrWhiteSpace($raw)) {
            $config = [pscustomobject]@{}
        }
        else {
            $config = $raw | ConvertFrom-Json
        }
    }
    else {
        $config = [pscustomobject]@{}
    }

    $hooksProperty = $config.PSObject.Properties["hooks"]
    $hooks = $null
    if ($hooksProperty) {
        $hooks = $hooksProperty.Value
    }
    if ($null -eq $hooks) {
        $hooks = [pscustomobject]@{}
        Set-JsonProperty -Object $config -Name "hooks" -Value $hooks
    }

    $hookId = "happy-ai-life-safety-guard"
    $preToolUseProperty = $hooks.PSObject.Properties["preToolUse"]
    $existingPreToolUse = @()
    if ($preToolUseProperty) {
        $existingPreToolUse = @($preToolUseProperty.Value)
    }
    $preservedPreToolUse = @(
        foreach ($entry in $existingPreToolUse) {
            $entryHookId = $null
            try {
                $entryHookId = [string]$entry.env.HAPPY_AI_LIFE_HOOK_ID
            }
            catch {
                $entryHookId = $null
            }

            if ($entryHookId -ne $hookId) {
                $entry
            }
        }
    )

    $managedEntry = New-ManagedHomeHookEntry -ScriptPath $ScriptPath
    Set-JsonProperty -Object $hooks -Name "preToolUse" -Value @($preservedPreToolUse + $managedEntry)

    $desiredContent = ($config | ConvertTo-Json -Depth 20)
    if (-not $desiredContent.EndsWith("`n")) {
        $desiredContent = "$desiredContent`n"
    }

    $added = @()
    $updated = @()
    $actions = @()
    if (-not $configExists) {
        $added = @("config.json")
        $actions = @([pscustomobject]@{
                Kind = "write-text"
                Destination = $ConfigPath
                Content = $desiredContent
            })
    }
    elseif ((Get-Content -LiteralPath $ConfigPath -Raw) -ne $desiredContent) {
        $updated = @("config.json")
        $actions = @([pscustomobject]@{
                Kind = "write-text"
                Destination = $ConfigPath
                Content = $desiredContent
            })
    }

    return [pscustomobject]@{
        Label = "config.json (managed safety hook)"
        Actions = $actions
        Added = $added
        Updated = $updated
        Deleted = @()
        MirrorMode = $false
        DestinationRoot = Split-Path -Path $ConfigPath -Parent
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

function Write-VerbosePlanDetails {
    param(
        [Parameter(Mandatory = $true)][object[]]$DirectoryPlans,
        [Parameter(Mandatory = $true)][object[]]$TrackedFilePlans,
        [switch]$DryRunMode
    )

    Write-Host ""
    Write-Host "◆ 詳細ログ" -ForegroundColor DarkCyan
    Write-Host "Mode            : $(if ($DryRunMode) { 'dry-run' } else { 'live' })"

    $allPlans = @($DirectoryPlans + $TrackedFilePlans)
    foreach ($entry in $allPlans) {
        $actions = @($entry.Plan.Actions)
        if ($actions.Count -eq 0) {
            continue
        }

        Write-Host "  [$($entry.Label)] actions=$($actions.Count)"
        foreach ($action in $actions) {
            $target = if ($action.Destination) { $action.Destination } else { $action.Source }
            Write-Host "    - $($action.Kind): $target"
        }
    }

    if (-not ($allPlans | Where-Object { @($_.Plan.Actions).Count -gt 0 })) {
        Write-Host "  no detailed actions"
    }
}

Write-Section "ホーム同期"

$sourceRootPath = [System.IO.Path]::GetFullPath($SourceRoot)
$destinationPath = [System.IO.Path]::GetFullPath($DestinationPath)
$templateRoot = Resolve-HomeTemplateRoot -SourceRootPath $sourceRootPath -TemplatePath $TemplateRelativePath
$archiveRoot = [System.IO.Path]::GetFullPath($ArchiveRoot)
Write-Host ""
Write-Host "準備完了。home sync は Copilot instructions、repo bootstrap 資産、user-level safety hook を同期し、"
Write-Host "skills/、agents/、docs/ は plugin install / user-owned surface として触りません。"
Write-Host "実行中..."
Write-Host ""

$unsupportedHooksPath = Join-Path $templateRoot "hooks"
Warn-IfPathExists `
    -Path $unsupportedHooksPath `
    -Message "home-template/.copilot/hooks is ignored. User-level hooks are managed through config.json by this sync script."

if ($Mirror) {
    Write-HomeMirrorCompatibilityWarning -WhatIfMode:$DryRun
}

$previewState = New-PreviewState
$legacyHomeHooksPath = Join-Path $destinationPath ".github\hooks"
$legacyHomeGithubPath = Join-Path $destinationPath ".github"
$legacyHomeHookRelativeFiles = @(
    "session-continuity.json",
    "safety-guard.json",
    "scripts\guard_pre_tool.ps1",
    "scripts\guard_pre_tool.sh",
    "scripts\session-end.js",
    "scripts\session-start.js",
    "scripts\lib\decision-validation.js",
    "scripts\lib\session-utils.js"
)
$legacyHomeHookFiles = New-Object System.Collections.Generic.List[string]
foreach ($relativeFile in $legacyHomeHookRelativeFiles) {
    $candidate = Join-Path $legacyHomeHooksPath $relativeFile
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        [void]$legacyHomeHookFiles.Add($candidate)
    }
}
if ($legacyHomeHookFiles.Count -gt 0) {
    Add-PreviewItems -PreviewState $previewState -Bucket Deleted -Items @(".github/hooks known legacy files")
    Write-Host "Legacy home hook transport detected: $legacyHomeHooksPath" -ForegroundColor Yellow
}

$directoryPlans = @(
    [pscustomobject]@{
        Label = "repo-template/ (managed)"
        Plan = (Get-DirectorySyncPlan -Source (Join-Path $sourceRootPath "repo-template") -Destination (Join-Path $destinationPath "repo-template") -PreviewRoot "repo-template" -MirrorMode)
    }
)

$trackedFilePlans = @(
    [pscustomobject]@{
        Label = "copilot-instructions.md"
        Plan = (Get-TrackedFilePlan -Source (Join-Path $templateRoot "copilot-instructions.md") -Destination (Join-Path $destinationPath "copilot-instructions.md") -PreviewPath "copilot-instructions.md")
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
        Label = "hooks/scripts/guard_pre_tool.ps1"
        Plan = (Get-TrackedFilePlan -Source (Join-Path $sourceRootPath ".github\hooks\scripts\guard_pre_tool.ps1") -Destination (Join-Path $destinationPath "hooks\scripts\guard_pre_tool.ps1") -PreviewPath "hooks/scripts/guard_pre_tool.ps1")
    }
)

$configHookPlan = Get-HomeConfigHookPlan `
    -ConfigPath (Join-Path $destinationPath "config.json") `
    -ScriptPath (Join-Path $destinationPath "hooks\scripts\guard_pre_tool.ps1")

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
Add-PreviewItems -PreviewState $previewState -Bucket Added -Items @($configHookPlan.Added)
Add-PreviewItems -PreviewState $previewState -Bucket Updated -Items @($configHookPlan.Updated)

if ($VerboseLog) {
    Write-VerbosePlanDetails `
        -DirectoryPlans $directoryPlans `
        -TrackedFilePlans @($trackedFilePlans + [pscustomobject]@{ Label = $configHookPlan.Label; Plan = $configHookPlan }) `
        -DryRunMode:$DryRun
}

if (-not $DryRun) {
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

    foreach ($action in @($configHookPlan.Actions)) {
        Invoke-FileAction -Action $action
    }

    foreach ($legacyHookFile in $legacyHomeHookFiles) {
        Remove-PathItem -Path $legacyHookFile
    }
    if ($legacyHomeHookFiles.Count -gt 0) {
        Remove-EmptyDirectories -Root $legacyHomeGithubPath
        if ((Test-Path -LiteralPath $legacyHomeGithubPath) -and @(Get-ChildItem -LiteralPath $legacyHomeGithubPath -Force).Count -eq 0) {
            Remove-Item -LiteralPath $legacyHomeGithubPath -Force
        }
    }
}

Write-SyncSummary `
    -Added $previewState.Added.Count `
    -Updated $previewState.Updated.Count `
    -Deleted $previewState.Deleted.Count `
    -DryRunMode:$DryRun

Write-SyncMarkers -PreviewState $previewState -WhatIfMode:$DryRun
