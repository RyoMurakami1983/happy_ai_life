#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"
$script:ProtectedPathPropertyNames = @("path", "filePath", "file_path", "targetPath", "target_path")
$script:GuardPolicy = $null
$script:GuardPolicyRepoRoot = $null

function Write-HookResponse($obj) {
    $json = $obj | ConvertTo-Json -Compress
    [Console]::Out.Write($json)
}

function Resolve-HookEventName {
    $hookEvent = [Environment]::GetEnvironmentVariable("HAPPY_AI_LIFE_HOOK_EVENT")
    if ($hookEvent -in @("preToolUse", "permissionRequest")) {
        return $hookEvent
    }

    return "preToolUse"
}

function Resolve-MaintenanceModePath {
    return [System.IO.Path]::GetFullPath((Join-Path $HOME ".copilot\maintenance-mode.json"))
}

function Get-MinimalGuardPolicy {
    return [pscustomobject]@{
        schemaVersion = 1
        pathPropertyNames = @("path", "filePath", "file_path", "targetPath", "target_path")
        protectedPaths = @(
            [pscustomobject]@{ id = "repo-hooks"; path = ".github/hooks/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-githooks"; path = ".githooks/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-workflows"; path = ".github/workflows/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-instructions-dir"; path = ".github/instructions/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-skills-dir"; path = ".github/skills/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "agents-skills-dir"; path = ".agents/skills/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "claude-skills-dir"; path = ".claude/skills/**"; scope = "directory"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-copilot-instructions"; path = ".github/copilot-instructions.md"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "repo-mcp"; path = ".github/mcp.json"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "root-mcp"; path = ".mcp.json"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "gitleaks-config"; path = ".gitleaks.toml"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "guard-policy-json"; path = "policy/guard-policy.json"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "guard-policy-schema"; path = "policy/guard-policy.schema.json"; scope = "file"; action = "ask"; maintenanceScope = "protectedPathEdit" }
            [pscustomobject]@{ id = "maintenance-mode-state"; path = '$HOME/.copilot/maintenance-mode.json'; scope = "file"; action = "deny"; maintenanceScope = $null }
            [pscustomobject]@{ id = "home-copilot-root"; path = '$HOME/.copilot/**'; scope = "directory"; action = "ask"; maintenanceScope = $null }
        )
        denyCommandRules = @(
            [pscustomobject]@{ id = "maintenance-mode-manual-only"; kind = "specialized"; description = "AI must not enter or exit maintenance mode, or edit the maintenance state file." }
            [pscustomobject]@{ id = "git-hooks-no-verify"; kind = "specialized"; description = "Block git commit --no-verify, git commit -n, and git push --no-verify." }
            [pscustomobject]@{ id = "git-hooks-path-change"; kind = "specialized"; description = "Block core.hooksPath writes, unsets, and inline git -c core.hooksPath usage." }
            [pscustomobject]@{ id = "git-hooks-update-index-bypass"; kind = "specialized"; description = "Block git update-index --skip-worktree and --assume-unchanged." }
            [pscustomobject]@{ id = "git-push-force"; kind = "specialized"; description = "Block git push -f, --force, and --force-with-lease." }
            [pscustomobject]@{ id = "git-commit-secret-scan"; kind = "specialized"; description = "Run staged gitleaks scan before git commit." }
            [pscustomobject]@{ id = "git-push-secret-scan"; kind = "specialized"; description = "Run unpushed-commit gitleaks scan before git push." }
            [pscustomobject]@{ id = "gh-pr-create-secret-scan"; kind = "specialized"; description = "Run unpushed-commit gitleaks scan before gh pr create." }
            [pscustomobject]@{ id = "rm-rf-root"; kind = "pattern"; matchAgainst = "normalized"; description = "Block rm -rf /."; pattern = "\brm\s+-rf\s+\/" }
            [pscustomobject]@{ id = "rm-rf-dot"; kind = "pattern"; matchAgainst = "normalized"; description = "Block rm -rf ."; pattern = "\brm\s+-rf\s+\.(?:\s|$)" }
            [pscustomobject]@{ id = "windows-del-force-recursive"; kind = "pattern"; matchAgainst = "normalized"; description = "Block del /f /s /q."; pattern = "\bdel\s+\/f\s+\/s\s+\/q\b" }
            [pscustomobject]@{ id = "format-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block format."; pattern = "\bformat\b" }
            [pscustomobject]@{ id = "mkfs-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block mkfs."; pattern = "\bmkfs\b" }
            [pscustomobject]@{ id = "shutdown-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block shutdown."; pattern = "\bshutdown\b" }
            [pscustomobject]@{ id = "reboot-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block reboot."; pattern = "\breboot\b" }
            [pscustomobject]@{ id = "init-zero-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block init 0."; pattern = "\binit\s+0\b" }
            [pscustomobject]@{ id = "poweroff-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block poweroff."; pattern = "\bpoweroff\b" }
            [pscustomobject]@{ id = "stop-computer-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block Stop-Computer."; pattern = "\bstop-computer\b" }
            [pscustomobject]@{ id = "restart-computer-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block Restart-Computer."; pattern = "\brestart-computer\b" }
            [pscustomobject]@{ id = "remove-item-recurse-force"; kind = "pattern"; matchAgainst = "normalized"; description = "Block Remove-Item -Recurse -Force."; pattern = "(?=.*\bremove-item\b)(?=.*(?:^|\s)-recurse(?:\s|$))(?=.*(?:^|\s)-force(?:\s|$))" }
            [pscustomobject]@{ id = "git-reset-hard"; kind = "pattern"; matchAgainst = "normalized"; description = "Block git reset --hard."; pattern = "\bgit\s+reset\s+--hard\b" }
            [pscustomobject]@{ id = "powershell-encoded-command"; kind = "pattern"; matchAgainst = "normalized"; description = "Block powershell/pwsh -EncodedCommand."; pattern = '(^|[;&|]\s*)(?:powershell|pwsh)(?:\.exe)?(?:\s+[^;&|]+)*\s+-(?:encodedcommand|enc|ec)(?=\s|$|[;&|])' }
            [pscustomobject]@{ id = "invoke-expression"; kind = "pattern"; matchAgainst = "normalized"; description = "Block Invoke-Expression / iex."; pattern = '(^|[;&|]\s*)(?:(?:[\w.\\]+\\)?invoke-expression|iex)(?=\s|$|[;&|])' }
            [pscustomobject]@{ id = "powershell-command-invoke-expression"; kind = "pattern"; matchAgainst = "normalized"; description = "Block powershell -Command Invoke-Expression / iex."; pattern = '(^|[;&|]\s*)(?:powershell|pwsh)(?:\.exe)?(?:\s+[^;&|]+)*\s+-(?:command|c)\s+(?:"|'')?(?:&\s*\{\s*)?(?:(?:[\w.\\]+\\)?invoke-expression|iex)\b' }
            [pscustomobject]@{ id = "curl-pipe-sh"; kind = "pattern"; matchAgainst = "normalized"; description = "Block curl ... | sh."; pattern = '\bcurl(?:\.exe)?\b[^;&|]*\|\s*sh\b' }
            [pscustomobject]@{ id = "wget-pipe-sh"; kind = "pattern"; matchAgainst = "normalized"; description = "Block wget ... | sh."; pattern = '\bwget(?:\.exe)?\b[^;&|]*\|\s*sh\b' }
        )
    }
}

function Normalize-GuardPolicyPathValue {
    param([Parameter(Mandatory = $true)][string]$PathValue)

    $normalized = $PathValue.Trim()
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return ""
    }

    $normalized = $normalized -replace "\\", "/"
    if ($normalized.EndsWith("/**")) {
        return $normalized.ToLowerInvariant()
    }

    return $normalized.TrimEnd('/').ToLowerInvariant()
}

function Resolve-GuardPolicyPath {
    param([string]$RepoRoot)

    $scriptDirectory = Get-Item -LiteralPath $PSScriptRoot -ErrorAction SilentlyContinue
    if ($null -eq $scriptDirectory -or $scriptDirectory.Name -ne "scripts") {
        return $null
    }

    $hooksDirectory = $scriptDirectory.Parent
    if ($null -eq $hooksDirectory -or $hooksDirectory.Name -ne "hooks") {
        return $null
    }

    $layoutRoot = $hooksDirectory.Parent
    if ($null -eq $layoutRoot) {
        return $null
    }

    if ($layoutRoot.Name -eq ".copilot") {
        $candidate = Join-Path $layoutRoot.FullName "policy\guard-policy.json"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
        return $null
    }

    if ($layoutRoot.Name -eq ".github" -and $null -ne $layoutRoot.Parent) {
        $candidate = Join-Path $layoutRoot.Parent.FullName "policy\guard-policy.json"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    return $null
}

function Test-GuardPolicyShape {
    param($Policy)

    if ($null -eq $Policy -or $Policy.schemaVersion -ne 1) {
        return $false
    }

    if (@($Policy.pathPropertyNames).Count -eq 0 -or @($Policy.protectedPaths).Count -eq 0 -or @($Policy.denyCommandRules).Count -eq 0) {
        return $false
    }

    $pathPropertyNames = @{}
    foreach ($name in @($Policy.pathPropertyNames)) {
        $propertyName = [string]$name
        if ([string]::IsNullOrWhiteSpace($propertyName) -or $pathPropertyNames.ContainsKey($propertyName)) {
            return $false
        }
        $pathPropertyNames[$propertyName] = $true
    }

    $protectedIds = @{}
    $protectedPaths = @{}
    foreach ($entry in @($Policy.protectedPaths)) {
        $entryId = [string]$entry.id
        $entryPath = [string]$entry.path
        $normalizedPath = Normalize-GuardPolicyPathValue -PathValue $entryPath

        if ([string]::IsNullOrWhiteSpace($entryId) -or [string]::IsNullOrWhiteSpace($entryPath) -or [string]::IsNullOrWhiteSpace($normalizedPath)) {
            return $false
        }
        if ([string]$entry.scope -notin @("file", "directory")) {
            return $false
        }
        if ([string]$entry.action -notin @("ask", "deny")) {
            return $false
        }
        if ([string]$entry.action -eq "deny" -and $null -ne $entry.maintenanceScope) {
            return $false
        }
        if ($protectedIds.ContainsKey($entryId) -or $protectedPaths.ContainsKey($normalizedPath)) {
            return $false
        }

        $protectedIds[$entryId] = $true
        $protectedPaths[$normalizedPath] = $true
    }

    $denyRuleIds = @{}
    foreach ($entry in @($Policy.denyCommandRules)) {
        $entryId = [string]$entry.id
        if ([string]::IsNullOrWhiteSpace($entryId) -or [string]::IsNullOrWhiteSpace([string]$entry.kind)) {
            return $false
        }
        if ($denyRuleIds.ContainsKey($entryId)) {
            return $false
        }
        $denyRuleIds[$entryId] = $true

        if ([string]$entry.kind -eq "pattern") {
            if ([string]::IsNullOrWhiteSpace([string]$entry.pattern) -or [string]$entry.matchAgainst -notin @("normalized", "compact")) {
                return $false
            }

            try {
                [void][System.Text.RegularExpressions.Regex]::new(
                    [string]$entry.pattern,
                    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase,
                    [TimeSpan]::FromSeconds(1)
                )
            }
            catch {
                return $false
            }
        }
    }

    return $true
}

function Get-GuardPolicy {
    param([string]$RepoRoot)

    if ($null -ne $script:GuardPolicy -and $script:GuardPolicyRepoRoot -eq $RepoRoot) {
        return $script:GuardPolicy
    }

    $policy = $null
    $policyPath = Resolve-GuardPolicyPath -RepoRoot $RepoRoot
    if (-not [string]::IsNullOrWhiteSpace($policyPath)) {
        try {
            $policy = Get-Content -LiteralPath $policyPath -Raw | ConvertFrom-Json
        }
        catch {
            $policy = $null
        }
    }

    if (-not (Test-GuardPolicyShape -Policy $policy)) {
        $policy = Get-MinimalGuardPolicy
    }

    $script:GuardPolicy = $policy
    $script:GuardPolicyRepoRoot = $RepoRoot
    return $policy
}

function Test-SamePath {
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )

    $leftFull = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/')
    $rightFull = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/')
    return $leftFull.Equals($rightFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-MaintenanceModeScope {
    param(
        $State,
        [Parameter(Mandatory = $true)][string]$Scope
    )

    $scopes = @($State.scopes)
    foreach ($candidate in $scopes) {
        if ([string]$candidate -eq $Scope) {
            return $true
        }
    }

    return $false
}

function Test-MaintenanceModeActive {
    param([Parameter(Mandatory = $true)][string]$Scope)

    $statePath = Resolve-MaintenanceModePath
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        return $false
    }

    try {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    }
    catch {
        return $false
    }

    if ($state.schemaVersion -ne 1 -or $state.enabled -ne $true) {
        return $false
    }

    if (-not (Test-MaintenanceModeScope -State $state -Scope $Scope)) {
        return $false
    }

    $createdAt = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$state.createdAt, [ref]$createdAt)) {
        return $false
    }

    $expiresAt = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$state.expiresAt, [ref]$expiresAt)) {
        return $false
    }

    $now = [DateTimeOffset]::Now
    if ($createdAt -gt $now) {
        return $false
    }

    if ($expiresAt -le $createdAt -or $expiresAt -gt $createdAt.AddMinutes(120) -or $expiresAt -gt $now.AddMinutes(120)) {
        return $false
    }

    return $expiresAt -gt $now
}

function Write-Deny([string]$reason) {
    if ($script:HookEvent -eq "permissionRequest") {
        Write-HookResponse @{
            behavior = "deny"
            message = $reason
            interrupt = $true
        }
        return
    }

    Write-HookResponse @{
        permissionDecision = "deny"
        permissionDecisionReason = $reason
    }
}

function Write-Ask([string]$reason) {
    if ($script:HookEvent -eq "permissionRequest") {
        exit 0
    }

    Write-HookResponse @{
        permissionDecision = "ask"
        permissionDecisionReason = $reason
    }
}

function Resolve-GitleaksPath {
    $requested = [Environment]::GetEnvironmentVariable("GITLEAKS_BIN")
    if (-not [string]::IsNullOrWhiteSpace($requested)) {
        if (Test-Path -LiteralPath $requested -PathType Leaf) {
            return $requested
        }
        $resolvedRequested = Get-Command $requested -ErrorAction SilentlyContinue
        if ($resolvedRequested) {
            return $resolvedRequested.Source
        }
        return $null
    }

    $resolved = Get-Command "gitleaks" -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Source
    }

    return $null
}

function Get-PayloadPropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    foreach ($name in $Names) {
        $property = $Object.PSObject.Properties[$name]
        if (-not $property) {
            continue
        }

        $value = $property.Value
        if ($null -eq $value) {
            continue
        }

        if ($value -is [string] -and [string]::IsNullOrWhiteSpace($value)) {
            continue
        }

        if ($property) {
            return $value
        }
    }

    return $null
}

function ConvertTo-HookObject {
    param(
        $Value,
        [switch]$ParseJsonStrings
    )

    if ($null -eq $Value) {
        return $null
    }

    if ($Value -is [string]) {
        if ([string]::IsNullOrWhiteSpace($Value)) {
            return $null
        }

        if (-not $ParseJsonStrings) {
            return $Value
        }

        $trimmed = $Value.Trim()
        if (-not ($trimmed.StartsWith("{") -or $trimmed.StartsWith("["))) {
            return $Value
        }

        try {
            return $Value | ConvertFrom-Json
        }
        catch {
            return $Value
        }
    }

    return $Value
}

function Get-ProtectedPathValues {
    param(
        $Value,
        [int]$Depth = 0
    )

    if ($Depth -gt 64 -or $null -eq $Value) {
        return @()
    }

    $normalizedValue = ConvertTo-HookObject -Value $Value -ParseJsonStrings:($Depth -eq 0)

    if ($null -eq $normalizedValue) {
        return @()
    }

    if ($normalizedValue -is [string]) {
        return @()
    }

    if ($normalizedValue -is [System.Collections.IDictionary]) {
        foreach ($key in $normalizedValue.Keys) {
            $keyName = [string]$key
            $propertyValue = $normalizedValue[$key]
            if ($keyName -in $ProtectedPathPropertyNames) {
                Get-ProtectedPathValuesFromKnownProperty -Value $propertyValue -Depth ($Depth + 1)
                continue
            }

            Get-ProtectedPathValues -Value $propertyValue -Depth ($Depth + 1)
        }
        return
    }

    if ($normalizedValue -is [System.Collections.IEnumerable]) {
        return @(
            foreach ($item in $normalizedValue) {
                Get-ProtectedPathValues -Value $item -Depth ($Depth + 1)
            }
        )
    }

    $properties = @($normalizedValue.PSObject.Properties)
    if ($properties.Count -gt 0) {
        foreach ($property in $properties) {
            $propertyValue = $property.Value
            if ($property.Name -in $ProtectedPathPropertyNames) {
                Get-ProtectedPathValuesFromKnownProperty -Value $propertyValue -Depth ($Depth + 1)
                continue
            }

            Get-ProtectedPathValues -Value $propertyValue -Depth ($Depth + 1)
        }
        return
    }
}

function Get-ProtectedPathValuesFromKnownProperty {
    param(
        $Value,
        [int]$Depth = 0
    )

    if ($Depth -gt 64 -or $null -eq $Value) {
        return @()
    }

    $normalizedValue = ConvertTo-HookObject -Value $Value
    if ($null -eq $normalizedValue) {
        return @()
    }

    if ($normalizedValue -is [string]) {
        if (-not [string]::IsNullOrWhiteSpace($normalizedValue)) {
            return ,$normalizedValue
        }
        return @()
    }

    if ($normalizedValue -is [System.Collections.IEnumerable]) {
        foreach ($item in $normalizedValue) {
            $normalizedItem = ConvertTo-HookObject -Value $item
            if ($normalizedItem -is [string]) {
                if (-not [string]::IsNullOrWhiteSpace($normalizedItem)) {
                    $normalizedItem
                }
                continue
            }

            Get-ProtectedPathValues -Value $normalizedItem -Depth ($Depth + 1)
        }
        return
    }

    Get-ProtectedPathValues -Value $normalizedValue -Depth ($Depth + 1)
}

function Resolve-FullPath {
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [Parameter(Mandatory = $true)][string]$BasePath
    )

    $expanded = [Environment]::ExpandEnvironmentVariables($PathValue.Trim())
    if ($expanded -match '^\$(?:\{HOME\}|env:HOME)([\\/].*)?$') {
        $suffix = $Matches[1]
        if ([string]::IsNullOrWhiteSpace($suffix)) {
            $expanded = $HOME
        }
        else {
            $expanded = Join-Path $HOME $suffix.TrimStart('\', '/')
        }
    }
    elseif ($expanded -match '^\$HOME([\\/].*)?$') {
        $suffix = $Matches[1]
        if ([string]::IsNullOrWhiteSpace($suffix)) {
            $expanded = $HOME
        }
        else {
            $expanded = Join-Path $HOME $suffix.TrimStart('\', '/')
        }
    }
    if ($expanded.StartsWith("~/") -or $expanded.StartsWith("~\")) {
        $expanded = Join-Path $HOME $expanded.Substring(2)
    }

    if ([System.IO.Path]::IsPathRooted($expanded)) {
        return [System.IO.Path]::GetFullPath($expanded)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $BasePath $expanded))
}

function Test-PathWithinRoot {
    param(
        [Parameter(Mandatory = $true)][string]$CandidatePath,
        [Parameter(Mandatory = $true)][string]$RootPath
    )

    $candidateFull = [System.IO.Path]::GetFullPath($CandidatePath).TrimEnd('\', '/')
    $rootFull = [System.IO.Path]::GetFullPath($RootPath).TrimEnd('\', '/')

    if ($candidateFull.Equals($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    return $candidateFull.StartsWith($rootFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-ProtectedPathRules {
    param([string]$RepoRoot)

    $rules = @()
    $policy = Get-GuardPolicy -RepoRoot $RepoRoot

    foreach ($entry in @($policy.protectedPaths)) {
        $pathText = [string]$entry.path
        $basePath = if ($pathText.StartsWith('$HOME') -or $pathText.StartsWith('${HOME}') -or $pathText.StartsWith('$env:HOME') -or $pathText.StartsWith("~/") -or $pathText.StartsWith("~\")) {
            $HOME
        }
        elseif (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
            $RepoRoot
        }
        else {
            (Get-Location).Path
        }

        $resolvedPath = if ([string]$entry.scope -eq "directory" -and $pathText.EndsWith("/**")) {
            Resolve-FullPath -PathValue $pathText.Substring(0, $pathText.Length - 3) -BasePath $basePath
        }
        else {
            Resolve-FullPath -PathValue $pathText -BasePath $basePath
        }

        $rules += [pscustomobject]@{
            Id = [string]$entry.id
            Scope = [string]$entry.scope
            Action = [string]$entry.action
            MaintenanceScope = [string]$entry.maintenanceScope
            Display = $pathText
            FullPath = $resolvedPath
        }
    }

    return $rules
}

function Find-ProtectedPathMatch {
    param(
        [Parameter(Mandatory = $true)][string[]]$CandidatePaths,
        [Parameter(Mandatory = $true)][object[]]$ProtectedRules
    )

    foreach ($candidate in $CandidatePaths) {
        foreach ($rule in $ProtectedRules) {
            if ($rule.Scope -eq "directory") {
                if (Test-PathWithinRoot -CandidatePath $candidate -RootPath $rule.FullPath) {
                    return [pscustomobject]@{
                        Candidate = $candidate
                        Rule = $rule
                    }
                }
            }
            elseif ($candidate.Equals($rule.FullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
                return [pscustomobject]@{
                    Candidate = $candidate
                    Rule = $rule
                }
            }
        }
    }

    return $null
}

function Get-RepoRoot {
    $root = (& git rev-parse --show-toplevel 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        return $null
    }
    return [System.IO.Path]::GetFullPath($root)
}

function New-RepoScratchDirectory {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $gitDir = (& git -C $RepoRoot rev-parse --git-dir 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitDir)) {
        throw "Failed to resolve .git directory."
    }
    if (-not [System.IO.Path]::IsPathRooted($gitDir)) {
        $gitDir = Join-Path $RepoRoot $gitDir
    }

    $scratchParent = Join-Path $gitDir "happy-secret-scan"
    if (-not (Test-Path -LiteralPath $scratchParent)) {
        New-Item -ItemType Directory -Path $scratchParent -Force | Out-Null
    }

    $scratchPath = Join-Path $scratchParent ("copilot-{0}" -f [guid]::NewGuid())
    New-Item -ItemType Directory -Path $scratchPath -Force | Out-Null
    return $scratchPath
}

function Invoke-GitleaksDir {
    param(
        [Parameter(Mandatory = $true)][string]$GitleaksPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ScanPath
    )

    $arguments = @("dir", $ScanPath)
    $configPath = Join-Path $RepoRoot ".gitleaks.toml"
    if (Test-Path -LiteralPath $configPath -PathType Leaf) {
        $arguments += @("--config", $configPath)
    }
    $arguments += @("--no-banner", "--redact=100", "--exit-code", "1")

    $output = & $GitleaksPath @arguments 2>&1 | Out-String
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = $output
    }
}

function Invoke-GitleaksGit {
    param(
        [Parameter(Mandatory = $true)][string]$GitleaksPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$LogOptions
    )

    $arguments = @("git", $RepoRoot, "--log-opts", $LogOptions)
    $configPath = Join-Path $RepoRoot ".gitleaks.toml"
    if (Test-Path -LiteralPath $configPath -PathType Leaf) {
        $arguments += @("--config", $configPath)
    }
    $arguments += @("--no-banner", "--redact=100", "--exit-code", "1")

    $output = & $GitleaksPath @arguments 2>&1 | Out-String
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = $output
    }
}

function Test-HasStagedFiles {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    & git -C $RepoRoot diff --cached --quiet --exit-code 2>$null
    return $LASTEXITCODE -eq 1
}

function Invoke-StagedSecretScan {
    $repoRoot = Get-RepoRoot
    if ([string]::IsNullOrWhiteSpace($repoRoot)) {
        return $null
    }

    $gitleaksPath = Resolve-GitleaksPath
    if ([string]::IsNullOrWhiteSpace($gitleaksPath)) {
        return "gitleaks is required before AI can run git commit."
    }

    if (-not (Test-HasStagedFiles -RepoRoot $repoRoot)) {
        return $null
    }

    $scratchDir = $null
    try {
        $scratchDir = New-RepoScratchDirectory -RepoRoot $repoRoot
        $snapshotDir = Join-Path $scratchDir "snapshot"
        New-Item -ItemType Directory -Path $snapshotDir -Force | Out-Null

        $stagedFiles = @(& git -C $repoRoot -c core.quotepath=false diff --cached --name-only --diff-filter=ACMR)
        if ($stagedFiles.Count -eq 0) {
            return $null
        }

        $checkoutInput = ($stagedFiles -join "`n") + "`n"
        $snapshotPrefix = $snapshotDir.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        $checkoutInput | & git -C $repoRoot checkout-index --prefix="$snapshotPrefix" --stdin 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) {
            return "Failed to prepare staged content for AI pre-commit secret scan."
        }

        $scan = Invoke-GitleaksDir -GitleaksPath $gitleaksPath -RepoRoot $repoRoot -ScanPath $snapshotDir
        if ($scan.ExitCode -ne 0) {
            return "Potential secrets were detected in staged changes. Commit was blocked before secrets entered Git history."
        }
    }
    finally {
        if (-not [string]::IsNullOrWhiteSpace($scratchDir) -and (Test-Path -LiteralPath $scratchDir)) {
            Remove-Item -LiteralPath $scratchDir -Recurse -Force
        }
    }

    return $null
}

function Get-UnpushedLogOptions {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $upstream = (& git -C $RepoRoot rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($upstream)) {
        $range = "$upstream..HEAD"
    }
    else {
        $range = "HEAD --not --remotes"
    }

    $commits = @(& git -C $RepoRoot rev-list $range 2>$null)
    if ($LASTEXITCODE -ne 0 -or $commits.Count -eq 0) {
        return $null
    }
    return $range
}

function Invoke-UnpushedSecretScan {
    param([string]$ActionName)

    $repoRoot = Get-RepoRoot
    if ([string]::IsNullOrWhiteSpace($repoRoot)) {
        return $null
    }

    $gitleaksPath = Resolve-GitleaksPath
    if ([string]::IsNullOrWhiteSpace($gitleaksPath)) {
        return "gitleaks is required before AI can run $ActionName."
    }

    $logOptions = Get-UnpushedLogOptions -RepoRoot $repoRoot
    if ([string]::IsNullOrWhiteSpace($logOptions)) {
        return $null
    }

    $scan = Invoke-GitleaksGit -GitleaksPath $gitleaksPath -RepoRoot $repoRoot -LogOptions $logOptions
    if ($scan.ExitCode -ne 0) {
        return "Potential secrets were detected in commits that may be published. $ActionName was blocked."
    }

    return $null
}

$script:HookEvent = Resolve-HookEventName

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    exit 0
}

try {
    $payload = $raw | ConvertFrom-Json
}
catch {
    # If we can't parse, do not block.
    exit 0
}

$toolName = [string](Get-PayloadPropertyValue -Object $payload -Names @("toolName", "tool_name"))
$toolArgsValue = Get-PayloadPropertyValue -Object $payload -Names @("toolArgs", "tool_input")
$hookCwd = [string](Get-PayloadPropertyValue -Object $payload -Names @("cwd"))
$toolArgs = ConvertTo-HookObject -Value $toolArgsValue -ParseJsonStrings

if ([string]::IsNullOrWhiteSpace($toolName)) {
    exit 0
}

$repoRoot = Get-RepoRoot
$script:GuardPolicy = Get-GuardPolicy -RepoRoot $repoRoot
$script:ProtectedPathPropertyNames = @($script:GuardPolicy.pathPropertyNames)
$resolutionBase = if (-not [string]::IsNullOrWhiteSpace($hookCwd)) {
    [System.IO.Path]::GetFullPath($hookCwd)
}
else {
    [System.IO.Path]::GetFullPath((Get-Location).Path)
}

if ($toolName -in @("create", "edit")) {
    $pathValues = @(Get-ProtectedPathValues -Value $toolArgs)

    if (@($pathValues).Count -gt 0) {
        $candidatePaths = @(
            foreach ($pathValue in @($pathValues | Select-Object -Unique)) {
                if (-not [string]::IsNullOrWhiteSpace($repoRoot) -and -not [System.IO.Path]::IsPathRooted([Environment]::ExpandEnvironmentVariables($pathValue)) -and -not $pathValue.StartsWith("~/") -and -not $pathValue.StartsWith("~\") -and -not $pathValue.StartsWith('$HOME') -and -not $pathValue.StartsWith('${HOME}') -and -not $pathValue.StartsWith('$env:HOME')) {
                    Resolve-FullPath -PathValue $pathValue -BasePath $repoRoot
                }
                Resolve-FullPath -PathValue $pathValue -BasePath $resolutionBase
            }
        )
        $protectedMatch = Find-ProtectedPathMatch -CandidatePaths $candidatePaths -ProtectedRules (Get-ProtectedPathRules -RepoRoot $repoRoot)
        if ($null -ne $protectedMatch) {
            if ($script:HookEvent -eq "permissionRequest") {
                # permissionRequest cannot ask, so fall through to the normal permission flow.
                exit 0
            }
            if ($protectedMatch.Rule.Action -eq "deny") {
                $reason = "Protected path change detected for {0} via {1}. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits." -f $protectedMatch.Rule.Display, $toolName
                Write-Deny $reason
                exit 0
            }
            if ($protectedMatch.Rule.Display -eq '$HOME/.copilot/**') {
                $reason = "Protected path change detected for {0} via {1}. Home-managed Copilot files always require explicit human review, even during maintenance mode." -f $protectedMatch.Rule.Display, $toolName
                Write-Ask $reason
                exit 0
            }
            if (-not [string]::IsNullOrWhiteSpace($protectedMatch.Rule.MaintenanceScope) -and (Test-MaintenanceModeActive -Scope $protectedMatch.Rule.MaintenanceScope)) {
                exit 0
            }
            $reason = "Protected path change detected for {0} via {1}. This path requires an atomic issue/PR and explicit human review." -f $protectedMatch.Rule.Display, $toolName
            Write-Ask $reason
            exit 0
        }
    }
}

# Guard shell command tools. Windows Copilot CLI reports PowerShell tool use as "powershell".
if ($toolName -notin @("bash", "powershell")) {
    exit 0
}

$command = ""
if ($toolArgs -is [string]) {
    $command = $toolArgs
}
elseif ($null -ne $toolArgs) {
    try { $command = [string]$toolArgs.command } catch {}
}

if ([string]::IsNullOrWhiteSpace($command)) {
    exit 0
}

$normalized = $command.Trim().ToLowerInvariant()
$compact = ($normalized -replace "\s+", " ")
$normalizedForPath = $normalized.Replace('/', '\')
$maintenanceStatePath = (Resolve-MaintenanceModePath).ToLowerInvariant()
$touchesMaintenanceModeScript = $compact -match '(^|[;&|]\s*)(?:\.\s+)?(?:&\s+)?[^;&|]*?(?:enter|exit)-copilot-maintenance-mode(?:\.ps1)?(?=\s|$|[;&|])'
$touchesMaintenanceStateFile = $normalizedForPath.Contains($maintenanceStatePath) -or ($compact -match 'maintenance-mode\.json') -or ($compact -match '(?:\$home|\$env:home|\$\{home\}|~)[\\/]\.copilot[\\/](?:[^;&|]*[\\/])?maintenance-mode\.json')

if ($touchesMaintenanceModeScript -or $touchesMaintenanceStateFile) {
    Write-Deny "AI is not allowed to enter or exit maintenance mode, or modify the maintenance state file. Ask a human to run the maintenance scripts manually."
    exit 0
}

$isGitCommit = $compact -match "(^|[;&|]\s*)git\s+commit(\s|$)"
$isGitPush = $compact -match "(^|[;&|]\s*)git\s+push(\s|$)"
$isGhPrCreate = $compact -match "(^|[;&|]\s*)gh\s+pr\s+create(\s|$)"
$isGitConfigHooksPathWrite = ($compact -match "(^|[;&|]\s*)git\s+config(\s|$)") -and ($compact -match "(^|\s)core\.hookspath(?:\s*=\s*|\s+)[^;&|]+")
$isGitConfigHooksPathUnset = $compact -match "(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--unset(?:-all)?(?:\s+[^;&|]+)*\s+core\.hookspath(?=\s*($|[;&|]))"
$isGitConfigRemoveCoreSection = $compact -match "(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--remove-section(?:\s+[^;&|]+)*\s+core(?=\s*($|[;&|]))"
$hasInlineGitHooksPathConfig = $compact -match "(^|[;&|]\s*)git(?:\s+[^;&|]+)*\s+-c\s+core\.hookspath(?:\s*=\s*|\s+)[^;&|]+"
$isGitUpdateIndexSkipWorktree = ($compact -match "(^|[;&|]\s*)git\s+update-index(\s|$)") -and ($compact -match "(^|\s)--skip-worktree(\s|$)")
$isGitUpdateIndexAssumeUnchanged = ($compact -match "(^|[;&|]\s*)git\s+update-index(\s|$)") -and ($compact -match "(^|\s)--assume-unchanged(\s|$)")
$hasGitPushForce = $compact -match '(^|[;&|]\s*)git\s+push(?:\s+[^;&|]+)*\s+(?:-f|--force(?:-with-lease(?:=[^;&|]+)?)?)(?=\s|$|[;&|])'
$hasNoVerify = $compact -match "(^|\s)--no-verify(\s|$)"
$hasCommitNoVerifyShort = $isGitCommit -and ($compact -match "(^|\s)-[a-z]*n[a-z]*(\s|$)")

if (($isGitCommit -and ($hasNoVerify -or $hasCommitNoVerifyShort)) -or ($isGitPush -and $hasNoVerify)) {
    Write-Deny "AI is not allowed to bypass Git hooks with --no-verify or git commit -n."
    exit 0
}

if ($isGitConfigHooksPathWrite -or $isGitConfigHooksPathUnset -or $isGitConfigRemoveCoreSection -or $hasInlineGitHooksPathConfig -or $isGitUpdateIndexSkipWorktree -or $isGitUpdateIndexAssumeUnchanged) {
    Write-Deny "AI is not allowed to disable or bypass Git hooks via core.hooksPath changes, git -c core.hooksPath, or git update-index skip-worktree/assume-unchanged."
    exit 0
}

if ($hasGitPushForce) {
    Write-Deny ("Blocked potentially destructive command: {0}" -f $command)
    exit 0
}

if ($isGitCommit) {
    $secretScanReason = Invoke-StagedSecretScan
    if (-not [string]::IsNullOrWhiteSpace($secretScanReason)) {
        Write-Deny $secretScanReason
        exit 0
    }
}

if ($isGitPush) {
    $secretScanReason = Invoke-UnpushedSecretScan -ActionName "git push"
    if (-not [string]::IsNullOrWhiteSpace($secretScanReason)) {
        Write-Deny $secretScanReason
        exit 0
    }
}

if ($isGhPrCreate) {
    $secretScanReason = Invoke-UnpushedSecretScan -ActionName "gh pr create"
    if (-not [string]::IsNullOrWhiteSpace($secretScanReason)) {
        Write-Deny $secretScanReason
        exit 0
    }
}

# Block list: keep it minimal and destructive-only at first
$denyPatterns = @(
    foreach ($rule in @($script:GuardPolicy.denyCommandRules)) {
        if ([string]$rule.kind -eq "pattern") {
            [pscustomobject]@{
                Pattern = [string]$rule.pattern
                MatchAgainst = [string]$rule.matchAgainst
            }
        }
    }
)

foreach ($rule in $denyPatterns) {
    $candidate = if ($rule.MatchAgainst -eq "compact") { $compact } else { $normalized }
    if ($candidate -match $rule.Pattern) {
        Write-Deny ("Blocked potentially destructive command: {0}" -f $command)
        exit 0
    }
}

# Allow by default (do nothing)
exit 0
