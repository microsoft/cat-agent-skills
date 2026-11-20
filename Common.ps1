# Shared helpers. Dot-source: . "$PSScriptRoot\Common.ps1"
# Required environment variables (names only; never commit values):
#   DATAVERSE_ENV_URL, DATAVERSE_TENANT_ID, DATAVERSE_CLIENT_ID, DATAVERSE_CLIENT_SECRET, DATAVERSE_PUBLISHER_PREFIX
$ErrorActionPreference = 'Stop'

function Get-Cfg {
    $names = 'DATAVERSE_ENV_URL','DATAVERSE_TENANT_ID','DATAVERSE_CLIENT_ID','DATAVERSE_CLIENT_SECRET','DATAVERSE_PUBLISHER_PREFIX'
    $missing = $names | Where-Object { -not (Get-Item "env:$_" -ErrorAction SilentlyContinue) }
    if ($missing) { throw "Missing environment variables: $($missing -join ', ')" }
    [pscustomobject]@{
        Url    = $env:DATAVERSE_ENV_URL.TrimEnd('/')
        Tenant = $env:DATAVERSE_TENANT_ID
        Client = $env:DATAVERSE_CLIENT_ID
        Secret = $env:DATAVERSE_CLIENT_SECRET
        Prefix = $env:DATAVERSE_PUBLISHER_PREFIX.ToLower()
    }
}

function Get-Token($cfg) {
    $body = @{ grant_type='client_credentials'; client_id=$cfg.Client; client_secret=$cfg.Secret; scope="$($cfg.Url)/.default" }
    (Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$($cfg.Tenant)/oauth2/v2.0/token" -Body $body).access_token
}

function Invoke-Dv($cfg, $token, [string]$Method, [string]$Path, $Body = $null) {
    $h = @{ Authorization="Bearer $token"; 'OData-MaxVersion'='4.0'; 'OData-Version'='4.0'; Accept='application/json' }
    if ($script:SolutionName) { $h['MSCRM.SolutionUniqueName'] = $script:SolutionName }
    $a = @{ Method=$Method; Uri="$($cfg.Url)/api/data/v9.2/$Path"; Headers=$h }
    if ($null -ne $Body) { $a.Body = ($Body | ConvertTo-Json -Depth 20); $a.ContentType = 'application/json; charset=utf-8' }
    Invoke-RestMethod @a
}

function New-Label([string]$Text) {
    @{ '@odata.type'='Microsoft.Dynamics.CRM.Label'; LocalizedLabels=@(@{ '@odata.type'='Microsoft.Dynamics.CRM.LocalizedLabel'; Label=$Text; LanguageCode=1033 }) }
}
