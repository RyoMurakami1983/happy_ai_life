$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

function Format-TokenCount {
    param([Nullable[double]]$Value)

    if ($null -eq $Value) { return '?' }
    if ($Value -ge 1000000) { return ('{0:0.0}m' -f ($Value / 1000000)) }
    if ($Value -ge 1000) { return ('{0:0.0}k' -f ($Value / 1000)) }
    return ([int]$Value).ToString()
}

function Format-Duration {
    param([Nullable[double]]$Milliseconds)

    if ($null -eq $Milliseconds -or $Milliseconds -le 0) { return '00:00:00' }
    $duration = [TimeSpan]::FromMilliseconds($Milliseconds)
    return '{0:00}:{1:00}:{2:00}' -f [int]$duration.TotalHours, $duration.Minutes, $duration.Seconds
}

function New-Gauge {
    param([Nullable[double]]$Percent)

    if ($null -eq $Percent) { return '..........' }
    $bounded = [Math]::Max(0, [Math]::Min(100, [Math]::Round($Percent)))
    $filled = [int][Math]::Floor($bounded / 10)
    return ('#' * $filled) + ('.' * (10 - $filled))
}

function Find-ProjectMarker {
    param(
        [string]$StartPath,
        [string[]]$Names = @(),
        [string[]]$Patterns = @(),
        [int]$MaxDepth = 6
    )

    $current = Get-Item -LiteralPath $StartPath -ErrorAction SilentlyContinue
    if ($null -eq $current) { return $false }
    if (-not $current.PSIsContainer) { $current = $current.Directory }

    for ($depth = 0; $null -ne $current -and $depth -le $MaxDepth; $depth++) {
        foreach ($name in $Names) {
            if (Test-Path -LiteralPath (Join-Path $current.FullName $name)) { return $true }
        }

        foreach ($pattern in $Patterns) {
            if (Get-ChildItem -LiteralPath $current.FullName -Filter $pattern -File -ErrorAction SilentlyContinue | Select-Object -First 1) {
                return $true
            }
        }

        $current = $current.Parent
    }

    return $false
}

function Invoke-VersionCommand {
    param(
        [string]$Command,
        [string[]]$Arguments = @(),
        [switch]$SkipWindowsAppAlias
    )

    $resolved = Get-Command $Command -ErrorAction SilentlyContinue
    if ($null -eq $resolved) { return $null }
    if ($SkipWindowsAppAlias -and $resolved.Source -like '*\Microsoft\WindowsApps\*') { return $null }

    try {
        $value = & $Command @Arguments 2>$null | Select-Object -First 1
        if ([string]::IsNullOrWhiteSpace($value)) { return $null }
        return [string]$value
    } catch {
        return $null
    }
}

function Get-ToolingStatus {
    param([string]$Path)

    $items = [System.Collections.Generic.List[string]]::new()

    if (Find-ProjectMarker $Path -Names @('global.json', 'Directory.Build.props') -Patterns @('*.csproj', '*.fsproj', '*.sln')) {
        $version = Invoke-VersionCommand 'dotnet' @('--version')
        $items.Add($(if ($version) { ".NET $version" } else { '.NET' }))
    }

    if (Find-ProjectMarker $Path -Names @('tsconfig.json', 'package.json', 'pnpm-lock.yaml', 'yarn.lock', 'package-lock.json')) {
        $version = Invoke-VersionCommand 'node' @('--version')
        if ($version) { $version = $version.TrimStart('v') }
        $items.Add($(if ($version) { "TS/Node $version" } else { 'TS/Node' }))
    }

    if (Find-ProjectMarker $Path -Names @('pyproject.toml', 'requirements.txt', 'uv.lock', '.python-version', 'Pipfile')) {
        $uvVersion = Invoke-VersionCommand 'uv' @('--version')
        if ($uvVersion) {
            $uvVersion = $uvVersion -replace '^uv\s+', ''
            $uvVersion = ($uvVersion -split '\s+')[0]
            $items.Add("Python/uv $uvVersion")
        } else {
            $version = Invoke-VersionCommand 'python3' @('--version') -SkipWindowsAppAlias
            if (-not $version) {
                $version = Invoke-VersionCommand 'python' @('--version') -SkipWindowsAppAlias
            }
            if ($version) {
                $version = $version -replace '^Python\s+', ''
                $items.Add("Python $version")
            } else {
                $items.Add('Python')
            }
        }
    }

    if (Find-ProjectMarker $Path -Names @('Cargo.toml', 'Cargo.lock')) {
        $version = Invoke-VersionCommand 'rustc' @('--version')
        if ($version) {
            $version = $version -replace '^rustc\s+', ''
            $version = ($version -split '\s+')[0]
            $items.Add("Rust $version")
        } else {
            $items.Add('Rust')
        }
    }

    return ($items -join ' ')
}

$payload = [Console]::In.ReadToEnd()

try {
    $json = $payload | ConvertFrom-Json
} catch {
    Write-Host -NoNewline 'Copilot status unavailable'
    exit 0
}

$context = $json.context_window
$cost = $json.cost

$currentTokens = if ($null -ne $context.current_context_tokens) {
    [double]$context.current_context_tokens
} else {
    $null
}

$contextLimit = if ($null -ne $context.displayed_context_limit) {
    [double]$context.displayed_context_limit
} else {
    $null
}

$contextPercent = if ($null -ne $context.current_context_used_percentage) {
    [double]$context.current_context_used_percentage
} elseif ($null -ne $context.used_percentage) {
    [double]$context.used_percentage
} else {
    $null
}

$linesAdded = if ($null -ne $cost.total_lines_added) { [int]$cost.total_lines_added } else { 0 }
$linesRemoved = if ($null -ne $cost.total_lines_removed) { [int]$cost.total_lines_removed } else { 0 }

$env:COPILOT_STATUS_CONTEXT = "$(Format-TokenCount $currentTokens)/$(Format-TokenCount $contextLimit)"
$env:COPILOT_STATUS_GAUGE = New-Gauge $contextPercent
$env:COPILOT_STATUS_DURATION = Format-Duration $cost.total_duration_ms
$env:COPILOT_STATUS_CHANGES = if ($linesAdded -or $linesRemoved) { "+$linesAdded/-$linesRemoved" } else { '' }

$theme = Join-Path $PSScriptRoot 'statusline.omp.json'
$cwd = if ($json.cwd) { [string]$json.cwd } else { (Get-Location).Path }
$env:COPILOT_STATUS_TOOLING = Get-ToolingStatus $cwd

try {
    if ((Get-Command 'oh-my-posh' -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $theme)) {
        $output = & oh-my-posh print primary --config $theme --pwd $cwd --force --escape=false 2>$null
        if ([string]::IsNullOrWhiteSpace($output)) {
            throw 'Oh My Posh returned no output.'
        }

        Write-Host -NoNewline $output.TrimEnd()
        exit 0
    }
} catch {
    $tooling = if ($env:COPILOT_STATUS_TOOLING) { "$($env:COPILOT_STATUS_TOOLING) " } else { '' }
    $changes = if ($env:COPILOT_STATUS_CHANGES) { " $($env:COPILOT_STATUS_CHANGES)" } else { '' }
    Write-Host -NoNewline "$($tooling)ctx $($env:COPILOT_STATUS_CONTEXT) $($env:COPILOT_STATUS_GAUGE) time $($env:COPILOT_STATUS_DURATION)$changes"
    exit 0
}

$tooling = if ($env:COPILOT_STATUS_TOOLING) { "$($env:COPILOT_STATUS_TOOLING) " } else { '' }
$changes = if ($env:COPILOT_STATUS_CHANGES) { " $($env:COPILOT_STATUS_CHANGES)" } else { '' }
Write-Host -NoNewline "$($tooling)ctx $($env:COPILOT_STATUS_CONTEXT) $($env:COPILOT_STATUS_GAUGE) time $($env:COPILOT_STATUS_DURATION)$changes"
