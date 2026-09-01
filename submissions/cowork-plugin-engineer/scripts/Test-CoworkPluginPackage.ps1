[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PackagePath,

    [string]$AtkVersion = '1.1.15',

    [switch]$AllowOAuthPlaceholder,

    [switch]$SkipToolkitValidation,

    [ValidateRange(1, 5000)]
    [int]$MaxEntries = 1000,

    [ValidateRange(1MB, 1GB)]
    [long]$MaxExtractedBytes = 250MB
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolvedPackage = (Resolve-Path -LiteralPath $PackagePath).Path
if ([IO.Path]::GetExtension($resolvedPackage) -ine '.zip') {
    throw "Package must be a ZIP file: $resolvedPackage"
}

$temporaryRoot = $null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($resolvedPackage)
$entries = @()
$totalBytes = 0L
$seenPaths = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)

try {
    if ($archive.Entries.Count -gt $MaxEntries) {
        throw "ZIP contains $($archive.Entries.Count) entries; maximum is $MaxEntries."
    }

    foreach ($entry in $archive.Entries) {
        $entryPath = $entry.FullName.Replace('\', '/')
        if ([string]::IsNullOrWhiteSpace($entryPath)) {
            throw 'ZIP contains an entry with an empty path.'
        }
        if ($entryPath.StartsWith('/') -or $entryPath.Contains(':')) {
            throw "ZIP contains an absolute path: $entryPath"
        }
        $segments = @($entryPath.Split('/') | Where-Object { $_ -ne '' })
        if (@($segments | Where-Object { $_ -in '.', '..' }).Count -gt 0) {
            throw "ZIP entry escapes the package root: $entryPath"
        }
        if (@($segments | Where-Object { $_ -match '[. ]$' }).Count -gt 0) {
            throw "ZIP entry has a Windows-ambiguous path: $entryPath"
        }
        if (-not $seenPaths.Add($entryPath.TrimEnd('/'))) {
            throw "ZIP contains a duplicate path: $entryPath"
        }

        $unixFileType = ($entry.ExternalAttributes -shr 16) -band 0xF000
        if ($unixFileType -eq 0xA000) {
            throw "ZIP contains a symbolic link, which is not allowed: $entryPath"
        }

        $totalBytes += $entry.Length
        if ($totalBytes -gt $MaxExtractedBytes) {
            throw "ZIP expands beyond the $MaxExtractedBytes byte safety limit."
        }
        $entries += [pscustomobject]@{
            Entry = $entry
            Path = $entryPath
        }
    }

    if (-not $seenPaths.Contains('manifest.json')) {
        throw 'ZIP must contain manifest.json at its root; wrapper directories are not supported.'
    }

    $temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) (
        "cowork-plugin-validation-$([guid]::NewGuid().ToString('N'))"
    )
    New-Item -ItemType Directory -Path $temporaryRoot | Out-Null

    try {
        $rootPrefix = [IO.Path]::GetFullPath($temporaryRoot).TrimEnd('\', '/') +
            [IO.Path]::DirectorySeparatorChar
        foreach ($item in $entries) {
            $relativePath = $item.Path.Replace('/', [IO.Path]::DirectorySeparatorChar)
            $targetPath = [IO.Path]::GetFullPath((Join-Path $temporaryRoot $relativePath))
            if (-not $targetPath.StartsWith(
                $rootPrefix,
                [StringComparison]::OrdinalIgnoreCase
            )) {
                throw "ZIP entry escapes the extraction directory: $($item.Path)"
            }

            if ($item.Path.EndsWith('/')) {
                New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
                continue
            }

            $targetFolder = Split-Path $targetPath -Parent
            New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
            $sourceStream = $item.Entry.Open()
            $targetStream = [IO.File]::Create($targetPath)
            try {
                $sourceStream.CopyTo($targetStream)
            }
            finally {
                $targetStream.Dispose()
                $sourceStream.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }

    $projectValidator = Join-Path $PSScriptRoot 'Test-CoworkPlugin.ps1'
    $validation = & $projectValidator `
        -ProjectPath $temporaryRoot `
        -PackagePath $resolvedPackage `
        -AllowOAuthPlaceholder:$AllowOAuthPlaceholder

    if (-not $SkipToolkitValidation) {
        $packageName = "@microsoft/m365agentstoolkit-cli@$AtkVersion"
        & npx --yes $packageName validate --package-file $resolvedPackage | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "atk validate failed with exit code $LASTEXITCODE."
        }
    }

    [pscustomobject]@{
        PackagePath = $resolvedPackage
        Entries = $entries.Count
        UncompressedBytes = $totalBytes
        ManifestVersion = $validation.ManifestVersion
        Version = $validation.Version
        Skills = $validation.Skills
        Connectors = $validation.Connectors
        ToolkitValidated = -not $SkipToolkitValidation
        AtkVersion = if ($SkipToolkitValidation) { $null } else { $AtkVersion }
        Status = 'Passed'
    }
}
finally {
    if ($archive) {
        $archive.Dispose()
    }
    if ($null -ne $temporaryRoot -and
        (Test-Path -LiteralPath $temporaryRoot -PathType Container)) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
