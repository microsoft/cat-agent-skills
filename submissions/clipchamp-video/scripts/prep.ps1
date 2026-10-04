$dst = "$env:USERPROFILE\.copilot\video-work\edge-tenant"
$pf  = Join-Path $dst 'Profile 1\Preferences'

# Only stop OUR OWN processes: the Edge instance running on the cloned "edge-tenant"
# profile (never the MCP browser or any other Edge window), and any node.exe process
# that's actually running one of this skill's scripts (never unrelated Node apps/dev
# servers on the machine).
Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
  Where-Object { $_.CommandLine -like '*edge-tenant*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -match 'recorder\.js|verify\.js|findagent\.js|diag\.js|dual-capture\.js' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
Get-ChildItem $dst -Filter 'Singleton*' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# REGEX ONLY - never ConvertFrom-Json/ConvertTo-Json this file (breaks signed-in state).
$c = Get-Content $pf -Raw -Encoding UTF8
$c = $c -replace '"exit_type":"[^"]*"', '"exit_type":"Normal"' -replace '"exited_cleanly":false', '"exited_cleanly":true'
[System.IO.File]::WriteAllText($pf, $c, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "profile prepped"
