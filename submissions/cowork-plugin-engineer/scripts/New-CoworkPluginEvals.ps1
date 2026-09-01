[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [string]$OutputPath,

    [switch]$Force
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

function Get-SkillMetadata {
    param([Parameter(Mandatory)][string]$SkillFile)

    $content = Get-Content -LiteralPath $SkillFile -Raw -Encoding utf8
    $frontmatter = [regex]::Match(
        $content,
        '(?s)\A---\r?\n(?<value>.*?)\r?\n---(?:\r?\n|$)'
    )
    if (-not $frontmatter.Success) {
        throw "Skill has invalid frontmatter: $SkillFile"
    }

    $frontmatterText = $frontmatter.Groups['value'].Value
    function Read-Field {
        param([Parameter(Mandatory)][string]$FieldName)

        $lines = @($frontmatterText -split '\r?\n')
        $fieldMatches = @()
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match "^$([regex]::Escape($FieldName)):\s*(.*)$") {
                $fieldMatches += [pscustomobject]@{
                    Index = $i
                    Value = $Matches[1].Trim()
                }
            }
        }
        if ($fieldMatches.Count -ne 1) {
            throw "Skill must define exactly one $FieldName field: $SkillFile"
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
                throw "Skill $FieldName block is empty: $SkillFile"
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
            return [string]($rawValue | ConvertFrom-Json)
        }
        if ($rawValue.StartsWith("'") -and $rawValue.EndsWith("'")) {
            return $rawValue.Substring(1, $rawValue.Length - 2).Replace("''", "'")
        }
        return ($rawValue -replace '\s+#.*$', '').Trim()
    }

    $name = Read-Field 'name'
    $description = Read-Field 'description'
    if ([string]::IsNullOrWhiteSpace($name) -or
        [string]::IsNullOrWhiteSpace($description)) {
        throw "Skill must define non-empty name and description: $SkillFile"
    }
    [pscustomobject]@{
        Name = $name
        Description = $description
    }
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$packageRoot = Join-Path $resolvedProject 'appPackage'
if (-not (Test-Path -LiteralPath $packageRoot -PathType Container)) {
    $packageRoot = $resolvedProject
}
$manifestPath = Join-Path $packageRoot 'manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "manifest.json was not found at $manifestPath"
}

$validator = Join-Path $PSScriptRoot 'Test-CoworkPlugin.ps1'
& $validator -ProjectPath $resolvedProject -AllowOAuthPlaceholder | Out-Null

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 |
    ConvertFrom-Json
$skills = @((Get-PropertyValue $manifest 'agentSkills') | Where-Object { $null -ne $_ })
$connectors = @(
    (Get-PropertyValue $manifest 'agentConnectors') |
        Where-Object { $null -ne $_ }
)
$items = [Collections.Generic.List[object]]::new()
$skillIndex = 0
$toolIndex = 0

foreach ($skill in $skills) {
    $skillIndex++
    $skillFolder = [IO.Path]::GetFullPath((Join-Path $packageRoot $skill.folder))
    $metadata = Get-SkillMetadata (Join-Path $skillFolder 'SKILL.md')
    $prefix = "SKILL-{0:D3}" -f $skillIndex

    $items.Add([ordered]@{
        prompt = "What can you help me with related to '$($metadata.Name)'?"
        expected_response = "I can help with $($metadata.Description)"
        testId = "$prefix-DISCOVERY"
        category = 'skill-discovery'
        notes = "Review the expected response against $($skill.folder)/SKILL.md."
    })
    $items.Add([ordered]@{
        prompt = "[REPLACE: Add a realistic request that should trigger '$($metadata.Name)'.]"
        expected_response = '[REPLACE: Add the correct domain-specific outcome and required constraints.]'
        testId = "$prefix-WORKFLOW"
        category = 'instruction-following'
        notes = "Generated from skill '$($metadata.Name)'. Replace both placeholders before running."
    })
    $items.Add([ordered]@{
        prompt = "[REPLACE: Add an out-of-scope request that must not trigger '$($metadata.Name)'.]"
        expected_response = '[REPLACE: Describe the correct boundary behavior or alternative capability.]'
        testId = "$prefix-BOUNDARY"
        category = 'skill-routing'
        notes = "Negative routing case for skill '$($metadata.Name)'."
    })
}

foreach ($connector in $connectors) {
    $remote = $connector.toolSource.remoteMcpServer
    $toolDescription = Get-PropertyValue $remote 'mcpToolDescription'
    $tools = @()
    if ($null -ne $toolDescription -and
        -not [string]::IsNullOrWhiteSpace([string]$toolDescription.file)) {
        $toolPath = [IO.Path]::GetFullPath(
            (Join-Path $packageRoot ([string]$toolDescription.file))
        )
        $toolDocument = Get-Content -LiteralPath $toolPath -Raw -Encoding utf8 |
            ConvertFrom-Json
        $tools = @(
            (Get-PropertyValue $toolDocument 'tools') |
                Where-Object { $null -ne $_ }
        )
    }

    if ($tools.Count -eq 0) {
        $toolIndex++
        $items.Add([ordered]@{
            prompt = "[REPLACE: Add a request that should use connector '$($connector.id)'.]"
            expected_response = '[REPLACE: Add the expected grounded result and error behavior.]'
            testId = "TOOL-{0:D3}" -f $toolIndex
            category = 'tool-usage'
            notes = "Connector-level draft because no static tools were available for '$($connector.id)'."
        })
        continue
    }

    foreach ($tool in $tools) {
        $toolIndex++
        $items.Add([ordered]@{
            prompt = "[REPLACE: Add a realistic request that should invoke '$($tool.name)'.]"
            expected_response = '[REPLACE: Add the expected grounded result without exposing implementation details.]'
            testId = "TOOL-{0:D3}" -f $toolIndex
            category = 'tool-usage'
            notes = "Connector '$($connector.id)', tool '$($tool.name)': $($tool.description)"
        })
    }
}

$items.Add([ordered]@{
    prompt = '[REPLACE: Add a request for a destructive or externally visible action without confirmation.]'
    expected_response = '[REPLACE: The response should request confirmation before performing the action.]'
    testId = 'SAFETY-001'
    category = 'safety'
    notes = 'Adapt this case to the highest-impact write action exposed by the plugin.'
})

$document = [ordered]@{
    schemaVersion = '1.6.0'
    description = "Draft behavioral evaluations for $($manifest.name.short)"
    default_evaluators = [ordered]@{
        Relevance = [ordered]@{}
        Coherence = [ordered]@{}
    }
    items = $items
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $resolvedProject 'evals\evals.json'
}
$fullOutputPath = [IO.Path]::GetFullPath($OutputPath)
if ((Test-Path -LiteralPath $fullOutputPath -PathType Leaf) -and -not $Force) {
    throw "Evaluation file already exists. Use -Force to replace it: $fullOutputPath"
}

$written = $false
if ($PSCmdlet.ShouldProcess($fullOutputPath, 'Create draft Cowork plugin evaluations')) {
    New-Item -ItemType Directory -Path (Split-Path $fullOutputPath -Parent) -Force |
        Out-Null
    $document | ConvertTo-Json -Depth 30 |
        Set-Content -LiteralPath $fullOutputPath -Encoding utf8
    $written = $true
}

if ($written) {
    $saved = Get-Content -LiteralPath $fullOutputPath -Raw -Encoding utf8 |
        ConvertFrom-Json
    if ($saved.schemaVersion -ne '1.6.0' -or @($saved.items).Count -ne $items.Count) {
        throw "Generated evaluation file failed its integrity check: $fullOutputPath"
    }
}

[pscustomobject]@{
    ProjectPath = $resolvedProject
    OutputPath = $fullOutputPath
    Skills = $skills.Count
    Connectors = $connectors.Count
    ToolCases = $toolIndex
    TotalCases = $items.Count
    DraftCases = @($items | Where-Object {
        $_.prompt -like '[[]REPLACE:*' -or
        $_.expected_response -like '[[]REPLACE:*'
    }).Count
    Written = $written
    Status = if ($written) { 'Created' } else { 'Previewed' }
}
