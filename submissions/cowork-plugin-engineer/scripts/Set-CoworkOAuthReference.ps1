[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [Parameter(Mandatory)]
    [string]$ConnectorId,

    [Parameter(Mandatory)]
    [string]$OAuthConfigurationId,

    [switch]$NoVersionBump
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$isObviousPlaceholder =
    $OAuthConfigurationId -match '(?i)(REPLACE|PLACEHOLDER|YOUR[_-]|<[^>]+>|\{\{.+\}\})'
$isImportedPlaceholder = $OAuthConfigurationId.EndsWith(
    "-$ConnectorId-auth",
    [StringComparison]::OrdinalIgnoreCase
)
if ($isObviousPlaceholder -or $isImportedPlaceholder) {
    throw 'OAuthConfigurationId appears to be a placeholder. Use the generated Teams Developer Portal OAuth client registration ID.'
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$manifestPath = Join-Path $resolvedProject 'appPackage\manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    $manifestPath = Join-Path $resolvedProject 'manifest.json'
}
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "manifest.json was not found under $resolvedProject"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 |
    ConvertFrom-Json
$connectors = @($manifest.agentConnectors)
$connector = @($connectors | Where-Object { $_.id -eq $ConnectorId })
if ($connector.Count -ne 1) {
    throw "Expected one connector with ID '$ConnectorId'; found $($connector.Count)."
}

$authorization = $connector[0].toolSource.remoteMcpServer.authorization
if ($null -eq $authorization -or $authorization.type -ne 'OAuthPluginVault') {
    throw "Connector '$ConnectorId' does not use OAuthPluginVault."
}

if (-not $NoVersionBump) {
    if ($manifest.version -notmatch '^(\d+)\.(\d+)\.(\d+)$') {
        throw "Manifest version is not semantic: $($manifest.version)"
    }
    $manifest.version = "$($Matches[1]).$($Matches[2]).$([int]$Matches[3] + 1)"
}

$updated = $false
if ($PSCmdlet.ShouldProcess($manifestPath, "Set OAuth reference for $ConnectorId")) {
    $authorization.referenceId = $OAuthConfigurationId
    $manifest | ConvertTo-Json -Depth 100 |
        Set-Content -LiteralPath $manifestPath -Encoding utf8
    $updated = $true
}

[pscustomobject]@{
    ManifestPath = $manifestPath
    ConnectorId = $ConnectorId
    Version = $manifest.version
    Updated = $updated
}
