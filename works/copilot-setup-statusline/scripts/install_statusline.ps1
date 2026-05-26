param(
    [string]$CopilotDir = (Join-Path $env:USERPROFILE '.copilot'),
    [string]$WindowsTerminalSettingsPath = ''
)

$ErrorActionPreference = 'Stop'

$skillDir = Split-Path -Parent $PSScriptRoot
$assetsDir = Join-Path $skillDir 'assets'
$settingsPath = Join-Path $CopilotDir 'settings.json'

function Test-JsonObjectLike {
    param([object]$Value)

    return $Value -is [pscustomobject] -or $Value -is [hashtable]
}

function Test-JsonArrayLike {
    param([object]$Value)

    return $Value -is [System.Collections.IList] -and $Value -isnot [string]
}

function Test-LooksLikeNerdFont {
    param([string]$Face)

    if ([string]::IsNullOrWhiteSpace($Face)) {
        return $false
    }

    return $Face -match 'Nerd Font| NF$'
}

function Get-WindowsTerminalSettingsPath {
    param([string]$OverridePath)

    if (-not [string]::IsNullOrWhiteSpace($OverridePath)) {
        if (Test-Path -LiteralPath $OverridePath) {
            return $OverridePath
        }

        return $null
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),
        (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json')
    )

    return $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

function Get-InstalledNerdFontFaces {
    $knownPatterns = @{
        'MesloLGMNerdFont*' = 'MesloLGM Nerd Font'
        'CaskaydiaMonoNerdFont*' = 'CaskaydiaMono Nerd Font'
        'CaskaydiaCoveNerdFont*' = 'CaskaydiaCove Nerd Font'
        'CascadiaCodeNerdFont*' = 'Cascadia Code Nerd Font'
        'FiraCodeNerdFont*' = 'FiraCode Nerd Font'
    }

    $dirs = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'),
        (Join-Path $env:WINDIR 'Fonts')
    )

    $faces = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($dir in $dirs) {
        if (-not (Test-Path -LiteralPath $dir)) {
            continue
        }

        foreach ($entry in $knownPatterns.GetEnumerator()) {
            $files = Get-ChildItem -LiteralPath $dir -Filter "$($entry.Key).ttf" -File -ErrorAction SilentlyContinue
            if ($files) {
                [void]$faces.Add($entry.Value)
            }
        }
    }

    return @($faces | Sort-Object)
}

function Write-OhMyPoshStatus {
    $command = Get-Command 'oh-my-posh' -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        $version = & $command.Source version 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($version)) {
            Write-Host "Found oh-my-posh $($version.Trim())"
        } else {
            Write-Host 'Found oh-my-posh'
        }
        return
    }

    Write-Warning 'oh-my-posh is not installed yet. The statusline files were installed, but icon rendering needs oh-my-posh.'
    if (Get-Command 'winget' -ErrorAction SilentlyContinue) {
        Write-Host 'Install it with: winget install JanDeDobbeleer.OhMyPosh -s winget'
    } else {
        Write-Host 'Install oh-my-posh on Windows before expecting icon rendering in the statusline.'
    }
}

function Write-WindowsTerminalFontStatus {
    param([string]$ResolvedSettingsPath)

    if ([string]::IsNullOrWhiteSpace($ResolvedSettingsPath)) {
        Write-Warning 'Windows Terminal settings.json was not found. If you use Windows Terminal, configure its font.face to a Nerd Font on the host.'
        return
    }

    try {
        $terminalSettings = Get-Content -Raw -LiteralPath $ResolvedSettingsPath | ConvertFrom-Json
    } catch {
        Write-Warning "$ResolvedSettingsPath could not be read as JSON. Check the host terminal font manually."
        return
    }

    if (-not (Test-JsonObjectLike $terminalSettings.profiles)) {
        Write-Warning "$ResolvedSettingsPath has no profiles object. Check the host terminal font manually."
        return
    }

    $faces = [System.Collections.Generic.List[object]]::new()
    $defaultsFontFace = $terminalSettings.profiles.defaults.font.face
    if (-not [string]::IsNullOrWhiteSpace($defaultsFontFace)) {
        $faces.Add([pscustomobject]@{
            Origin = 'profiles.defaults.font.face'
            Face = [string]$defaultsFontFace
        })
    }

    $profileList = @($terminalSettings.profiles.list)
    foreach ($profile in $profileList) {
        if (-not (Test-JsonObjectLike $profile)) {
            continue
        }
        if ($profile.source -ne 'Windows.Terminal.PowershellCore' -and $profile.name -ne 'PowerShell') {
            continue
        }
        $profileFontFace = $profile.font.face
        if ([string]::IsNullOrWhiteSpace($profileFontFace)) {
            continue
        }
        $faces.Add([pscustomobject]@{
            Origin = "profile $($profile.name)"
            Face = [string]$profileFontFace
        })
    }

    $configured = $faces | Where-Object { Test-LooksLikeNerdFont $_.Face } | Select-Object -First 1
    if ($null -ne $configured) {
        Write-Host "Windows Terminal font check: OK ($($configured.Face) via $($configured.Origin))."
        return
    }

    $installedFaces = @(Get-InstalledNerdFontFaces)
    if ($installedFaces.Count -gt 0) {
        Write-Warning 'Host Nerd Fonts were detected, but the Windows Terminal defaults/PowerShell profile do not appear to use one.'
        Write-Host ("Detected host Nerd Fonts: {0}" -f (($installedFaces | Select-Object -First 3) -join ', '))
        Write-Host "Set profiles.defaults.font.face or the current profile font.face in $ResolvedSettingsPath."
        return
    }

    Write-Warning 'No host Nerd Font was detected in the Windows font directories that were inspected.'
    Write-Host "Install one first (recommended: 'oh-my-posh font install meslo'), then set Windows Terminal font.face in $ResolvedSettingsPath."
}

New-Item -ItemType Directory -Force -Path $CopilotDir | Out-Null

foreach ($fileName in @('statusline.cmd', 'statusline.ps1', 'statusline.omp.json')) {
    Copy-Item -LiteralPath (Join-Path $assetsDir $fileName) -Destination (Join-Path $CopilotDir $fileName) -Force
}

if (Test-Path -LiteralPath $settingsPath) {
    $backup = "$settingsPath.statusline-backup-$(Get-Date -Format 'yyyyMMddTHHmmssK')"
    Copy-Item -LiteralPath $settingsPath -Destination $backup -Force
    $settings = Get-Content -Raw -LiteralPath $settingsPath | ConvertFrom-Json
} else {
    $settings = [pscustomobject]@{}
}

if ($settings -isnot [pscustomobject] -and $settings -isnot [hashtable]) {
    throw "$settingsPath must contain a JSON object."
}

if ($null -eq $settings.statusLine) {
    $settings | Add-Member -NotePropertyName statusLine -NotePropertyValue ([pscustomobject]@{}) -Force
} elseif (-not (Test-JsonObjectLike $settings.statusLine)) {
    throw "$settingsPath statusLine must be a JSON object."
}

$settings.statusLine | Add-Member -NotePropertyName type -NotePropertyValue 'command' -Force
$settings.statusLine | Add-Member -NotePropertyName command -NotePropertyValue (Join-Path $CopilotDir 'statusline.cmd') -Force
$settings.statusLine | Add-Member -NotePropertyName padding -NotePropertyValue 1 -Force

if ($null -eq $settings.feature_flags) {
    $settings | Add-Member -NotePropertyName feature_flags -NotePropertyValue ([pscustomobject]@{ enabled = @() }) -Force
} elseif (-not (Test-JsonObjectLike $settings.feature_flags)) {
    throw "$settingsPath feature_flags must be a JSON object."
}

if ($null -eq $settings.feature_flags.enabled) {
    $settings.feature_flags | Add-Member -NotePropertyName enabled -NotePropertyValue @() -Force
} elseif (-not (Test-JsonArrayLike $settings.feature_flags.enabled)) {
    throw "$settingsPath feature_flags.enabled must be a JSON array."
}

$enabled = @($settings.feature_flags.enabled)
if ($enabled -notcontains 'STATUS_LINE') {
    $settings.feature_flags.enabled = @($enabled + 'STATUS_LINE')
}

$settings | Add-Member -NotePropertyName experimental -NotePropertyValue $true -Force
$settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8

Write-Host "Installed Copilot statusline to $CopilotDir"
$resolvedWindowsTerminalSettingsPath = Get-WindowsTerminalSettingsPath -OverridePath $WindowsTerminalSettingsPath
Write-OhMyPoshStatus
Write-WindowsTerminalFontStatus -ResolvedSettingsPath $resolvedWindowsTerminalSettingsPath
Write-Host "Run /restart in Copilot CLI if it is already open."
