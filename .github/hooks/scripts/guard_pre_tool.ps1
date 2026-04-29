#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

function Write-Deny([string]$reason) {
    # Copilot CLI hook expects JSON output when denying
    $obj = @{
        permissionDecision = "deny"
        permissionDecisionReason = $reason
    }
    $json = $obj | ConvertTo-Json -Compress
    [Console]::Out.Write($json)
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

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    exit 0
}

try {
    $payload = $raw | ConvertFrom-Json
} catch {
    # If we can't parse, do not block.
    exit 0
}

# Your earlier python version used these fields:
$toolName = ""
$toolArgsRaw = ""

try { $toolName = [string]$payload.toolName } catch {}
try { $toolArgsRaw = [string]$payload.toolArgs } catch {}

if ([string]::IsNullOrWhiteSpace($toolName)) {
    exit 0
}

# Guard shell command tools. Windows Copilot CLI reports PowerShell tool use as "powershell".
if ($toolName -notin @("bash", "powershell")) {
    exit 0
}

$command = ""
if (-not [string]::IsNullOrWhiteSpace($toolArgsRaw)) {
    try {
        $toolArgs = $toolArgsRaw | ConvertFrom-Json
        try { $command = [string]$toolArgs.command } catch {}
    } catch {
        # toolArgs might not be JSON; ignore
        $command = ""
    }
}

if ([string]::IsNullOrWhiteSpace($command)) {
    exit 0
}

$normalized = $command.Trim().ToLowerInvariant()
$compact = ($normalized -replace "\s+", " ")

$isGitCommit = $compact -match "(^|[;&|]\s*)git\s+commit(\s|$)"
$isGitPush = $compact -match "(^|[;&|]\s*)git\s+push(\s|$)"
$isGhPrCreate = $compact -match "(^|[;&|]\s*)gh\s+pr\s+create(\s|$)"
$hasNoVerify = $compact -match "(^|\s)--no-verify(\s|$)"
$hasCommitNoVerifyShort = $isGitCommit -and ($compact -match "(^|\s)-[a-z]*n[a-z]*(\s|$)")

if (($isGitCommit -and ($hasNoVerify -or $hasCommitNoVerifyShort)) -or ($isGitPush -and $hasNoVerify)) {
    Write-Deny "AI is not allowed to bypass Git hooks with --no-verify or git commit -n."
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
