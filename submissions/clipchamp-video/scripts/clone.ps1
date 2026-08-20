$src = "$env:LOCALAPPDATA\Microsoft\Edge\User Data"
$dst = "$env:USERPROFILE\.copilot\video-work\edge-tenant"

# Close the REAL Edge (never the MCP/automation browser) so its profile files unlock for
# copying. Unrelated to the recording workflow's own Node processes, so node.exe is left alone.
Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
  Where-Object { $_.CommandLine -notlike '*m-playwright-profiles*' -and $_.CommandLine -notlike '*ms-playwright*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 3

Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item "$src\Local State" "$dst\Local State" -Force
robocopy "$src\Profile 1" "$dst\Profile 1" /E /NFL /NDL /NJH /NJS /R:0 /W:0 /XJ `
  /XD "Service Worker" "Cache" "Code Cache" "GPUCache" "Shared Dictionary" "DawnGraphiteCache" "DawnWebGPUCache" "EdgeCoupons" "Crashpad" "optimization_guide_model_store" | Out-Null

# Patch Preferences with REGEX ONLY. Round-tripping through ConvertFrom-Json/ConvertTo-Json
# reorders and retypes the file and breaks the profile's signed-in identity (api.bap 404).
$pf = Join-Path $dst 'Profile 1\Preferences'
$c = Get-Content $pf -Raw -Encoding UTF8
$c = $c -replace '"exit_type":"[^"]*"', '"exit_type":"Normal"' -replace '"exited_cleanly":false', '"exited_cleanly":true'
[System.IO.File]::WriteAllText($pf, $c, (New-Object System.Text.UTF8Encoding($false)))

"cloned: {0:N0} MB" -f ((Get-ChildItem $dst -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)
Write-Host ("cookies: " + (Test-Path "$dst\Profile 1\Network\Cookies"))
