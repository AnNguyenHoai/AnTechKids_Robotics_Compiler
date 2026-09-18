[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardArgs
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Orchestrator = Join-Path $RepoRoot "tools\one_click_production_zip.py"
if (-not (Test-Path $Orchestrator -PathType Leaf)) {
    throw "Missing B2.7 orchestrator: $Orchestrator"
}

function Test-BuildPython {
    param([string]$Exe, [string[]]$Prefix)
    try {
        $cmd = Get-Command $Exe -ErrorAction Stop
        $probe = & $cmd.Source @Prefix -c "import struct,sys; ok=(3,10)<=sys.version_info[:2]<(3,14) and struct.calcsize('P')*8==64; print(sys.version.split()[0]); raise SystemExit(0 if ok else 2)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{ Exe = $cmd.Source; Prefix = $Prefix; Version = ($probe | Select-Object -Last 1) }
        }
    } catch {
        return $null
    }
    return $null
}

$candidates = @()
if ($env:ROBOSTUDIO_BUILD_PYTHON) {
    $candidates += ,@($env:ROBOSTUDIO_BUILD_PYTHON, @())
}
# Prefer 3.10 because the production artifact itself is pinned to the
# Python 3.10.11 embeddable runtime. Newer build interpreters are fallback only.
$candidates += ,@("py", @("-3.10"))
$candidates += ,@("py", @("-3.11"))
$candidates += ,@("py", @("-3.12"))
$candidates += ,@("py", @("-3.13"))
$candidates += ,@("python", @())
$candidates += ,@("python3", @())

$selected = $null
foreach ($candidate in $candidates) {
    $selected = Test-BuildPython -Exe $candidate[0] -Prefix $candidate[1]
    if ($null -ne $selected) { break }
}

if ($null -eq $selected) {
    Write-Host "" -ForegroundColor Red
    Write-Host "No supported 64-bit Python build interpreter was found." -ForegroundColor Red
    Write-Host "Install Python 3.10-3.13 once on the build PC, or set ROBOSTUDIO_BUILD_PYTHON." -ForegroundColor Yellow
    exit 2
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RoboStudio - One Click Production ZIP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Repository : $RepoRoot"
Write-Host "Build Python: $($selected.Exe) $($selected.Prefix -join ' ') (v$($selected.Version))"
Write-Host ""

Push-Location $RepoRoot
try {
    & $selected.Exe @($selected.Prefix) $Orchestrator @ForwardArgs
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($exitCode -eq 0) {
    Write-Host "" -ForegroundColor Green
    Write-Host "Production ZIP completed successfully." -ForegroundColor Green
    Write-Host "Output: $RepoRoot\releases\production" -ForegroundColor Green
} else {
    Write-Host "" -ForegroundColor Red
    Write-Host "Production ZIP build failed. Review the error above." -ForegroundColor Red
}
exit $exitCode
