param(
    [string]$CopilotDir = (Join-Path $env:USERPROFILE '.copilot'),
    [string]$WindowsTerminalSettingsPath = ''
)

$ErrorActionPreference = 'Stop'

$skillDir = Split-Path -Parent $PSScriptRoot
$assetsDir = Join-Path $skillDir 'assets'
$settingsPath = Join-Path $CopilotDir 'settings.json'
$recommendedFontFace = 'MesloLGM Nerd Font'
$recommendedFontSlug = 'meslo'

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

function Get-WindowsTerminalFontCandidates {
    param([object]$TerminalSettings)

    $faces = [System.Collections.Generic.List[object]]::new()
    if (-not (Test-JsonObjectLike $TerminalSettings.profiles)) {
        return $faces
    }

    $defaultsFontFace = $TerminalSettings.profiles.defaults.font.face
    if (-not [string]::IsNullOrWhiteSpace($defaultsFontFace)) {
        $faces.Add([pscustomobject]@{
            Origin = 'profiles.defaults.font.face'
            Face = [string]$defaultsFontFace
        })
    }

    $profileList = @($TerminalSettings.profiles.list)
    $defaultProfileGuid = if (-not [string]::IsNullOrWhiteSpace($TerminalSettings.defaultProfile)) {
        [string]$TerminalSettings.defaultProfile
    } else {
        ''
    }

    if (-not [string]::IsNullOrWhiteSpace($defaultProfileGuid)) {
        $defaultProfile = $profileList | Where-Object {
            (Test-JsonObjectLike $_) -and $_.guid -eq $defaultProfileGuid
        } | Select-Object -First 1
        if ($null -ne $defaultProfile) {
            $defaultProfileFontFace = $defaultProfile.font.face
            if (-not [string]::IsNullOrWhiteSpace($defaultProfileFontFace)) {
                $faces.Add([pscustomobject]@{
                    Origin = "defaultProfile $($defaultProfile.name)"
                    Face = [string]$defaultProfileFontFace
                })
            }
        }
    }

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

    return $faces
}

function Ensure-OhMyPoshCommand {
    $command = Get-Command 'oh-my-posh' -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    if (-not (Get-Command 'winget' -ErrorAction SilentlyContinue)) {
        Write-Warning 'winget was not found, so oh-my-posh could not be installed automatically.'
        return $null
    }

    Write-Host 'Installing oh-my-posh with winget...'
    & winget install JanDeDobbeleer.OhMyPosh --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Warning 'oh-my-posh auto-install failed. Install it manually if icon rendering is still unavailable.'
        return $null
    }

    $installedPath = Join-Path $env:LOCALAPPDATA 'Programs\oh-my-posh\bin\oh-my-posh.exe'
    if (Test-Path -LiteralPath $installedPath) {
        $env:PATH = "$(Split-Path -Parent $installedPath);$env:PATH"
        return $installedPath
    }

    $command = Get-Command 'oh-my-posh' -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    Write-Warning 'oh-my-posh was installed but could not be resolved in the current session.'
    return $null
}

function Install-NerdFontIfNeeded {
    param([string]$OhMyPoshPath)

    if ([string]::IsNullOrWhiteSpace($OhMyPoshPath)) {
        return
    }

    $installedFaces = @(Get-InstalledNerdFontFaces)
    if ($installedFaces.Count -gt 0) {
        return
    }

    Write-Host "Installing $recommendedFontFace..."
    try {
        & $OhMyPoshPath font install $recommendedFontSlug
        if ($LASTEXITCODE -ne 0) {
            Write-Warning 'Nerd Font auto-install failed. Install a Nerd Font manually if icons still look broken.'
        }
    } catch {
        Write-Warning 'Nerd Font auto-install failed. Install a Nerd Font manually if icons still look broken.'
    }
}

function Set-WindowsTerminalFontIfNeeded {
    param(
        [string]$ResolvedSettingsPath,
        [string]$FontFaceToApply
    )

    if ([string]::IsNullOrWhiteSpace($ResolvedSettingsPath)) {
        Write-Warning 'Windows Terminal settings.json was not found. Configure font.face to a Nerd Font manually if icons still look broken.'
        return
    }

    if ([string]::IsNullOrWhiteSpace($FontFaceToApply)) {
        Write-Warning 'No installed Nerd Font was available to apply to Windows Terminal.'
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

    $configured = Get-WindowsTerminalFontCandidates -TerminalSettings $terminalSettings | Where-Object {
        Test-LooksLikeNerdFont $_.Face
    } | Select-Object -First 1
    if ($null -ne $configured) {
        Write-Host "Windows Terminal font check: OK ($($configured.Face) via $($configured.Origin))."
        return
    }

    if (-not (Test-JsonObjectLike $terminalSettings.profiles.defaults)) {
        $terminalSettings.profiles | Add-Member -NotePropertyName defaults -NotePropertyValue ([pscustomobject]@{}) -Force
    }
    if (-not (Test-JsonObjectLike $terminalSettings.profiles.defaults.font)) {
        $terminalSettings.profiles.defaults | Add-Member -NotePropertyName font -NotePropertyValue ([pscustomobject]@{}) -Force
    }
    $terminalSettings.profiles.defaults.font | Add-Member -NotePropertyName face -NotePropertyValue $FontFaceToApply -Force

    foreach ($profile in @($terminalSettings.profiles.list)) {
        if (-not (Test-JsonObjectLike $profile)) {
            continue
        }
        if ($profile.source -ne 'Windows.Terminal.PowershellCore' -and $profile.name -ne 'PowerShell') {
            continue
        }
        if (-not (Test-JsonObjectLike $profile.font)) {
            $profile | Add-Member -NotePropertyName font -NotePropertyValue ([pscustomobject]@{}) -Force
        }
        $profile.font | Add-Member -NotePropertyName face -NotePropertyValue $FontFaceToApply -Force
    }

    $timestamp = (Get-Date -Format 'yyyyMMddTHHmmsszzz').Replace(':', '')
    $backup = "$ResolvedSettingsPath.statusline-backup-$timestamp"
    Copy-Item -LiteralPath $ResolvedSettingsPath -Destination $backup -Force
    $terminalSettings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $ResolvedSettingsPath -Encoding UTF8
    Write-Host "Updated Windows Terminal font settings to $FontFaceToApply (backup: $backup)."
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

    $faces = Get-WindowsTerminalFontCandidates -TerminalSettings $terminalSettings
    $configured = $faces | Where-Object { Test-LooksLikeNerdFont $_.Face } | Select-Object -First 1
    if ($null -ne $configured) {
        Write-Host "Windows Terminal font check: OK ($($configured.Face) via $($configured.Origin))."
        return
    }

    $installedFaces = @(Get-InstalledNerdFontFaces)
    if ($installedFaces.Count -gt 0) {
        Write-Warning 'Host Nerd Fonts were detected, but the Windows Terminal defaults/default profile/current PowerShell profile do not appear to use one.'
        Write-Host ("Detected host Nerd Fonts: {0}" -f (($installedFaces | Select-Object -First 3) -join ', '))
        Write-Host "Set profiles.defaults.font.face, defaultProfile font.face, or the current profile font.face in $ResolvedSettingsPath."
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
$ohMyPoshPath = Ensure-OhMyPoshCommand
Install-NerdFontIfNeeded -OhMyPoshPath $ohMyPoshPath
$fontFaceToApply = @(Get-InstalledNerdFontFaces | Select-Object -First 1)[0]
Write-OhMyPoshStatus
Set-WindowsTerminalFontIfNeeded -ResolvedSettingsPath $resolvedWindowsTerminalSettingsPath -FontFaceToApply $fontFaceToApply
Write-WindowsTerminalFontStatus -ResolvedSettingsPath $resolvedWindowsTerminalSettingsPath
Write-Host "Run /restart in Copilot CLI if it is already open."
