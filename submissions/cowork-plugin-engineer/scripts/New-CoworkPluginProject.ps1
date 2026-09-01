[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [Parameter(Mandatory)]
    [string]$PluginName,

    [Parameter(Mandatory)]
    [string]$ShortDescription,

    [Parameter(Mandatory)]
    [string]$FullDescription,

    [Parameter(Mandatory)]
    [string]$DeveloperName,

    [Parameter(Mandatory)]
    [uri]$WebsiteUrl,

    [Parameter(Mandatory)]
    [uri]$PrivacyUrl,

    [Parameter(Mandatory)]
    [uri]$TermsOfUseUrl,

    [Parameter(Mandatory)]
    [string[]]$SkillName,

    [Parameter(Mandatory)]
    [string[]]$SkillDescription,

    [Parameter(Mandatory)]
    [string]$ColorIconPath,

    [Parameter(Mandatory)]
    [string]$OutlineIconPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($SkillName.Count -ne $SkillDescription.Count) {
    throw 'SkillName and SkillDescription must have the same number of values.'
}
if ($SkillName.Count -gt 20) {
    throw 'Cowork supports at most 20 registered skills.'
}
foreach ($name in $SkillName) {
    if ($name -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
        throw "Skill name must be lowercase kebab-case: $name"
    }
}
foreach ($uri in $WebsiteUrl, $PrivacyUrl, $TermsOfUseUrl) {
    if ($uri.Scheme -ne 'https') {
        throw "Developer URLs must use HTTPS: $uri"
    }
}

$fullProjectPath = [IO.Path]::GetFullPath($ProjectPath)
if (Test-Path -LiteralPath $fullProjectPath) {
    throw "Project path already exists: $fullProjectPath"
}

$resolvedColorIcon = (Resolve-Path -LiteralPath $ColorIconPath).Path
$resolvedOutlineIcon = (Resolve-Path -LiteralPath $OutlineIconPath).Path
$templatePath = Join-Path $PSScriptRoot '..\assets\manifest.v1.28.template.json'
$manifest = Get-Content -LiteralPath $templatePath -Raw -Encoding utf8 |
    ConvertFrom-Json

$manifest.id = [guid]::NewGuid().ToString()
$manifest.developer.name = $DeveloperName
$manifest.developer.websiteUrl = $WebsiteUrl.AbsoluteUri
$manifest.developer.privacyUrl = $PrivacyUrl.AbsoluteUri
$manifest.developer.termsOfUseUrl = $TermsOfUseUrl.AbsoluteUri
$manifest.name.short = $PluginName
$manifest.name.full = "$PluginName for Copilot Cowork"
$manifest.description.short = $ShortDescription
$manifest.description.full = $FullDescription
$manifest.agentSkills = @($SkillName | ForEach-Object {
    [pscustomobject]@{ folder = "./skills/$_" }
})

if ($PSCmdlet.ShouldProcess($fullProjectPath, 'Create Cowork plugin project')) {
    $appPackage = Join-Path $fullProjectPath 'appPackage'
    New-Item -ItemType Directory -Path $appPackage -Force | Out-Null
    Copy-Item -LiteralPath $resolvedColorIcon -Destination (Join-Path $appPackage 'color.png')
    Copy-Item -LiteralPath $resolvedOutlineIcon -Destination (Join-Path $appPackage 'outline.png')
    $manifest | ConvertTo-Json -Depth 100 |
        Set-Content -LiteralPath (Join-Path $appPackage 'manifest.json') -Encoding utf8

    for ($i = 0; $i -lt $SkillName.Count; $i++) {
        $skillFolder = Join-Path $appPackage "skills\$($SkillName[$i])"
        New-Item -ItemType Directory -Path $skillFolder -Force | Out-Null
        $yamlDescription = $SkillDescription[$i] | ConvertTo-Json -Compress
        @"
---
name: $($SkillName[$i])
description: $yamlDescription
---

# $($SkillName[$i])

Define the focused workflow, activation boundaries, required inputs, and output
format for this skill. Move detailed material into references/.
"@ | Set-Content -LiteralPath (Join-Path $skillFolder 'SKILL.md') -Encoding utf8
    }

    @'
version: v1.11
environmentFolderPath: ./env
'@ | Set-Content -LiteralPath (Join-Path $fullProjectPath 'm365agents.yml') -Encoding utf8
    New-Item -ItemType Directory -Path (Join-Path $fullProjectPath 'env') -Force |
        Out-Null
}

[pscustomobject]@{
    ProjectPath = $fullProjectPath
    ManifestId = $manifest.id
    Skills = $SkillName.Count
    Status = 'Created'
}
