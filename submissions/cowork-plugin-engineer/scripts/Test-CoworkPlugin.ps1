[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [string]$PackagePath,

    [switch]$AllowOAuthPlaceholder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSVersionTable.PSVersion -lt [version]'7.2') {
    throw 'Test-CoworkPlugin.ps1 requires PowerShell 7.2 or later.'
}

if ($null -eq ('CoworkPluginValidation.NonBufferingReadStream' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;

namespace CoworkPluginValidation
{
    public sealed class NonBufferingReadStream : Stream
    {
        private readonly Stream inner;

        public NonBufferingReadStream(Stream inner)
        {
            this.inner = inner ?? throw new ArgumentNullException(nameof(inner));
        }

        public override bool CanRead => inner.CanRead;
        public override bool CanSeek => inner.CanSeek;
        public override bool CanWrite => false;
        public override long Length => inner.Length;
        public override long Position
        {
            get => inner.Position;
            set => inner.Position = value;
        }

        public override void Flush() { }
        public override long Seek(long offset, SeekOrigin origin) =>
            inner.Seek(offset, origin);
        public override void SetLength(long value) =>
            throw new NotSupportedException();
        public override void Write(byte[] buffer, int offset, int count) =>
            throw new NotSupportedException();
        public override int Read(byte[] buffer, int offset, int count) =>
            inner.Read(buffer, offset, Math.Min(count, 1));
        public override int Read(Span<byte> buffer) =>
            buffer.Length == 0 ? 0 : inner.Read(buffer.Slice(0, 1));
        public override int ReadByte() => inner.ReadByte();
    }
}
'@
}

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

function Read-PngUInt32 {
    param(
        [Parameter(Mandatory)][byte[]]$Bytes,
        [Parameter(Mandatory)][int]$Offset
    )

    return ([uint32]$Bytes[$Offset] -shl 24) -bor
        ([uint32]$Bytes[$Offset + 1] -shl 16) -bor
        ([uint32]$Bytes[$Offset + 2] -shl 8) -bor
        [uint32]$Bytes[$Offset + 3]
}

function Get-PngSample {
    param(
        [Parameter(Mandatory)][byte[]]$Row,
        [Parameter(Mandatory)][int]$Index,
        [Parameter(Mandatory)][int]$BitDepth
    )

    switch ($BitDepth) {
        8 { return [int]$Row[$Index] }
        16 {
            $offset = $Index * 2
            return ([int]$Row[$offset] -shl 8) -bor $Row[$offset + 1]
        }
        { $_ -in 1, 2, 4 } {
            $samplesPerByte = 8 / $BitDepth
            $byteIndex = [math]::Floor($Index / $samplesPerByte)
            $sampleInByte = $Index % $samplesPerByte
            $shift = 8 - $BitDepth - ($sampleInByte * $BitDepth)
            $mask = (1 -shl $BitDepth) - 1
            return ([int]$Row[$byteIndex] -shr $shift) -band $mask
        }
        default { throw "Unsupported PNG bit depth: $BitDepth" }
    }
}

function Get-PaethPredictor {
    param(
        [int]$Left,
        [int]$Up,
        [int]$UpperLeft
    )

    $estimate = $Left + $Up - $UpperLeft
    $leftDistance = [math]::Abs($estimate - $Left)
    $upDistance = [math]::Abs($estimate - $Up)
    $upperLeftDistance = [math]::Abs($estimate - $UpperLeft)
    if ($leftDistance -le $upDistance -and
        $leftDistance -le $upperLeftDistance) {
        return $Left
    }
    if ($upDistance -le $upperLeftDistance) {
        return $Up
    }
    return $UpperLeft
}

function Assert-OutlinePngPixels {
    param([Parameter(Mandatory)][string]$Path)

    $bytes = [IO.File]::ReadAllBytes($Path)
    $offset = 8
    $width = 0
    $height = 0
    $bitDepth = 0
    $colorType = 0
    $interlace = 0
    [byte[]]$palette = @()
    [byte[]]$transparency = @()
    $foundIend = $false
    $compressed = [IO.MemoryStream]::new()
    try {
        while ($offset + 12 -le $bytes.Length) {
            $length = [int](Read-PngUInt32 $bytes $offset)
            $type = [Text.Encoding]::ASCII.GetString($bytes, $offset + 4, 4)
            $dataOffset = $offset + 8
            if ($length -lt 0 -or $dataOffset + $length + 4 -gt $bytes.Length) {
                throw "PNG contains an invalid chunk: $Path"
            }

            switch ($type) {
                'IHDR' {
                    if ($length -ne 13) {
                        throw "PNG has an invalid IHDR chunk: $Path"
                    }
                    $width = [int](Read-PngUInt32 $bytes $dataOffset)
                    $height = [int](Read-PngUInt32 $bytes ($dataOffset + 4))
                    $bitDepth = $bytes[$dataOffset + 8]
                    $colorType = $bytes[$dataOffset + 9]
                    $interlace = $bytes[$dataOffset + 12]
                }
                'PLTE' {
                    $palette = [byte[]]::new($length)
                    [Array]::Copy($bytes, $dataOffset, $palette, 0, $length)
                }
                'tRNS' {
                    $transparency = [byte[]]::new($length)
                    [Array]::Copy($bytes, $dataOffset, $transparency, 0, $length)
                }
                'IDAT' { $compressed.Write($bytes, $dataOffset, $length) }
                'IEND' {
                    if ($length -ne 0) {
                        throw "PNG has an invalid IEND chunk: $Path"
                    }
                    $foundIend = $true
                }
            }
            $offset = $dataOffset + $length + 4
            if ($foundIend) {
                if ($offset -ne $bytes.Length) {
                    throw "PNG contains data after its IEND chunk: $Path"
                }
                break
            }
        }
        if (-not $foundIend) {
            throw "PNG is missing its IEND chunk: $Path"
        }

        if ($width -ne 32 -or $height -ne 32) {
            throw "outline.png must be 32x32; found ${width}x${height}."
        }
        if ($interlace -ne 0) {
            throw 'outline.png must use a non-interlaced PNG encoding for pixel validation.'
        }

        $channels = switch ($colorType) {
            0 { 1 }
            2 { 3 }
            3 { 1 }
            4 { 2 }
            6 { 4 }
            default { throw "outline.png uses unsupported PNG color type $colorType." }
        }
        $validDepths = switch ($colorType) {
            0 { @(1, 2, 4, 8, 16) }
            2 { @(8, 16) }
            3 { @(1, 2, 4, 8) }
            4 { @(8, 16) }
            6 { @(8, 16) }
        }
        if ($bitDepth -notin $validDepths) {
            throw "outline.png uses unsupported bit depth $bitDepth for color type $colorType."
        }
        if ($colorType -eq 3 -and ($palette.Length -eq 0 -or
            $palette.Length % 3 -ne 0)) {
            throw 'outline.png has an invalid or missing PNG palette.'
        }

        $rowBytes = [int][math]::Ceiling($width * $channels * $bitDepth / 8)
        $filterBytesPerPixel = [math]::Max(
            1,
            [int][math]::Ceiling($channels * $bitDepth / 8)
        )
        $compressed.Position = 0
        $strictCompressed = [CoworkPluginValidation.NonBufferingReadStream]::new(
            $compressed
        )
        $expectedBytes = ($rowBytes + 1) * $height
        $scanlines = [byte[]]::new($expectedBytes)
        $zlib = [IO.Compression.ZLibStream]::new(
            $strictCompressed,
            [IO.Compression.CompressionMode]::Decompress,
            $true
        )
        try {
            $totalRead = 0
            while ($totalRead -lt $expectedBytes) {
                $read = $zlib.Read(
                    $scanlines,
                    $totalRead,
                    $expectedBytes - $totalRead
                )
                if ($read -eq 0) {
                    break
                }
                $totalRead += $read
            }
            $overflow = [byte[]]::new(1)
            if ($totalRead -ne $expectedBytes -or
                $zlib.Read($overflow, 0, 1) -ne 0) {
                throw 'outline.png has unexpected decompressed pixel data.'
            }
            if ($strictCompressed.Position -ne $strictCompressed.Length) {
                throw 'outline.png IDAT contains data after its zlib stream.'
            }
        }
        finally {
            $zlib.Dispose()
            $strictCompressed.Dispose()
        }

        $reconstructed = [byte[]]::new($rowBytes * $height)
        for ($y = 0; $y -lt $height; $y++) {
            $sourceOffset = $y * ($rowBytes + 1)
            $filter = $scanlines[$sourceOffset]
            for ($x = 0; $x -lt $rowBytes; $x++) {
                $raw = [int]$scanlines[$sourceOffset + 1 + $x]
                $targetOffset = ($y * $rowBytes) + $x
                $left = if ($x -ge $filterBytesPerPixel) {
                    [int]$reconstructed[$targetOffset - $filterBytesPerPixel]
                } else { 0 }
                $up = if ($y -gt 0) {
                    [int]$reconstructed[$targetOffset - $rowBytes]
                } else { 0 }
                $upperLeft = if ($y -gt 0 -and $x -ge $filterBytesPerPixel) {
                    [int]$reconstructed[
                        $targetOffset - $rowBytes - $filterBytesPerPixel
                    ]
                } else { 0 }
                $predictor = switch ($filter) {
                    0 { 0 }
                    1 { $left }
                    2 { $up }
                    3 { [math]::Floor(($left + $up) / 2) }
                    4 { Get-PaethPredictor $left $up $upperLeft }
                    default { throw "outline.png uses invalid PNG filter $filter." }
                }
                $reconstructed[$targetOffset] = [byte](($raw + $predictor) -band 255)
            }
        }

        $maxSample = (1 -shl $bitDepth) - 1
        if ($bitDepth -eq 16) {
            $maxSample = 65535
        }
        $transparentPixels = 0
        $visiblePixels = 0
        for ($y = 0; $y -lt $height; $y++) {
            $row = [byte[]]::new($rowBytes)
            [Array]::Copy($reconstructed, $y * $rowBytes, $row, 0, $rowBytes)
            for ($x = 0; $x -lt $width; $x++) {
                $sampleIndex = $x * $channels
                $channelMax = $maxSample
                $alphaSample = $maxSample
                switch ($colorType) {
                    0 {
                        $graySample = Get-PngSample $row $sampleIndex $bitDepth
                        $redSample = $greenSample = $blueSample = $graySample
                        if ($transparency.Length -ge 2) {
                            $transparentGray = ([int]$transparency[0] -shl 8) -bor
                                $transparency[1]
                            if ($graySample -eq $transparentGray) {
                                $alphaSample = 0
                            }
                        }
                    }
                    2 {
                        $redSample = Get-PngSample $row $sampleIndex $bitDepth
                        $greenSample = Get-PngSample $row ($sampleIndex + 1) $bitDepth
                        $blueSample = Get-PngSample $row ($sampleIndex + 2) $bitDepth
                        if ($transparency.Length -ge 6) {
                            $transparentRed = ([int]$transparency[0] -shl 8) -bor
                                $transparency[1]
                            $transparentGreen = ([int]$transparency[2] -shl 8) -bor
                                $transparency[3]
                            $transparentBlue = ([int]$transparency[4] -shl 8) -bor
                                $transparency[5]
                            if ($redSample -eq $transparentRed -and
                                $greenSample -eq $transparentGreen -and
                                $blueSample -eq $transparentBlue) {
                                $alphaSample = 0
                            }
                        }
                    }
                    3 {
                        $paletteIndex = Get-PngSample $row $sampleIndex $bitDepth
                        $paletteOffset = $paletteIndex * 3
                        if ($paletteOffset + 2 -ge $palette.Length) {
                            throw "outline.png references missing palette index $paletteIndex."
                        }
                        $channelMax = 255
                        $redSample = $palette[$paletteOffset]
                        $greenSample = $palette[$paletteOffset + 1]
                        $blueSample = $palette[$paletteOffset + 2]
                        $alphaSample = 255
                        if ($paletteIndex -lt $transparency.Length) {
                            $alphaSample = $transparency[$paletteIndex]
                        }
                    }
                    4 {
                        $graySample = Get-PngSample $row $sampleIndex $bitDepth
                        $alphaSample = Get-PngSample $row ($sampleIndex + 1) $bitDepth
                        $redSample = $greenSample = $blueSample = $graySample
                    }
                    6 {
                        $redSample = Get-PngSample $row $sampleIndex $bitDepth
                        $greenSample = Get-PngSample $row ($sampleIndex + 1) $bitDepth
                        $blueSample = Get-PngSample $row ($sampleIndex + 2) $bitDepth
                        $alphaSample = Get-PngSample $row ($sampleIndex + 3) $bitDepth
                    }
                }

                if ($alphaSample -eq 0) {
                    $transparentPixels++
                }
                else {
                    $visiblePixels++
                    if ($redSample -ne $channelMax -or
                        $greenSample -ne $channelMax -or
                        $blueSample -ne $channelMax) {
                        $red = [int][math]::Round(
                            $redSample * 255 / $channelMax
                        )
                        $green = [int][math]::Round(
                            $greenSample * 255 / $channelMax
                        )
                        $blue = [int][math]::Round(
                            $blueSample * 255 / $channelMax
                        )
                        $alpha = [int][math]::Round(
                            $alphaSample * 255 / $channelMax
                        )
                        throw "outline.png contains a non-white visible pixel at ($x,$y): RGBA($red,$green,$blue,$alpha)."
                    }
                }
            }
        }
        if ($transparentPixels -eq 0 -or $visiblePixels -eq 0) {
            throw 'outline.png must contain both transparent and visible white pixels.'
        }
    }
    finally {
        $compressed.Dispose()
    }
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
Assert-OutlinePngPixels $outlinePath

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
