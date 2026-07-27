#!/usr/bin/env bash
set -uo pipefail

# macOS/Linux helper for WhatsApp automations.
#
# Default (no args): take a run lock so two runs never share the browser profile.
#   The lock is a directory (mkdir is atomic). IMPORTANT: in Scout each command is
#   a short-lived process, so the run is NOT a long-lived PID we can probe. The
#   lock is therefore TIME-BOXED, not PID-based: a lock younger than the TTL is
#   treated as an active run and we back off; a lock older than the TTL is assumed
#   finished or crashed and is overridden. Ownership for release is a random TOKEN
#   (printed as LOCK_TOKEN=...), not a PID. Prints RUN_ALREADY_ACTIVE and exits 0
#   when it backs off. Well-behaved runs release the lock at the end (see below),
#   so the TTL only matters after a crash. Keep a run shorter than the TTL, or it
#   may be overridden by the next run.
#   A stuck browser is cleared ONLY when a stale lock was recovered, so a normal
#   run reuses the open WhatsApp session with no close/reopen flicker.
#
# `--release <token>`: remove the lock only if it still holds <token> (the value
#   printed as LOCK_TOKEN at acquire). Call this at end of run.
#
# `--clear`: kill a stuck Playwright browser WITHOUT touching the lock. The caller
#   (already holding the lock) uses this mid-run when WhatsApp will not load.
#
# Only browser binaries under the Playwright install are targeted, never the Node
# driver or the user's normal windows.

lock=/tmp/scout-whatsapp.lock
owner="$lock/owner"
ttl=600         # 10 minutes: a lock older than this is assumed finished/crashed
reclaimed=0

kill_browser() {
  pkill -f 'ms-playwright/.*(chromium|chrome|headless_shell|msedge)' 2>/dev/null || true
  sleep 3
}

# --clear: on-demand browser kill (caller already holds the lock).
if [ "${1:-}" = "--clear" ]; then
  kill_browser
  echo "Cleared a stuck browser (on request)."
  exit 0
fi

# --release <token>: token-checked release.
if [ "${1:-}" = "--release" ]; then
  tok="${2:-}"
  if [ -n "$tok" ] && [ "$(head -n1 "$owner" 2>/dev/null)" = "$tok" ]; then
    rm -rf "$lock"
    echo "Lock released."
  else
    echo "Not the lock owner; left it alone."
  fi
  exit 0
fi

token="$$-$(date +%s)-${RANDOM}${RANDOM}"
write_owner() { printf '%s\n%s\n' "$token" "$(date -u +%FT%TZ)" > "$owner"; }

take_lock() {
  if mkdir "$lock" 2>/dev/null; then
    write_owner
  else
    local now mtime age
    now=$(date +%s)
    mtime=$(stat -c %Y "$lock" 2>/dev/null || stat -f %m "$lock" 2>/dev/null || echo "$now")
    age=$(( now - mtime ))
    [ "$age" -lt "$ttl" ] && return 1            # a recent run holds it: back off
    rm -rf "$lock"
    mkdir "$lock" 2>/dev/null || return 1        # lost the re-gate: back off
    write_owner
    reclaimed=1
  fi
  # Commit-verify: if a concurrent reclaimer stomped us, back off.
  sleep 0.3
  [ "$(head -n1 "$owner" 2>/dev/null)" = "$token" ] || return 1
  return 0
}

if ! take_lock; then echo "RUN_ALREADY_ACTIVE"; exit 0; fi

echo "LOCK_TOKEN=$token"   # pass this to `--release <token>` at end of run

if [ "$reclaimed" -eq 1 ]; then
  kill_browser
  echo "Recovered a stale run: cleared a leftover browser."
else
  echo "Lock acquired; reusing the existing browser session if present."
fi
