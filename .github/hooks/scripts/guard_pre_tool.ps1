#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(ValueFromPipeline = $true)]
    [AllowNull()]
    [string]$InputObject
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-HookEventName {
    $hookEvent = [Environment]::GetEnvironmentVariable("HAPPY_AI_LIFE_HOOK_EVENT")
    if ($hookEvent -in @("preToolUse", "permissionRequest")) {
        return $hookEvent
    }

    return "preToolUse"
}

$script:HookEvent = Resolve-HookEventName

function Write-HookResponse {
    param([Parameter(Mandatory = $true)]$Object)

    [Console]::Out.Write(($Object | ConvertTo-Json -Compress))
}

function Test-FailureLogEnabled {
    $value = [Environment]::GetEnvironmentVariable("HAPPY_AI_LIFE_GUARD_FAILURE_LOG")
    return -not [string]::IsNullOrWhiteSpace($value) -and $value -match '^(?i:1|true|yes|on)$'
}

function Sanitize-FailureLogMessage {
    param([Parameter(Mandatory = $true)][string]$Message)

    if ([string]::IsNullOrWhiteSpace($Message)) {
        return ""
    }

    $sanitized = $Message -replace "\s*stderr:.*$", ""
    $sanitized = $sanitized -replace "\s+", " "
    $sanitized = $sanitized.Trim()
    if ($sanitized.Length -gt 240) {
        return $sanitized.Substring(0, 240) + "..."
    }

    return $sanitized
}

function Write-FailureLog {
    param([Parameter(Mandatory = $true)][string]$Message)

    try {
        if (-not (Test-FailureLogEnabled)) {
            return
        }

        $sanitized = Sanitize-FailureLogMessage -Message $Message
        if ([string]::IsNullOrWhiteSpace($sanitized)) {
            return
        }

        $logPath = Join-Path $HOME ".copilot\guard-failures.log"
        $logDirectory = Split-Path -Parent $logPath
        if (-not (Test-Path -LiteralPath $logDirectory -PathType Container)) {
            [void](New-Item -ItemType Directory -Path $logDirectory -Force)
        }
        if (Test-Path -LiteralPath $logPath -PathType Leaf) {
            $existingLog = Get-Item -LiteralPath $logPath -ErrorAction SilentlyContinue
            if ($null -ne $existingLog -and $existingLog.Length -gt 64KB) {
                $recentLines = @(Get-Content -LiteralPath $logPath -Tail 199 -ErrorAction SilentlyContinue)
                Set-Content -LiteralPath $logPath -Value $recentLines -Encoding utf8
            }
        }
        Add-Content -LiteralPath $logPath -Value ("{0} {1}" -f [DateTimeOffset]::Now.ToString("o"), $sanitized) -Encoding utf8
    }
    catch {
    }
}

function Write-DenyResponse {
    param([Parameter(Mandatory = $true)][string]$Reason)

    Write-FailureLog -Message $Reason
    if ($script:HookEvent -eq "permissionRequest") {
        Write-HookResponse @{
            behavior  = "deny"
            message   = $Reason
            interrupt = $true
        }
        return
    }

    Write-HookResponse @{
        permissionDecision       = "deny"
        permissionDecisionReason = $Reason
    }
}

function Resolve-LayoutRoot {
    $scriptDirectory = Get-Item -LiteralPath $PSScriptRoot -ErrorAction Stop
    if ($scriptDirectory.Name -ne "scripts") {
        return $null
    }

    $hooksDirectory = $scriptDirectory.Parent
    if ($null -eq $hooksDirectory) {
        return $null
    }

    return $hooksDirectory.Parent
}

function Resolve-RepoRoot {
    param($LayoutRoot)

    if ($null -eq $LayoutRoot) {
        return $null
    }

    if ($LayoutRoot.Name -eq ".github" -and $null -ne $LayoutRoot.Parent) {
        return [System.IO.Path]::GetFullPath($LayoutRoot.Parent.FullName)
    }

    return $null
}

function Resolve-GuardEnginePath {
    $layoutRoot = Resolve-LayoutRoot
    if ($null -eq $layoutRoot) {
        return $null
    }

    if ($layoutRoot.Name -eq ".copilot") {
        $candidate = Join-Path $layoutRoot.FullName "scripts\guard_policy.py"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
        return $null
    }

    if ($layoutRoot.Name -eq ".github" -and $null -ne $layoutRoot.Parent) {
        $candidate = Join-Path $layoutRoot.Parent.FullName "scripts\guard_policy.py"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    return $null
}

function Resolve-GuardPolicyPath {
    $layoutRoot = Resolve-LayoutRoot
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

function Test-WindowsAppsPath {
    param([string]$PathValue)

    return -not [string]::IsNullOrWhiteSpace($PathValue) -and $PathValue -match "[\\/]WindowsApps[\\/]"
}

function New-PythonCommandSpec {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$PrefixArgs = @()
    )

    return [pscustomobject]@{
        Executable = $Executable
        PrefixArgs = @($PrefixArgs)
    }
}

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$PrefixArgs = @()
    )

    if ([string]::IsNullOrWhiteSpace($Executable) -or (Test-WindowsAppsPath -PathValue $Executable)) {
        return $false
    }

    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        return $false
    }

    try {
        & $Executable @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 2)" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Resolve-PythonOverride {
    param(
        [Parameter(Mandatory = $true)][string]$Override
    )

    if ([string]::IsNullOrWhiteSpace($Override)) {
        return $null
    }

    if ($Override -match '[\\/]') {
        if (Test-PythonCandidate -Executable $Override) {
            return New-PythonCommandSpec -Executable $Override
        }
        return $null
    }

    $candidate = Get-Command $Override -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $candidate) {
        return $null
    }

    $candidatePath = [string]$candidate.Source
    if ([System.IO.Path]::GetFileNameWithoutExtension($Override) -eq "py") {
        if (Test-PythonCandidate -Executable $candidatePath -PrefixArgs @("-3.10")) {
            return New-PythonCommandSpec -Executable $candidatePath -PrefixArgs @("-3.10")
        }
        if (Test-PythonCandidate -Executable $candidatePath -PrefixArgs @("-3")) {
            return New-PythonCommandSpec -Executable $candidatePath -PrefixArgs @("-3")
        }
        return $null
    }

    if (Test-PythonCandidate -Executable $candidatePath) {
        return New-PythonCommandSpec -Executable $candidatePath
    }

    return $null
}

function Resolve-PythonCommand {
    $layoutRoot = Resolve-LayoutRoot
    $repoRoot = Resolve-RepoRoot -LayoutRoot $layoutRoot
    $override = [Environment]::GetEnvironmentVariable("HAPPY_AI_LIFE_PYTHON")
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $overrideCommand = Resolve-PythonOverride -Override $override
        if ($null -ne $overrideCommand) {
            return $overrideCommand
        }
    }

    $candidatePaths = New-Object System.Collections.Generic.List[string]
    if ($null -ne $repoRoot) {
        [void]$candidatePaths.Add((Join-Path $repoRoot ".venv\Scripts\python.exe"))
        [void]$candidatePaths.Add((Join-Path $repoRoot ".venv\bin\python"))
        [void]$candidatePaths.Add((Join-Path $repoRoot ".venv\bin\python3"))
    }
    if ($null -ne $layoutRoot -and $layoutRoot.Name -eq ".copilot") {
        [void]$candidatePaths.Add((Join-Path $layoutRoot.FullName ".venv\Scripts\python.exe"))
        [void]$candidatePaths.Add((Join-Path $layoutRoot.FullName ".venv\bin\python"))
        [void]$candidatePaths.Add((Join-Path $layoutRoot.FullName ".venv\bin\python3"))
    }

    foreach ($candidatePath in $candidatePaths) {
        if (Test-PythonCandidate -Executable $candidatePath) {
            return New-PythonCommandSpec -Executable $candidatePath
        }
    }

    foreach ($candidateName in @("python", "python3")) {
        $candidate = Get-Command $candidateName -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $candidate) {
            continue
        }

        $candidatePath = [string]$candidate.Source
        if (Test-PythonCandidate -Executable $candidatePath) {
            return New-PythonCommandSpec -Executable $candidatePath
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $pyLauncher) {
        $pyPath = [string]$pyLauncher.Source
        if (Test-PythonCandidate -Executable $pyPath -PrefixArgs @("-3.10")) {
            return New-PythonCommandSpec -Executable $pyPath -PrefixArgs @("-3.10")
        }
        if (Test-PythonCandidate -Executable $pyPath -PrefixArgs @("-3")) {
            return New-PythonCommandSpec -Executable $pyPath -PrefixArgs @("-3")
        }
    }

    return $null
}

function Join-QuotedProcessArguments {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $quoted = foreach ($argument in $Arguments) {
        if ([string]::IsNullOrEmpty($argument)) {
            '""'
            continue
        }

        if ($argument -notmatch '[\s"]') {
            $argument
            continue
        }

        $escaped = $argument -replace '(\\*)"', '$1$1\"'
        $escaped = $escaped -replace '(\\+)$', '$1$1'
        '"' + $escaped + '"'
    }

    return ($quoted -join " ")
}

function Get-StderrSummary {
    param([string]$StderrText)

    if ([string]::IsNullOrWhiteSpace($StderrText)) {
        return ""
    }

    $trimmed = $StderrText.Trim()
    if ($trimmed.Length -le 500) {
        return $trimmed
    }

    return $trimmed.Substring(0, 500)
}

function Receive-TaskText {
    param(
        [Parameter(Mandatory = $true)]$Task,
        [int]$TimeoutMilliseconds = 1000
    )

    if ($null -eq $Task) {
        return [pscustomobject]@{
            Completed = $true
            Text      = ""
        }
    }

    try {
        if (-not $Task.Wait($TimeoutMilliseconds)) {
            return [pscustomobject]@{
                Completed = $false
                Text      = ""
            }
        }

        return [pscustomobject]@{
            Completed = $true
            Text      = $Task.GetAwaiter().GetResult()
        }
    }
    catch {
        return [pscustomobject]@{
            Completed = $false
            Text      = ""
        }
    }
}

function Invoke-GuardEngine {
    param(
        [Parameter(Mandatory = $true)][string]$Raw,
        [Parameter(Mandatory = $true)][string]$EnginePath,
        [string]$PolicyPath,
        [Parameter(Mandatory = $true)]$PythonCommand,
        [Parameter(Mandatory = $true)][string]$CurrentDirectory,
        [Parameter(Mandatory = $true)][string]$HomeDirectory,
        [string]$RepoRoot
    )

    $arguments = @()
    $arguments += @($PythonCommand.PrefixArgs)
    $arguments += @("-X", "utf8", $EnginePath, "--hook-event", $script:HookEvent, "--cwd", $CurrentDirectory, "--home", $HomeDirectory)
    if (-not [string]::IsNullOrWhiteSpace($PolicyPath)) {
        $arguments += @("--policy-path", $PolicyPath)
    }
    if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
        $arguments += @("--repo-root", $RepoRoot)
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = [string]$PythonCommand.Executable
    $startInfo.Arguments = Join-QuotedProcessArguments -Arguments $arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
    $startInfo.EnvironmentVariables["PYTHONUTF8"] = "1"

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    try {
        $process.StandardInput.Write($Raw)
        $process.StandardInput.Close()

        if (-not $process.WaitForExit(15000)) {
            $terminated = $false
            try {
                $process.Kill()
                $terminated = $process.WaitForExit(1000)
            }
            catch {
            }

            [void](Receive-TaskText -Task $stdoutTask -TimeoutMilliseconds 200)
            [void](Receive-TaskText -Task $stderrTask -TimeoutMilliseconds 200)

            $reason = "Timed out while running the shared guard policy engine (scripts/guard_policy.py). Secret scanning or repository operations may be slow; retry the focused operation and review hook timeoutSec if this persists. Do not bypass the secret scan."
            if (-not $terminated) {
                $reason = "$reason The engine did not exit promptly after termination."
            }

            return [pscustomobject]@{
                Succeeded = $false
                Reason    = $reason
            }
        }

        $stdoutRead = Receive-TaskText -Task $stdoutTask
        $stderrRead = Receive-TaskText -Task $stderrTask
        if (-not $stdoutRead.Completed -or -not $stderrRead.Completed) {
            return [pscustomobject]@{
                Succeeded = $false
                Reason    = "Failed to read the shared guard policy engine output before the hook timeout budget elapsed. Retry the focused operation and review hook timeoutSec if this persists."
            }
        }
        $stdout = [string]$stdoutRead.Text
        $stderr = [string]$stderrRead.Text
        if ($process.ExitCode -ne 0) {
            $summary = Get-StderrSummary -StderrText $stderr
            $reason = "Failed to run the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter."
            if (-not [string]::IsNullOrWhiteSpace($summary)) {
                $reason = "$reason stderr: $summary"
            }
            return [pscustomobject]@{
                Succeeded = $false
                Reason    = $reason
            }
        }
    }
    finally {
        $process.Dispose()
    }

    if ([string]::IsNullOrWhiteSpace($stdout)) {
        return [pscustomobject]@{
            Succeeded = $true
            Output    = ""
        }
    }

    try {
        $null = $stdout | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return [pscustomobject]@{
            Succeeded = $false
            Reason    = "The shared guard policy engine returned invalid JSON. Restore the synchronized guard runtime or sync again."
        }
    }

    return [pscustomobject]@{
        Succeeded = $true
        Output    = $stdout
    }
}

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    $pipelineInput = New-Object System.Collections.Generic.List[string]
    if ($null -ne $InputObject) {
        [void]$pipelineInput.Add([string]$InputObject)
    }
    foreach ($item in @($input)) {
        if ($null -ne $item) {
            [void]$pipelineInput.Add($item.ToString())
        }
    }
    if ($pipelineInput.Count -gt 0) {
        $raw = ($pipelineInput -join [Environment]::NewLine)
    }
}
if ([string]::IsNullOrWhiteSpace($raw)) {
    exit 0
}

$layoutRoot = Resolve-LayoutRoot
$repoRoot = Resolve-RepoRoot -LayoutRoot $layoutRoot
$enginePath = Resolve-GuardEnginePath
if ($null -eq $enginePath) {
    Write-DenyResponse -Reason "Failed to locate the shared guard policy engine (scripts/guard_policy.py). Restore the synchronized guard runtime or sync again."
    exit 0
}

$pythonCommand = Resolve-PythonCommand
if ($null -eq $pythonCommand) {
    Write-DenyResponse -Reason "Python 3.10+ is required to run the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter."
    exit 0
}

$policyPath = Resolve-GuardPolicyPath
$result = Invoke-GuardEngine `
    -Raw $raw `
    -EnginePath $enginePath `
    -PolicyPath $policyPath `
    -PythonCommand $pythonCommand `
    -CurrentDirectory (Get-Location).ProviderPath `
    -HomeDirectory $HOME `
    -RepoRoot $repoRoot

if (-not $result.Succeeded) {
    Write-DenyResponse -Reason $result.Reason
    exit 0
}

if (-not [string]::IsNullOrWhiteSpace($result.Output)) {
    [Console]::Out.Write([string]$result.Output)
}

exit 0
