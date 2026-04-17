param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).ProviderPath
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$resolvedOutput = (Resolve-Path -LiteralPath $OutputDir).ProviderPath

$powerPoint = $null
$presentation = $null

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application

    $presentation = $powerPoint.Presentations.Open(
        $resolvedInput,
        $false,
        $false,
        $false
    )

    $presentation.SaveAs($resolvedOutput, 18)
}
finally {
    if ($presentation -ne $null) {
        try {
            $presentation.Close()
        }
        finally {
            [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
        }
    }

    if ($powerPoint -ne $null) {
        try {
            $powerPoint.Quit()
        }
        finally {
            [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint)
        }
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
