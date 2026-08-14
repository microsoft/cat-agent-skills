#!/bin/sh
# Launcher for cs-agent-test on macOS and Linux.
# Keeps callers from having to type "node scripts/cs-agent-test.cjs" every time.

if ! command -v node >/dev/null 2>&1; then
  echo ""
  echo "Node.js was not found on PATH."
  echo ""
  echo "This tool needs Node.js 22 or later. Install it from https://nodejs.org"
  echo "then open a new terminal and try again."
  echo ""
  exit 1
fi

DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
exec node "$DIR/cs-agent-test.cjs" "$@"
