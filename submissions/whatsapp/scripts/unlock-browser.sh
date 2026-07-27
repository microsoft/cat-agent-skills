#!/usr/bin/env bash
set -uo pipefail

# macOS/Linux helper for WhatsApp automations.
#
# Default (no args): take a run lock so two runs never share the browser profile.
#   The lock is a directory (mkdir is atomic). The winner writes an `owner` file
#   (PID + timestamp) immediately. On contention:
#     - owner empty/non-numeric and the dir is fresh -> another run is
#       mid-acquire, so back off (grace window) rather than stomp it.
#     - owner alive and younger than the 30-min backstop -> back off.
#     - otherwise stale: rm the dir and re-gate on mkdir.
#   Then COMMIT-VERIFY: after writing owner, settle briefly and re-read owner; if
#   a concurrent reclaimer overwrote it, back off. Prints RUN_ALREADY_ACTIVE and
#   exits 0 on any back-off. A live run past the 30-min backstop is overridden.
#   A stuck browser is cleared ONLY when a stale lock was recovered, so a normal
#   run reuses the open WhatsApp session with no close/reopen flicker.
#
# `--clear`: kill a stuck Playwright browser WITHOUT touching the lock. The
#   caller (already holding the lock) uses this mid-run when WhatsApp will not
#   load and a reload did not help - the "close it because we saw a problem" path.
#
# Only browser binaries under the Playwright install are targeted, never the Node
# driver or the user's normal windows.
#
# Release is the caller's job at end of run, owner-checked:
#   lock=/tmp/scout-whatsapp.lock
#   [ "$(head -n1 "$lock/owner" 2>/dev/null)" = "$$" ] && rm -rf "$lock"

lock=/tmp/scout-whatsapp.lock
owner="$lock/owner"
backstop=1800   # 30 minutes
grace=60        # seconds to respect a lock whose owner file is not written yet
reclaimed=0     # set to 1 when we overrode a stale lock

kill_browser() {
  pkill -f 'ms-playwright/.*(chromium|chrome|headless_shell|msedge)' 2>/dev/null || true
  sleep 3
}

# On-demand clear (caller already holds the lock).
if [ "${1:-}" = "--clear" ]; then
  kill_browser
  echo "Cleared a stuck browser (on request)."
  exit 0
fi

write_owner() { printf '%s\n%s\n' "$$" "$(date -u +%FT%TZ)" > "$owner"; }

take_lock() {
  if mkdir "$lock" 2>/dev/null; then
    write_owner
  else
    local opid now mtime age
    opid=$(head -n1 "$owner" 2>/dev/null || echo "")
    now=$(date +%s)
    mtime=$(stat -c %Y "$lock" 2>/dev/null || stat -f %m "$lock" 2>/dev/null || echo "$now")
    age=$(( now - mtime ))
    if ! printf '%s' "$opid" | grep -qE '^[0-9]+$'; then
      [ "$age" -lt "$grace" ] && return 1        # empty/non-numeric: mid-acquire
    else
      kill -0 "$opid" 2>/dev/null && [ "$age" -lt "$backstop" ] && return 1
    fi
    rm -rf "$lock"
    mkdir "$lock" 2>/dev/null || return 1        # lost the re-gate: back off
    write_owner
    reclaimed=1
  fi
  # Commit-verify: if a concurrent reclaimer stomped us, back off.
  sleep 0.3
  [ "$(head -n1 "$owner" 2>/dev/null)" = "$$" ] || return 1
  return 0
}

if ! take_lock; then echo "RUN_ALREADY_ACTIVE"; exit 0; fi

if [ "$reclaimed" -eq 1 ]; then
  kill_browser
  echo "Recovered a stale run: cleared a leftover browser."
else
  echo "Lock acquired; reusing the existing browser session if present."
fi
