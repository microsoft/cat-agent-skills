param([switch]$Clear)

# unlock-browser.ps1
# Windows helper for WhatsApp automations.
#
# Default (no args): take a run lock so two runs never share the browser profile.
#   The lock is a directory (creation is atomic). The winner writes an `owner`
#   file (PID + timestamp) immediately. On contention:
#     - owner empty/non-numeric and the dir is fresh -> another run is
#       mid-acquire, so back off (grace window) rather than stomp it.
#     - owner alive and younger than the 30-minute backstop -> back off.
#     - otherwise stale: remove the dir and re-gate on New-Item.
#   Then COMMIT-VERIFY: after writing owner, settle briefly and re-read owner; if
#   a concurrent reclaimer overwrote it, back off. Prints RUN_ALREADY_ACTIVE and
#   exits 0 on any back-off. A live run past the 30-minute backstop is overridden.
#   A stuck browser is cleared ONLY when a stale lock was recovered, so a normal
#   run reuses the open WhatsApp session with no close/reopen flicker.
#
# -Clear: kill a stuck Playwright browser WITHOUT touching the lock. The caller
#   (already holding the lock) uses this mid-run when WhatsApp will not load and a
#   reload did not help - the "close it because we saw a problem" path.
#
# Only browser binaries launched from the Playwright install are targeted (bundled
# Chromium or the msedge channel), never the Node driver or the user's normal windows.
#
# Release is the caller's job at end of run, owner-checked:
#   $o = Join-Path $env:TEMP 'scout-whatsapp.lock\owner'
#   if ((Test-Path $o) -and ((Get-Content $o -First 1) -eq "$PID")) {
#     Remove-Item (Split-Path $o) -Recurse -Force -ErrorAction SilentlyContinue }

$lockDir = Join-Path $env:TEMP 'scout-whatsapp.lock'
$ownerFile = Join-Path $lockDir 'owner'
$backstopSec = 1800   # 30 minutes
$graceSec = 60        # respect a lock whose owner file is not written yet
$script:Reclaimed = $false

function Clear-Browser {
  Get-CimInstance Win32_Process `
  | Where-Object {
      $_.CommandLine -like '*ms-playwright*' -and
      ($_.Name -match '^(msedge|chrome|chromium|headless_shell)')
    } `
  | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 3
}

# On-demand clear (caller already holds the lock).
if ($Clear) {
  Clear-Browser
  Write-Output 'Cleared a stuck browser (on request).'
  exit 0
}

function Write-Owner { Set-Content -Path $ownerFile -Value "$PID`n$(Get-Date -Format o)" }

function Take-Lock {
  try {
    New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null
    Write-Owner
  } catch {
    $ownerPid = if (Test-Path $ownerFile) { (Get-Content $ownerFile -TotalCount 1) } else { '' }
    $item = Get-Item $lockDir -ErrorAction SilentlyContinue
    $ageSec = if ($item) { ((Get-Date) - $item.LastWriteTime).TotalSeconds } else { 0 }
    $pidNum = 0
    if ([int]::TryParse($ownerPid, [ref]$pidNum)) {
      $alive = [bool](Get-Process -Id $pidNum -ErrorAction SilentlyContinue)
      if ($alive -and $ageSec -lt $backstopSec) { return $false }
    } elseif ($ageSec -lt $graceSec) {
      return $false   # empty/non-numeric owner, fresh dir: mid-acquire, back off
    }
    Remove-Item -LiteralPath $lockDir -Recurse -Force -ErrorAction SilentlyContinue
    try { New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null }
    catch { return $false }   # lost the re-gate: back off
    Write-Owner
    $script:Reclaimed = $true
  }
  # Commit-verify: if a concurrent reclaimer stomped us, back off.
  Start-Sleep -Milliseconds 300
  $current = if (Test-Path $ownerFile) { (Get-Content $ownerFile -TotalCount 1) } else { '' }
  if ($current -ne "$PID") { return $false }
  return $true
}

if (-not (Take-Lock)) { Write-Output 'RUN_ALREADY_ACTIVE'; exit 0 }

if ($script:Reclaimed) {
  Clear-Browser
  Write-Output 'Recovered a stale run: cleared a leftover browser.'
} else {
  Write-Output 'Lock acquired; reusing the existing browser session if present.'
}
