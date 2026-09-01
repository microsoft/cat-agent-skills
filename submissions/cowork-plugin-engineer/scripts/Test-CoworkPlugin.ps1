[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [string]$PackagePath,

    [switch]$AllowOAuthPlaceholder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PropertyValue {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Name
    )

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Assert-Text {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Label
    )

    $value = [string](Get-PropertyValue -Object $Object -Name $Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "$Label is required."
    }
    return $value
}

function Resolve-InRoot {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Label
    )

    $normalized = $RelativePath -replace '^[.][\\/]', ''
    if ([IO.Path]::IsPathRooted($normalized)) {
        throw "$Label must be package-relative: $RelativePath"
    }

    $candidate = [IO.Path]::GetFullPath((Join-Path $Root $normalized))
    $rootPrefix = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/') +
        [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the package root: $RelativePath"
    }
    return $candidate
}

function Get-PngDimensions {
    param([Parameter(Mandatory)][string]$Path)

    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 24) {
        throw "PNG is too small: $Path"
    }

    $signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    for ($i = 0; $i -lt $signature.Count; $i++) {
        if ($bytes[$i] -ne $signature[$i]) {
            throw "File is not a PNG: $Path"
        }
    }

    $width = ($bytes[16] -shl 24) -bor ($bytes[17] -shl 16) -bor
        ($bytes[18] -shl 8) -bor $bytes[19]
    $height = ($bytes[20] -shl 24) -bor ($bytes[21] -shl 16) -bor
        ($bytes[22] -shl 8) -bor $bytes[23]

    [pscustomobject]@{ Width = $width; Height = $height }
}

function Test-Placeholder {
    param(
        [string]$Value,
        [string]$ConnectorId
    )

    if ($Value -match '(?i)(REPLACE|PLACEHOLDER|YOUR[_-]|<[^>]+>|\{\{.+\}\})') {
        return $true
    }
    return -not [string]::IsNullOrWhiteSpace($ConnectorId) -and
        $Value.EndsWith("-$ConnectorId-auth", [StringComparison]::OrdinalIgnoreCase)
}

function Get-FrontmatterField {
    param(
        [Parameter(Mandatory)][string]$Frontmatter,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$SkillFile
    )

    $lines = @($Frontmatter -split '\r?\n')
    $fieldMatches = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^$([regex]::Escape($Name)):\s*(.*)$") {
            $fieldMatches += [pscustomobject]@{
                Index = $i
                Value = $Matches[1].Trim()
            }
        }
    }
    if ($fieldMatches.Count -ne 1) {
        throw "SKILL.md must define exactly one $Name field: $SkillFile"
    }

    $rawValue = $fieldMatches[0].Value
    if ($rawValue -match '^(?<style>[|>])[-+]?$') {
        $style = [string]$Matches['style']
        $blockLines = [Collections.Generic.List[string]]::new()
        for ($i = $fieldMatches[0].Index + 1; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Length -gt 0 -and $lines[$i] -notmatch '^\s') {
                break
            }
            $blockLines.Add($lines[$i])
        }
        $indents = @($blockLines | Where-Object { $_ -match '\S' } |
            ForEach-Object { ([regex]::Match($_, '^\s*')).Length })
        if ($indents.Count -eq 0) {
            throw "SKILL.md $Name block is empty: $SkillFile"
        }
        $indent = ($indents | Measure-Object -Minimum).Minimum
        $values = @($blockLines | ForEach-Object {
            if ($_.Length -ge $indent) { $_.Substring($indent) } else { '' }
        })
        $value = if ($style -eq '>') {
            ($values -join ' ') -replace '\s+', ' '
        }
        else {
            $values -join "`n"
        }
        return $value.Trim()
    }

    if ($rawValue.StartsWith('"') -and $rawValue.EndsWith('"')) {
        try {
            return [string]($rawValue | ConvertFrom-Json)
        }
        catch {
            throw "SKILL.md $Name has invalid double-quoted YAML: $SkillFile"
        }
    }
    if ($rawValue.StartsWith("'") -and $rawValue.EndsWith("'")) {
        return $rawValue.Substring(1, $rawValue.Length - 2).Replace("''", "'")
    }
    return ($rawValue -replace '\s+#.*$', '').Trim()
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$appPackage = Join-Path $resolvedProject 'appPackage'
$packageRoot = if (Test-Path -LiteralPath $appPackage -PathType Container) {
    $appPackage
} else {
    $resolvedProject
}

$manifestPath = Join-Path $packageRoot 'manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "manifest.json was not found at $manifestPath"
}

try {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 |
        ConvertFrom-Json
} catch {
    throw "manifest.json is not valid JSON: $($_.Exception.Message)"
}

$manifestVersion = Assert-Text $manifest 'manifestVersion' 'manifestVersion'
$schema = Assert-Text $manifest '$schema' '$schema'
if ($schema -notmatch "/v$([regex]::Escape($manifestVersion))/") {
    throw "`$schema and manifestVersion do not match: $schema / $manifestVersion"
}

$version = Assert-Text $manifest 'version' 'version'
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "version must use three numeric parts: $version"
}

$id = Assert-Text $manifest 'id' 'id'
$parsedId = [guid]::Empty
if (-not [guid]::TryParse($id, [ref]$parsedId) -or $parsedId -eq [guid]::Empty) {
    throw "id must be a non-empty GUID: $id"
}

$null = Assert-Text $manifest.developer 'name' 'developer.name'
foreach ($urlName in 'websiteUrl', 'privacyUrl', 'termsOfUseUrl') {
    $urlValue = Assert-Text $manifest.developer $urlName "developer.$urlName"
    $uri = [uri]$urlValue
    if ($uri.Scheme -ne 'https') {
        throw "developer.$urlName must use HTTPS: $urlValue"
    }
}

$colorPath = Resolve-InRoot $packageRoot $manifest.icons.color 'icons.color'
$outlinePath = Resolve-InRoot $packageRoot $manifest.icons.outline 'icons.outline'
foreach ($iconPath in $colorPath, $outlinePath) {
    if (-not (Test-Path -LiteralPath $iconPath -PathType Leaf)) {
        throw "Icon is missing: $iconPath"
    }
}
$colorSize = Get-PngDimensions $colorPath
$outlineSize = Get-PngDimensions $outlinePath
if ($colorSize.Width -ne 192 -or $colorSize.Height -ne 192) {
    throw "color.png must be 192x192; found $($colorSize.Width)x$($colorSize.Height)."
}
if ($outlineSize.Width -ne 32 -or $outlineSize.Height -ne 32) {
    throw "outline.png must be 32x32; found $($outlineSize.Width)x$($outlineSize.Height)."
}

$skills = @((Get-PropertyValue $manifest 'agentSkills') | Where-Object { $null -ne $_ })
$connectors = @((Get-PropertyValue $manifest 'agentConnectors') | Where-Object { $null -ne $_ })
if ($skills.Count -eq 0 -and $connectors.Count -eq 0) {
    throw 'At least one agentSkills or agentConnectors entry is required.'
}
if ($skills.Count -gt 20) {
    throw "A maximum of 20 registered skills is supported; found $($skills.Count)."
}

$skillNames = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
foreach ($skill in $skills) {
    $folder = Assert-Text $skill 'folder' 'agentSkills.folder'
    $skillFolder = Resolve-InRoot $packageRoot $folder 'agentSkills.folder'
    if (-not (Test-Path -LiteralPath $skillFolder -PathType Container)) {
        throw "Skill folder is missing: $folder"
    }

    $skillFile = Join-Path $skillFolder 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Registered skill is missing SKILL.md: $folder"
    }

    $nestedSkills = @(Get-ChildItem -LiteralPath $skillFolder -Recurse -File -Filter 'SKILL.md' |
        Where-Object { $_.FullName -ne $skillFile })
    if ($nestedSkills.Count -gt 0) {
        $paths = $nestedSkills.FullName -join ', '
        throw "Nested SKILL.md files are not valid companion documents: $paths"
    }

    $content = Get-Content -LiteralPath $skillFile -Raw -Encoding utf8
    $frontmatterMatch = [regex]::Match(
        $content,
        '(?s)\A---\r?\n(?<frontmatter>.*?)\r?\n---(?:\r?\n|$)'
    )
    if (-not $frontmatterMatch.Success) {
        throw "SKILL.md must start with YAML frontmatter: $skillFile"
    }

    $frontmatter = $frontmatterMatch.Groups['frontmatter'].Value
    $skillName = Get-FrontmatterField $frontmatter 'name' $skillFile
    $skillDescription = Get-FrontmatterField $frontmatter 'description' $skillFile
    if ([string]::IsNullOrWhiteSpace($skillDescription)) {
        throw "Skill description is required: $skillFile"
    }
    $folderName = Split-Path $skillFolder -Leaf
    if ($skillName -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
        throw "Skill name must be lowercase kebab-case: $skillName"
    }
    if ($skillName -cne $folderName) {
        throw "Skill name '$skillName' must match folder '$folderName'."
    }
    if (-not $skillNames.Add($skillName)) {
        throw "Duplicate skill name: $skillName"
    }

    $companions = @(Get-ChildItem -LiteralPath $skillFolder -Recurse -File |
        Where-Object { $_.FullName -ne $skillFile })
    if ($companions.Count -gt 20) {
        throw "Skill '$skillName' has $($companions.Count) companion files; maximum is 20."
    }
    foreach ($companion in $companions) {
        if ($companion.Length -gt 5MB) {
            throw "Companion file exceeds 5 MB: $($companion.FullName)"
        }
    }
    $companionBytes = if ($companions.Count -eq 0) {
        0
    }
    else {
        ($companions | Measure-Object -Property Length -Sum).Sum
    }
    if ($null -ne $companionBytes -and $companionBytes -gt 10MB) {
        throw "Skill '$skillName' companion files exceed 10 MB total."
    }
}

$connectorIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
foreach ($connector in $connectors) {
    $connectorId = Assert-Text $connector 'id' 'agentConnectors.id'
    if (-not $connectorIds.Add($connectorId)) {
        throw "Duplicate connector ID: $connectorId"
    }

    $null = Assert-Text $connector 'displayName' "connector '$connectorId' displayName"
    $remote = $connector.toolSource.remoteMcpServer
    if ($null -eq $remote) {
        throw "Connector '$connectorId' must define remoteMcpServer."
    }
    $serverUrl = Assert-Text $remote 'mcpServerUrl' "connector '$connectorId' URL"
    if (([uri]$serverUrl).Scheme -ne 'https') {
        throw "Connector '$connectorId' must use HTTPS: $serverUrl"
    }

    $toolDescription = Get-PropertyValue $remote 'mcpToolDescription'
    if ($null -eq $toolDescription) {
        throw "Connector '$connectorId' requires mcpToolDescription."
    }
    if ($null -ne $toolDescription) {
        $toolFile = Assert-Text $toolDescription 'file' "connector '$connectorId' tool file"
        $toolPath = Resolve-InRoot $packageRoot $toolFile "connector '$connectorId' tool file"
        if (-not (Test-Path -LiteralPath $toolPath -PathType Leaf)) {
            throw "Connector '$connectorId' tool file is missing: $toolFile"
        }
        $toolDocument = Get-Content -LiteralPath $toolPath -Raw -Encoding utf8 |
            ConvertFrom-Json
        $tools = @((Get-PropertyValue $toolDocument 'tools') | Where-Object { $null -ne $_ })
        if ($tools.Count -eq 0) {
            throw "Connector '$connectorId' tool description has no tools."
        }
        $toolNames = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($tool in $tools) {
            $toolName = Assert-Text $tool 'name' "connector '$connectorId' tool name"
            $null = Assert-Text $tool 'description' "tool '$toolName' description"
            if ($null -eq (Get-PropertyValue $tool 'inputSchema')) {
                throw "Tool '$toolName' is missing inputSchema."
            }
            if (-not $toolNames.Add($toolName)) {
                throw "Duplicate tool name in connector '$connectorId': $toolName"
            }
        }
    }

    $authorization = Get-PropertyValue $remote 'authorization'
    if ($null -ne $authorization) {
        $authType = Assert-Text $authorization 'type' "connector '$connectorId' auth type"
        $referenceId = [string](Get-PropertyValue $authorization 'referenceId')
        switch ($authType) {
            'None' {
                if (-not [string]::IsNullOrWhiteSpace($referenceId)) {
                    throw "Connector '$connectorId' uses None and must omit referenceId."
                }
            }
            'OAuthPluginVault' {
                if ([string]::IsNullOrWhiteSpace($referenceId)) {
                    throw "Connector '$connectorId' requires an OAuth referenceId."
                }
                if (-not $AllowOAuthPlaceholder -and
                    (Test-Placeholder $referenceId $connectorId)) {
                    throw "Connector '$connectorId' has unresolved OAuth placeholder '$referenceId'."
                }
            }
            'ApiKeyPluginVault' {
                throw "ApiKeyPluginVault is not currently a deployable Cowork connector authentication type."
            }
            'DynamicClientRegistration' {
                throw "Connector '$connectorId' must omit authorization to use Dynamic Client Registration."
            }
            default {
                throw "Connector '$connectorId' uses unsupported auth type '$authType'."
            }
        }
    }
}

if (-not [string]::IsNullOrWhiteSpace($PackagePath)) {
    $resolvedPackage = (Resolve-Path -LiteralPath $PackagePath).Path
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($resolvedPackage)
    try {
        $entryNames = @($archive.Entries.FullName | ForEach-Object {
            $_.Replace('\', '/')
        })
        if ('manifest.json' -notin $entryNames) {
            throw 'ZIP does not contain manifest.json at its root.'
        }
        foreach ($requiredPath in @(
            $manifest.icons.color,
            $manifest.icons.outline
        )) {
            $zipPath = $requiredPath -replace '^[.][\\/]', ''
            if ($zipPath -notin $entryNames) {
                throw "ZIP is missing referenced file: $zipPath"
            }
        }
    } finally {
        $archive.Dispose()
    }
}

[pscustomobject]@{
    ProjectPath = $resolvedProject
    ManifestPath = $manifestPath
    ManifestVersion = $manifestVersion
    Version = $version
    Skills = $skills.Count
    Connectors = $connectors.Count
    PackageChecked = -not [string]::IsNullOrWhiteSpace($PackagePath)
    Status = 'Passed'
}
