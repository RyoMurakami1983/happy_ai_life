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

# Only guard bash tool calls (same intent as your python version)
if ($toolName -ne "bash") {
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

# Block list: keep it minimal and destructive-only at first
$denyPatterns = @(
    "\brm\s+-rf\s+\/",                 # rm -rf /
    "\brm\s+-rf\s+\.\b",               # rm -rf .
    "\bdel\s+\/f\s+\/s\s+\/q\b",       # del /f /s /q
    "\bformat\b",                      # format
    "\bmkfs\b",                        # mkfs
    "\bshutdown\b",                    # shutdown
    "\breboot\b",                      # reboot
    "\binit\s+0\b",                    # init 0
    "\bpoweroff\b",                    # poweroff
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