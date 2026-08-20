$dst = "$env:USERPROFILE\.copilot\video-work\edge-tenant"
$pf  = Join-Path $dst 'Profile 1\Preferences'

Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='node.exe'" |
  Where-Object { $_.CommandLine -notlike '*m-playwright-profiles*' -and $_.CommandLine -notlike '*ms-playwright*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
Get-ChildItem $dst -Filter 'Singleton*' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# REGEX ONLY - never ConvertFrom-Json/ConvertTo-Json this file (breaks signed-in state).
$c = Get-Content $pf -Raw -Encoding UTF8
$c = $c -replace '"exit_type":"[^"]*"', '"exit_type":"Normal"' -replace '"exited_cleanly":false', '"exited_cleanly":true'
[System.IO.File]::WriteAllText($pf, $c, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "profile prepped"
