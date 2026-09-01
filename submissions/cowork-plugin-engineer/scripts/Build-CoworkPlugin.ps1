[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [string]$OutputPath,

    [string]$AtkVersion = '1.1.15'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$workflowPath = Join-Path $resolvedProject 'm365agents.yml'
if (-not (Test-Path -LiteralPath $workflowPath -PathType Leaf)) {
    throw "m365agents.yml is required for atk packaging: $workflowPath"
}

$testScript = Join-Path $PSScriptRoot 'Test-CoworkPlugin.ps1'
& $testScript -ProjectPath $resolvedProject | Out-Null

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $resolvedProject 'appPackage\build\appPackage.zip'
}
$fullOutputPath = [IO.Path]::GetFullPath($OutputPath)
$outputFolder = Split-Path $fullOutputPath -Parent
$manifestPath = Join-Path $resolvedProject 'appPackage\manifest.json'
$packageName = "@microsoft/m365agentstoolkit-cli@$AtkVersion"

New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
Push-Location $resolvedProject
try {
    & npx --yes $packageName package `
        --manifest-file $manifestPath `
        --output-package-file $fullOutputPath `
        --output-folder $outputFolder
    if ($LASTEXITCODE -ne 0) {
        throw "atk package failed with exit code $LASTEXITCODE."
    }

    & npx --yes $packageName validate --package-file $fullOutputPath
    if ($LASTEXITCODE -ne 0) {
        throw "atk validate failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

& $testScript -ProjectPath $resolvedProject -PackagePath $fullOutputPath |
    Out-Null

[pscustomobject]@{
    ProjectPath = $resolvedProject
    PackagePath = $fullOutputPath
    Bytes = (Get-Item -LiteralPath $fullOutputPath).Length
    AtkVersion = $AtkVersion
    Status = 'Passed'
}
