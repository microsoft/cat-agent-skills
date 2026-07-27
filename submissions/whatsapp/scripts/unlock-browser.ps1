param([switch]$Clear, [string]$Release)

# unlock-browser.ps1
# Windows helper for WhatsApp automations.
#
# Default (no args): take a run lock so two runs never share the browser profile.
#   The lock is a directory (creation is atomic). IMPORTANT: in Scout each command
#   is a short-lived process, so the run is NOT a long-lived PID we can probe. The
#   lock is therefore TIME-BOXED, not PID-based: a lock younger than the TTL is an
#   active run and we back off; a lock older than the TTL is assumed finished or
#   crashed and is overridden. Ownership for release is a random TOKEN (printed as
#   LOCK_TOKEN=...), not a PID. Prints RUN_ALREADY_ACTIVE and exits 0 when it backs
#   off. Well-behaved runs release the lock at the end, so the TTL only matters
#   after a crash. Keep a run shorter than the TTL or it may be overridden.
#   A stuck browser is cleared ONLY when a stale lock was recovered, so a normal
#   run reuses the open WhatsApp session with no close/reopen flicker.
#
# -Release <token>: remove the lock only if it still holds <token> (the value
#   printed as LOCK_TOKEN at acquire). Call this at end of run.
#
# -Clear: kill a stuck Playwright browser WITHOUT touching the lock. The caller
#   (already holding the lock) uses this mid-run when WhatsApp will not load.
#
# Only browser binaries launched from the Playwright install are targeted (bundled
# Chromium or the msedge channel), never the Node driver or the user's normal windows.

$lockDir = Join-Path $env:TEMP 'scout-whatsapp.lock'
$ownerFile = Join-Path $lockDir 'owner'
$ttlSec = 600   # 10 minutes: a lock older than this is assumed finished/crashed

function Clear-Browser {
  Get-CimInstance Win32_Process `
  | Where-Object {
      $_.CommandLine -like '*ms-playwright*' -and
      ($_.Name -match '^(msedge|chrome|chromium|headless_shell)')
    } `
  | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 3
}

# -Clear: on-demand browser kill (caller already holds the lock).
if ($Clear) {
  Clear-Browser
  Write-Output 'Cleared a stuck browser (on request).'
  exit 0
}

# -Release <token>: token-checked release.
if ($Release) {
  $held = if (Test-Path $ownerFile) { (Get-Content $ownerFile -TotalCount 1) } else { '' }
  if ($Release -eq $held) {
    Remove-Item -LiteralPath $lockDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Output 'Lock released.'
  } else {
    Write-Output 'Not the lock owner; left it alone.'
  }
  exit 0
}

$token = [guid]::NewGuid().ToString('N')
function Write-Owner { Set-Content -Path $ownerFile -Value "$token`n$(Get-Date -Format o)" }

function Take-Lock {
  try {
    New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null
    Write-Owner
    return $true
  } catch {
    $item = Get-Item $lockDir -ErrorAction SilentlyContinue
    $ageSec = if ($item) { ((Get-Date) - $item.LastWriteTime).TotalSeconds } else { 0 }
    if ($ageSec -lt $ttlSec) { return $false }   # a recent run holds it: back off
    Remove-Item -LiteralPath $lockDir -Recurse -Force -ErrorAction SilentlyContinue
    try { New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null }
    catch { return $false }                       # lost the re-gate: back off
    Write-Owner
    $script:Reclaimed = $true
    return $true
  }
}

$script:Reclaimed = $false
if (-not (Take-Lock)) { Write-Output 'RUN_ALREADY_ACTIVE'; exit 0 }

# Commit-verify: if a concurrent reclaimer stomped us, back off.
Start-Sleep -Milliseconds 300
$current = if (Test-Path $ownerFile) { (Get-Content $ownerFile -TotalCount 1) } else { '' }
if ($current -ne $token) { Write-Output 'RUN_ALREADY_ACTIVE'; exit 0 }

Write-Output "LOCK_TOKEN=$token"   # pass this to -Release <token> at end of run

if ($script:Reclaimed) {
  Clear-Browser
  Write-Output 'Recovered a stale run: cleared a leftover browser.'
} else {
  Write-Output 'Lock acquired; reusing the existing browser session if present.'
}
