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
#   Exit codes: 0 = lock acquired, or RUN_ALREADY_ACTIVE (another run holds it);
#   2 = the lock could not be evaluated at all (TEMP unset or not writable,
#   filesystem error, ...), with the cause on stderr as LOCK_ERROR. Contention and
#   failure are never conflated: a caller that sees exit 2 must report the error,
#   not back off as if a run were active.
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

function Write-LockError($message) { [Console]::Error.WriteLine("LOCK_ERROR: $message") }

if (-not $env:TEMP) {
  Write-LockError 'TEMP is not set, so there is nowhere to place the run lock.'
  exit 2
}

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
function Write-Owner { Set-Content -Path $ownerFile -Value "$token`n$(Get-Date -Format o)" -ErrorAction Stop }

# 'ok' = acquired, 'busy' = another run holds it, 'error' = unexpected failure
# (cause already written to stderr as LOCK_ERROR).
function Take-Lock {
  try {
    New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null
  } catch {
    # Creation failed. That is contention ONLY if the lock directory really is
    # there; every other cause (TEMP not writable, filesystem error, a file at
    # that path) is a real error and must not be reported as an active run.
    if (-not (Test-Path -LiteralPath $lockDir -PathType Container)) {
      Write-LockError "cannot create $lockDir ($($_.Exception.Message))"
      return 'error'
    }
    $item = Get-Item -LiteralPath $lockDir -ErrorAction SilentlyContinue
    if (-not $item) { Write-LockError "cannot stat $lockDir"; return 'error' }
    if (((Get-Date) - $item.LastWriteTime).TotalSeconds -lt $ttlSec) {
      return 'busy'                               # a recent run holds it: back off
    }
    Remove-Item -LiteralPath $lockDir -Recurse -Force -ErrorAction SilentlyContinue
    try { New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null }
    catch {
      if (Test-Path -LiteralPath $lockDir -PathType Container) { return 'busy' }  # another run re-took it
      Write-LockError "cannot recreate $lockDir after clearing a stale lock ($($_.Exception.Message))"
      return 'error'
    }
    $script:Reclaimed = $true
  }
  try { Write-Owner } catch {
    Remove-Item -LiteralPath $lockDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-LockError "cannot write $ownerFile ($($_.Exception.Message))"
    return 'error'
  }
  return 'ok'
}

$script:Reclaimed = $false
switch (Take-Lock) {
  'busy'  { Write-Output 'RUN_ALREADY_ACTIVE'; exit 0 }
  'error' { exit 2 }                              # cause already on stderr as LOCK_ERROR
}

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
