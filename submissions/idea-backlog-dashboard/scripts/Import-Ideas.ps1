<#
.SYNOPSIS  Stores ideas captured by the Copilot Studio agent (JSON array or object) into Dataverse. Also used to seed sample data.
.PARAMETER Path  JSON file. Fields: title, description, submittedBy, submitterEmail, category, priority (Low|Medium|High),
                 status (New|In Progress|Completed), businessValue, source, conversationId
#>
param([Parameter(Mandatory)][string]$Path)
. "$PSScriptRoot\Common.ps1"
$cfg = Get-Cfg; $token = Get-Token $cfg; $p = $cfg.Prefix; $script:SolutionName = $null
$status = @{ 'New'=100000000; 'In Progress'=100000001; 'Completed'=100000002 }
$prio = @{ 'Low'=100000000; 'Medium'=100000001; 'High'=100000002 }
$cat = @{ 'Process'=100000000; 'Product'=100000001; 'Technology'=100000002; 'Customer Experience'=100000003; 'Other'=100000004 }

$items = @(Get-Content -Raw $Path | ConvertFrom-Json)
foreach ($i in $items) {
    if (-not $i.title) { Write-Warning 'Skipped idea without title'; continue }
    $st = if ($i.status -and $status[$i.status]) { $status[$i.status] } else { 100000000 }
    $row = @{
        "${p}_title"=$i.title; "${p}_description"=$i.description; "${p}_submittedby"=$i.submittedBy
        "${p}_submitteremail"=$i.submitterEmail; "${p}_businessvalue"=$i.businessValue
        "${p}_source"=$(if ($i.source) { $i.source } else { 'Copilot Studio' }); "${p}_conversationid"=$i.conversationId
        "${p}_status"=$st
        "${p}_priority"=$(if ($i.priority -and $prio[$i.priority]) { $prio[$i.priority] } else { 100000001 })
        "${p}_category"=$(if ($i.category -and $cat[$i.category]) { $cat[$i.category] } else { 100000004 })
    }
    if ($st -eq 100000002) { $row["${p}_completedon"] = (Get-Date).ToString('yyyy-MM-dd') }
    Invoke-Dv $cfg $token POST "${p}_ideas" $row | Out-Null
    Write-Host "Stored: $($i.title)"
}
