$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$temporary = Join-Path $PSScriptRoot ('..\artifacts\package-test-' + [guid]::NewGuid())
$parameters = @{
    AppId = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    ServerUrl = 'https://support.example.org/mcp'
    OAuthReferenceId = 'test-reference-not-a-credential'
    WebsiteUrl = 'https://support.example.org/'
    PrivacyUrl = 'https://support.example.org/privacy'
    TermsUrl = 'https://support.example.org/terms'
    OutputDirectory = $temporary
}
try {
    $zip = & (Join-Path $PSScriptRoot 'New-CoworkPackage.ps1') @parameters
    $manifest = Get-Content -LiteralPath (Join-Path $temporary 'manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.manifestVersion -ne '1.29') { throw 'Unexpected manifest version.' }
    if ($manifest.agentConnectors[0].toolSource.remoteMcpServer.authorization.type -ne 'OAuthPluginVault') { throw 'Anonymous authentication is forbidden.' }
    if ($manifest.validDomains[0] -ne 'support.example.org') { throw 'Missing MCP domain.' }
    if ($manifest.PSObject.Properties.Name -contains 'bots') { throw 'Cowork package must not contain an SDK bot registration.' }
    $archive = [IO.Compression.ZipFile]::OpenRead($zip)
    try {
        $entries = @($archive.Entries.FullName | Sort-Object)
        if (($entries -join ',') -ne 'color.png,manifest.json,outline.png') { throw 'Unexpected package contents.' }
    } finally { $archive.Dispose() }
    foreach ($icon in @(@('color.png', 192), @('outline.png', 32))) {
        $image = [Drawing.Image]::FromFile((Join-Path $temporary $icon[0]))
        try {
            if ($image.Width -ne $icon[1] -or $image.Height -ne $icon[1]) { throw 'Incorrect icon dimensions.' }
        } finally { $image.Dispose() }
    }
    foreach ($badUrl in @('http://support.example.org/mcp', 'https://localhost/mcp', 'https://support.example.org/mcp?token=secret', 'https://support.example.org/not-mcp')) {
        $invalid = $parameters.Clone()
        $invalid.ServerUrl = $badUrl
        $rejected = $false
        try { & (Join-Path $PSScriptRoot 'New-CoworkPackage.ps1') @invalid -Force | Out-Null }
        catch { $rejected = $true }
        if (!$rejected) { throw "Accepted invalid MCP URL: $badUrl" }
    }
    Write-Output 'Package structure, OAuth requirement, icon dimensions and URL guards passed.'
} finally {
    if (Test-Path $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
}
