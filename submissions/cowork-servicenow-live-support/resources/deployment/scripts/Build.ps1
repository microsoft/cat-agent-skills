[CmdletBinding()]
param([switch] $Test)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

function Invoke-Checked([scriptblock] $Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE." }
}

Push-Location $root
try {
    if (!(Test-Path 'widget\node_modules')) {
        Invoke-Checked { npm --prefix widget ci --no-audit --no-fund }
    }
    Invoke-Checked { npm --prefix widget run build }
    Invoke-Checked { node servicenow\tools\build-artifacts.cjs }
    Invoke-Checked { node servicenow\tools\generate-install.cjs }
    Invoke-Checked { dotnet build 'src\CoworkSn\CoworkSn.csproj' --configuration Release --nologo }
    if ($Test) {
        Invoke-Checked { npm --prefix widget run typecheck }
        Invoke-Checked { npm --prefix widget test }
        Invoke-Checked { dotnet test 'tests\CoworkSn.Tests\CoworkSn.Tests.csproj' --configuration Release --nologo }
        Push-Location 'servicenow'
        try { Invoke-Checked { node --test } }
        finally { Pop-Location }
        & (Join-Path $PSScriptRoot 'Test-Package.ps1')
    }
} finally {
    Pop-Location
}
