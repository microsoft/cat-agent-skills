[CmdletBinding()]
param([ValidateRange(1024, 65535)][int] $Port = 5078)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (!(Test-Path (Join-Path $root 'widget\dist\index.html'))) {
    throw 'Widget is not built. Run .\scripts\Build.ps1 first.'
}

$names = @('ASPNETCORE_ENVIRONMENT', 'DOTNET_ENVIRONMENT', 'Demo__Enabled', 'Demo__Port', 'ASPNETCORE_URLS')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
    $env:ASPNETCORE_ENVIRONMENT = 'Development'
    $env:DOTNET_ENVIRONMENT = 'Development'
    $env:Demo__Enabled = 'true'
    $env:Demo__Port = "$Port"
    $env:ASPNETCORE_URLS = "http://localhost:$Port"
    Write-Output "Synthetic local demo: http://localhost:$Port/?demo=1"
    Write-Output 'No ServiceNow traffic. Do not expose this demo through a tunnel or public proxy.'
    dotnet run --project (Join-Path $root 'src\CoworkSn\CoworkSn.csproj') --configuration Release --no-launch-profile
    if ($LASTEXITCODE -ne 0) { throw "Demo exited with code $LASTEXITCODE." }
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
}
