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
#   Exit codes: 0 = lock acquired, or RUN_ALREADY_ACTIVE (another run holds it);
#   2 = the lock could not be evaluated at all (no permission on the temp
#   directory, read-only or full filesystem, ...), with the cause on stderr as
#   LOCK_ERROR. Contention and failure are never conflated: a caller that sees
#   exit 2 must report the error, not back off as if a run were active.
#   A stuck browser is cleared ONLY when a stale lock was recovered, so a normal
#   run reuses the open WhatsApp session with no close/reopen flicker.
#
# `--release <token>`: remove the lock only if it still holds <token> (the value
#   printed as LOCK_TOKEN at acquire). Call this at end of run.
#
# `--clear`: kill a stuck Playwright browser WITHOUT touching the lock. The caller
#   (already holding the lock) uses this mid-run when WhatsApp will not load.
#
# Only the browser Playwright is driving is targeted - identified by its profile
# directory, since with the msedge channel the executable is the user's own Edge -
# never the Node driver or the user's normal windows. Note this matches ANY
# browser on an ms-playwright profile for this user, not only the one holding
# WhatsApp, so a concurrent Playwright session is closed as well.
#
# The lock lives under $TMPDIR (falling back to /tmp) and carries the uid in its
# name, so two users on the same machine do not contend over one lock, and it is
# created mode 0700: with a default umask the owner file would be world-readable,
# and the release token in it is the only thing stopping another local user from
# releasing this run's lock (the sticky bit on /tmp stops them deleting it, so
# the token is what protects it).

umask 077        # lock dir 0700, owner file 0600 - see the note above. Done with
                 # umask rather than `mkdir -m`, which on some platforms creates
                 # the directory and *then* fails applying the mode, so a failed
                 # chmod would be misread as "the lock already exists".

lock="${TMPDIR:-/tmp}/scout-whatsapp-$(id -u).lock"
owner="$lock/owner"
ttl=600         # 10 minutes: a lock older than this is assumed finished/crashed
reclaimed=0

lock_error() { echo "LOCK_ERROR: $1" >&2; }

kill_browser() {
  # Match the PROFILE, not the executable. With the msedge channel Playwright
  # launches the system Edge, which does not live under the Playwright install,
  # so keying on the binary's path silently fails to kill it - and this helper
  # would report a cleared browser having killed nothing. The --user-data-dir
  # flag pointing under ms-playwright is what actually identifies our browser.
  # It also keeps bystanders out of range: a process merely holding such a path
  # as an argument (`tail -f .../ms-playwright/.../chrome_debug.log`, an editor
  # with that file open) does not carry the flag. -u limits the sweep to our own
  # processes, and the Node driver is skipped by name so it is never a target.
  local pid
  # ms-playwright must be a PATH COMPONENT of the profile, and the flag must be
  # the real `--user-data-dir=`, not a loose substring: `.*` would span spaces
  # and match a browser on an unrelated profile that merely mentions
  # ms-playwright later on its command line, which would close the user's own
  # windows. A profile named "...ms-playwright-notes" is not a target either.
  for pid in $(pgrep -u "$(id -u)" -f -- '--user-data-dir=[^[:space:]]*[/\]ms-playwright[/\]' 2>/dev/null); do
    # Anything that is not the driver gets terminated, including the case where
    # the name could not be read - the pid already matched the profile flag, and
    # skipping it would mean recovery quietly leaving the browser holding the
    # profile, which is the failure this whole path exists to fix. A pid that
    # has already exited just makes kill a no-op.
    case "$(ps -o comm= -p "$pid" 2>/dev/null)" in
      *node*|*Node*) continue ;;
      *) kill "$pid" 2>/dev/null || true ;;
    esac
  done
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
    # Do not announce a release that did not happen: a caller told "Lock
    # released." stops worrying about it, while the next run is blocked until
    # the TTL with no idea why.
    if rm -rf "$lock" 2>/dev/null && [ ! -d "$lock" ]; then
      echo "Lock released."
    else
      lock_error "owned this lock but could not remove $lock; it stays until the TTL expires"
      exit 2
    fi
  else
    echo "Not the lock owner; left it alone."
  fi
  exit 0
fi

# $RANDOM is not a CSPRNG, and deliberately so: this token is not a security
# boundary. It exists so a run cannot release a lock it does not own by mistake,
# and it is unguessable enough for that. Anyone who can read it can already read
# the lock directory.
token="$$-$(date +%s)-${RANDOM}${RANDOM}"
write_owner() { printf '%s\n%s\n' "$token" "$(date -u +%FT%TZ)" > "$owner"; }

# 0 = acquired, 1 = another run holds it, 2 = unexpected failure (cause on stderr).
take_lock() {
  local now mtime age
  if mkdir "$lock" 2>/dev/null; then
    write_owner || { rm -rf "$lock"; lock_error "cannot write $owner (permissions or disk full)"; return 2; }
  else
    # mkdir failed. That is contention ONLY if the lock directory really is
    # there; every other cause (no permission on /tmp, read-only or full
    # filesystem, a stray file at that path) is a real error and must not be
    # reported as an active run.
    [ -d "$lock" ] || { lock_error "cannot create $lock (permissions, read-only filesystem, or a non-directory exists at that path)"; return 2; }
    now=$(date +%s)
    mtime=$(stat -c %Y "$lock" 2>/dev/null || stat -f %m "$lock" 2>/dev/null) \
      || { lock_error "cannot stat $lock"; return 2; }
    age=$(( now - mtime ))
    [ "$age" -lt "$ttl" ] && return 1            # a recent run holds it: back off
    # A removal that fails is an environment fault, not contention. Left
    # unchecked it surfaces as the next mkdir failing with the directory still
    # present, which reads exactly like another run holding the lock - the very
    # conflation this function exists to avoid.
    rm -rf "$lock" 2>/dev/null \
      || { lock_error "cannot remove the stale lock at $lock (read-only filesystem or permissions)"; return 2; }
    if ! mkdir "$lock" 2>/dev/null; then
      # We did remove it, so a directory here now is a run that took it in
      # between - genuine contention.
      [ -d "$lock" ] && return 1
      lock_error "cannot recreate $lock after clearing a stale lock"
      return 2
    fi
    write_owner || { rm -rf "$lock"; lock_error "cannot write $owner (permissions or disk full)"; return 2; }
    reclaimed=1
  fi
  # Commit-verify: if a concurrent reclaimer stomped us, back off.
  sleep 0.3
  [ "$(head -n1 "$owner" 2>/dev/null)" = "$token" ] || return 1
  return 0
}

take_lock; rc=$?
case "$rc" in
  0) ;;
  1) echo "RUN_ALREADY_ACTIVE"; exit 0 ;;
  *) exit 2 ;;                                   # cause already on stderr as LOCK_ERROR
esac

echo "LOCK_TOKEN=$token"   # pass this to `--release <token>` at end of run

if [ "$reclaimed" -eq 1 ]; then
  kill_browser
  echo "Recovered a stale run: cleared a leftover browser."
else
  echo "Lock acquired; reusing the existing browser session if present."
fi
