#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"
$ProtectedPathPropertyNames = @("path", "filePath", "file_path", "targetPath", "target_path")

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

    if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
        foreach ($relativePath in @(
                ".github\hooks",
                ".githooks",
                ".github\workflows",
                ".github\instructions",
                ".github\skills",
                ".agents\skills",
                ".claude\skills"
            )) {
            $rules += [pscustomobject]@{
                    Scope = "directory"
                    Display = ($relativePath -replace "\\", "/") + "/**"
                    FullPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $relativePath))
                }
        }

        foreach ($relativePath in @(
                ".github\copilot-instructions.md",
                ".github\mcp.json",
                ".mcp.json",
                ".gitleaks.toml",
                "SECURITY.md",
                "docs\TRUST_BOUNDARY.md",
                "docs\HOOKS_GOVERNANCE.md",
                "docs\ENTERPRISE_SECURITY_REVIEW.md"
            )) {
            $rules += [pscustomobject]@{
                    Scope = "file"
                    Display = ($relativePath -replace "\\", "/")
                    FullPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $relativePath))
                }
        }
    }

    $homeCopilotRoot = [System.IO.Path]::GetFullPath((Join-Path $HOME ".copilot"))
    $rules += [pscustomobject]@{
            Scope = "directory"
            Display = '$HOME/.copilot/**'
            FullPath = $homeCopilotRoot
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

$isGitCommit = $compact -match "(^|[;&|]\s*)git\s+commit(\s|$)"
$isGitPush = $compact -match "(^|[;&|]\s*)git\s+push(\s|$)"
$isGhPrCreate = $compact -match "(^|[;&|]\s*)gh\s+pr\s+create(\s|$)"
$isGitConfigHooksPathWrite = ($compact -match "(^|[;&|]\s*)git\s+config(\s|$)") -and ($compact -match "(^|\s)core\.hookspath(?:\s*=\s*|\s+)[^;&|]+")
$isGitConfigHooksPathUnset = $compact -match "(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--unset(?:-all)?(?:\s+[^;&|]+)*\s+core\.hookspath(?=\s*($|[;&|]))"
$isGitConfigRemoveCoreSection = $compact -match "(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--remove-section(?:\s+[^;&|]+)*\s+core(?=\s*($|[;&|]))"
$hasInlineGitHooksPathConfig = $compact -match "(^|[;&|]\s*)git(?:\s+[^;&|]+)*\s+-c\s+core\.hookspath(?:\s*=\s*|\s+)[^;&|]+"
$isGitUpdateIndexSkipWorktree = ($compact -match "(^|[;&|]\s*)git\s+update-index(\s|$)") -and ($compact -match "(^|\s)--skip-worktree(\s|$)")
$isGitUpdateIndexAssumeUnchanged = ($compact -match "(^|[;&|]\s*)git\s+update-index(\s|$)") -and ($compact -match "(^|\s)--assume-unchanged(\s|$)")
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
    "\brm\s+-rf\s+\/",                 # rm -rf /
    "\brm\s+-rf\s+\.(?:\s|$)",        # rm -rf .
    "\bdel\s+\/f\s+\/s\s+\/q\b",       # del /f /s /q
    "\bformat\b",                      # format
    "\bmkfs\b",                        # mkfs
    "\bshutdown\b",                    # shutdown
    "\breboot\b",                      # reboot
    "\binit\s+0\b",                    # init 0
    "\bpoweroff\b",                    # poweroff
    "\bstop-computer\b",               # Stop-Computer
    "\brestart-computer\b",            # Restart-Computer
    "(?=.*\bremove-item\b)(?=.*(?:^|\s)-recurse(?:\s|$))(?=.*(?:^|\s)-force(?:\s|$))", # Remove-Item with -Recurse and -Force in any order
    "\bgit\s+push\s+--force\b",        # git push --force
    "\bgit\s+reset\s+--hard\b"         # git reset --hard
)

foreach ($pattern in $denyPatterns) {
    if ($normalized -match $pattern) {
        Write-Deny ("Blocked potentially destructive command: {0}" -f $command)
        exit 0
    }
}

# Allow by default (do nothing)
exit 0
