<#
.SYNOPSIS  Creates the solution, Idea table, columns and choices in Dataverse (idempotent).
#>
param([string]$SolutionName = 'IdeaBacklog', [string]$PublisherUniqueName = '')
. "$PSScriptRoot\Common.ps1"
$cfg = Get-Cfg; $token = Get-Token $cfg; $p = $cfg.Prefix
$script:SolutionName = $null

$pubs = Invoke-Dv $cfg $token GET "publishers?`$select=publisherid,uniquename,customizationprefix&`$filter=customizationprefix eq '$p'"
if (-not $pubs.value) { throw "No publisher with prefix '$p'. Create one (Power Apps > Solutions > Publishers) and re-run." }
$pub = if ($PublisherUniqueName) { $pubs.value | Where-Object uniquename -eq $PublisherUniqueName | Select-Object -First 1 } else { $pubs.value | Select-Object -First 1 }
$sol = Invoke-Dv $cfg $token GET "solutions?`$select=solutionid&`$filter=uniquename eq '$SolutionName'"
if (-not $sol.value) {
    Invoke-Dv $cfg $token POST 'solutions' @{ uniquename=$SolutionName; friendlyname='Idea Backlog'; version='1.0.0.0'; 'publisherid@odata.bind'="/publishers($($pub.publisherid))" } | Out-Null
    Write-Host "Created solution $SolutionName"
}
$script:SolutionName = $SolutionName

$table = "${p}_idea"
$exists = $true
try { Invoke-Dv $cfg $token GET "EntityDefinitions(LogicalName='$table')?`$select=LogicalName" | Out-Null } catch { $exists = $false }

if (-not $exists) {
    $def = @{
        '@odata.type'='Microsoft.Dynamics.CRM.EntityMetadata'
        SchemaName=$table; OwnershipType='UserOwned'; HasNotes=$true; HasActivities=$false
        DisplayName=(New-Label 'Idea'); DisplayCollectionName=(New-Label 'Ideas')
        Description=(New-Label 'Ideas captured from users by the Copilot Studio agent')
        Attributes=@(@{
            '@odata.type'='Microsoft.Dynamics.CRM.StringAttributeMetadata'; SchemaName="${p}_title"; IsPrimaryName=$true
            RequiredLevel=@{Value='ApplicationRequired'}; MaxLength=200; FormatName=@{Value='Text'}; DisplayName=(New-Label 'Title')
        })
    }
    Invoke-Dv $cfg $token POST 'EntityDefinitions' $def | Out-Null
    Write-Host "Created table $table"
}

function Add-Col($body) {
    $name = $body.SchemaName.ToLower()
    $found = $true
    try { Invoke-Dv $cfg $token GET "EntityDefinitions(LogicalName='$table')/Attributes(LogicalName='$name')?`$select=LogicalName" | Out-Null } catch { $found = $false }
    if ($found) { Write-Host "  exists: $name"; return }
    Invoke-Dv $cfg $token POST "EntityDefinitions(LogicalName='$table')/Attributes" $body | Out-Null
    Write-Host "  added:  $name"
}
function Str($n,$l,$max=200,$fmt='Text') { @{ '@odata.type'='Microsoft.Dynamics.CRM.StringAttributeMetadata'; SchemaName="${p}_$n"; MaxLength=$max; FormatName=@{Value=$fmt}; DisplayName=(New-Label $l); RequiredLevel=@{Value='None'} } }
function Memo($n,$l) { @{ '@odata.type'='Microsoft.Dynamics.CRM.MemoAttributeMetadata'; SchemaName="${p}_$n"; MaxLength=10000; Format='TextArea'; DisplayName=(New-Label $l); RequiredLevel=@{Value='None'} } }
function Pick($n,$l,$opts,$default) {
    $o = @(); $v = 100000000
    foreach ($x in $opts) { $o += @{ Value=$v; Label=(New-Label $x) }; $v++ }
    @{ '@odata.type'='Microsoft.Dynamics.CRM.PicklistAttributeMetadata'; SchemaName="${p}_$n"; DisplayName=(New-Label $l); RequiredLevel=@{Value='None'}
       DefaultFormValue=$default; OptionSet=@{ '@odata.type'='Microsoft.Dynamics.CRM.OptionSetMetadata'; IsGlobal=$false; OptionSetType='Picklist'; Options=$o } }
}

Write-Host 'Columns:'
Add-Col (Memo 'description' 'Description')
Add-Col (Pick 'status' 'Status' @('New','In Progress','Completed') 100000000)
Add-Col (Pick 'priority' 'Priority' @('Low','Medium','High') 100000001)
Add-Col (Pick 'category' 'Category' @('Process','Product','Technology','Customer Experience','Other') 100000004)
Add-Col (Str 'submittedby' 'Submitted By' 200)
Add-Col (Str 'submitteremail' 'Submitter Email' 200 'Email')
Add-Col (Memo 'businessvalue' 'Business Value')
Add-Col (Memo 'statusnotes' 'Status Notes')
Add-Col (Str 'source' 'Source' 100)
Add-Col (Str 'conversationid' 'Conversation Id' 100)
Add-Col @{ '@odata.type'='Microsoft.Dynamics.CRM.DateTimeAttributeMetadata'; SchemaName="${p}_completedon"; Format='DateOnly'; DisplayName=(New-Label 'Completed On'); RequiredLevel=@{Value='None'} }

Invoke-Dv $cfg $token POST 'PublishAllXml' @{} | Out-Null
Write-Host "Done. Table: $table  Solution: $SolutionName  (status 100000000=New, 100000001=In Progress, 100000002=Completed)"
