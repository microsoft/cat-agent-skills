[CmdletBinding()]
param(
    [Parameter(Mandatory)][uri] $ServerUrl,
    [Parameter(Mandatory)][ValidateLength(1, 128)][string] $OAuthReferenceId,
    [Parameter(Mandatory)][uri] $WebsiteUrl,
    [Parameter(Mandatory)][uri] $PrivacyUrl,
    [Parameter(Mandatory)][uri] $TermsUrl,
    [Parameter(Mandatory)][guid] $AppId,
    [ValidateLength(1, 32)][string] $DeveloperName = 'Cowork SN sample',
    [ValidatePattern('^\d+\.\d+\.\d+$')][string] $Version = '0.1.0',
    [string] $OutputDirectory = (Join-Path $PSScriptRoot '..\artifacts\package'),
    [switch] $Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

foreach ($url in @($ServerUrl, $WebsiteUrl, $PrivacyUrl, $TermsUrl)) {
    if (!$url.IsAbsoluteUri -or $url.Scheme -ne 'https' -or $url.UserInfo -or $url.Fragment -or $url.Query) {
        throw 'Package URLs must be absolute HTTPS URLs without credentials, fragments, or query strings.'
    }
    if ($url.IsLoopback) { throw 'A Cowork package cannot point at localhost. Use an authenticated HTTPS deployment.' }
}
if ($ServerUrl.AbsolutePath.TrimEnd('/') -notmatch '/mcp$') {
    throw 'ServerUrl must be the MCP endpoint, ending in /mcp.'
}
if ($OAuthReferenceId -match '\s|[<>]' -or $OAuthReferenceId -match '^(REPLACE|YOUR_|TODO)') {
    throw 'Supply the real OAuth token-store reference ID, not a secret or placeholder.'
}
if ($AppId -eq [guid]::Empty) { throw 'AppId must not be an empty GUID.' }

$output = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path $output) {
    if (!$Force) { throw "Output already exists: $output. Use -Force to replace the generated package files." }
    $unexpected = @(Get-ChildItem -LiteralPath $output -Force | Where-Object {
        $_.Name -notin @('manifest.json', 'color.png', 'outline.png', 'cowork-sn.zip')
    })
    if ($unexpected.Count) { throw 'Output contains non-package files; choose a dedicated output directory.' }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$manifest = [ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/teams/v1.29/MicrosoftTeams.schema.json'
    manifestVersion = '1.29'
    version = $Version
    id = $AppId.ToString()
    developer = [ordered]@{
        name = $DeveloperName
        websiteUrl = $WebsiteUrl.AbsoluteUri
        privacyUrl = $PrivacyUrl.AbsoluteUri
        termsOfUseUrl = $TermsUrl.AbsoluteUri
    }
    name = @{ short = 'ServiceNow Live Support'; full = 'ServiceNow Live Support for Copilot Cowork' }
    description = @{
        short = 'Request live IT support in an embedded Cowork chat panel.'
        full = 'Prepare a support handover, review the summary before sharing, and chat with a ServiceNow representative inside Copilot Cowork. The human conversation uses the embedded panel, not the main Copilot composer. Requires a separately configured ServiceNow integration.'
    }
    icons = @{ color = 'color.png'; outline = 'outline.png' }
    accentColor = '#B11F4B'
    validDomains = @($ServerUrl.DnsSafeHost)
    agentConnectors = @(
        @{
            id = 'cowork-sn'
            displayName = 'ServiceNow Live Support'
            description = 'Use start_live_chat when the employee asks for a human support representative. It only prepares a draft. The employee must approve sharing inside the embedded panel before ServiceNow receives the request. Do not claim a representative is connected until the session reports connected.'
            toolSource = @{
                remoteMcpServer = @{
                    mcpServerUrl = $ServerUrl.AbsoluteUri.TrimEnd('/')
                    authorization = @{ type = 'OAuthPluginVault'; referenceId = $OAuthReferenceId }
                }
            }
        }
    )
}
[IO.File]::WriteAllText((Join-Path $output 'manifest.json'), ($manifest | ConvertTo-Json -Depth 15), [Text.UTF8Encoding]::new($false))

Add-Type -AssemblyName System.Drawing
function Write-ChatIcon([int] $Size, [bool] $Outline, [string] $Path) {
    $bitmap = [Drawing.Bitmap]::new($Size, $Size)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    $pen = $null
    $brush = $null
    try {
        $graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.Clear($(if ($Outline) { [Drawing.Color]::Transparent } else { [Drawing.Color]::FromArgb(177, 31, 75) }))
        $pen = [Drawing.Pen]::new([Drawing.Color]::White, [single]($Size / 16))
        $brush = [Drawing.SolidBrush]::new([Drawing.Color]::White)
        $graphics.DrawRectangle($pen, [single]($Size * .2), [single]($Size * .22), [single]($Size * .6), [single]($Size * .43))
        $graphics.DrawLine($pen, [single]($Size * .31), [single]($Size * .65), [single]($Size * .31), [single]($Size * .8))
        $graphics.DrawLine($pen, [single]($Size * .31), [single]($Size * .8), [single]($Size * .48), [single]($Size * .65))
        foreach ($x in @(.34, .48, .62)) {
            $graphics.FillEllipse($brush, [single]($Size * $x), [single]($Size * .41), [single]($Size * .065), [single]($Size * .065))
        }
        $bitmap.Save($Path, [Drawing.Imaging.ImageFormat]::Png)
    } finally {
        if ($pen) { $pen.Dispose() }
        if ($brush) { $brush.Dispose() }
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}
Write-ChatIcon 192 $false (Join-Path $output 'color.png')
Write-ChatIcon 32 $true (Join-Path $output 'outline.png')

$zip = Join-Path $output 'cowork-sn.zip'
if (Test-Path $zip) { Remove-Item -LiteralPath $zip }
Compress-Archive -LiteralPath @(
    (Join-Path $output 'manifest.json'),
    (Join-Path $output 'color.png'),
    (Join-Path $output 'outline.png')
) -DestinationPath $zip
Write-Output $zip
