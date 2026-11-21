#!/usr/bin/env bash
# Headless Chrome screenshot with a throw-away profile and a hard time limit.
#   scripts/shot.sh <url> <out.png> [width] [height] [budget_ms]
set -euo pipefail
url=$1; out=$2; w=${3:-1400}; h=${4:-2000}; budget=${5:-9000}
prof=$(mktemp -d "${TMPDIR:-/tmp}/rh-chrome.XXXXXX")
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --no-first-run --no-default-browser-check --user-data-dir="$prof" --window-size="$w,$h" \
  --virtual-time-budget="$budget" --screenshot="$out" "$url" >/dev/null 2>&1 &
pid=$!
for _ in $(seq 1 90); do sleep 1; kill -0 "$pid" 2>/dev/null || break; done
kill "$pid" 2>/dev/null || true
rm -rf "$prof"
test -s "$out" && echo "screenshot: $out"
