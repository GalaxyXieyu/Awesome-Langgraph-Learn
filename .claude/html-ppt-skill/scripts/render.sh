#!/usr/bin/env bash
# html-ppt :: render.sh — headless Chrome screenshot(s)
#
# Usage:
#   render.sh <html-file>                     # one PNG, slide 1
#   render.sh <html-file> <N>                 # N PNGs, slides 1..N, via #/k
#   render.sh <html-file> all                 # autodetect .slide count
#   render.sh <html-file> <N> <out-dir>       # custom output dir
#
# Chrome discovery (in order):
#   1. $CHROME env variable
#   2. /Applications/Google Chrome.app
#   3. mdfind (Spotlight) for any Google Chrome.app
#   4. Playwright cached Chromium

set -euo pipefail

# ─── Chrome auto-discovery ─────────────────────────────────────────
find_chrome() {
  # 1. User override
  if [[ -n "${CHROME:-}" && -x "$CHROME" ]]; then
    echo "$CHROME"
    return 0
  fi

  # 2. Standard path
  local std="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  if [[ -x "$std" ]]; then
    echo "$std"
    return 0
  fi

  # 3. mdfind (Spotlight) — catches "Google Chrome 2.app" etc.
  local found
  found="$(mdfind 'kMDItemCFBundleIdentifier == "com.google.Chrome"' 2>/dev/null | head -1)"
  if [[ -n "$found" ]]; then
    local bin="$found/Contents/MacOS/Google Chrome"
    if [[ -x "$bin" ]]; then
      echo "$bin"
      return 0
    fi
  fi

  # 4. Playwright cached Chromium fallback
  local pw_chrome
  pw_chrome="$(find ~/Library/Caches/ms-playwright -maxdepth 4 -name 'Chromium' -type f 2>/dev/null | head -1)"
  if [[ -n "$pw_chrome" && -x "$pw_chrome" ]]; then
    echo "$pw_chrome"
    return 0
  fi

  # 5. Linux common paths
  for p in /usr/bin/google-chrome /usr/bin/chromium /usr/bin/chromium-browser \
           /usr/local/bin/google-chrome /snap/bin/chromium; do
    if [[ -x "$p" ]]; then
      echo "$p"
      return 0
    fi
  done

  return 1
}

CHROME_BIN="$(find_chrome)" || {
  echo "error: Chrome not found." >&2
  echo "  Tried: CHROME env, /Applications/Google Chrome.app, mdfind, Playwright cache, Linux paths" >&2
  echo "  Set CHROME=/path/to/chrome to override." >&2
  exit 1
}

# ─── Args ──────────────────────────────────────────────────────────
FILE="${1:-}"
if [[ -z "$FILE" ]]; then
  echo "usage: render.sh <html> [N|all] [out-dir]" >&2
  exit 1
fi
if [[ ! -f "$FILE" ]]; then
  echo "error: $FILE not found" >&2
  exit 1
fi

COUNT="${2:-1}"
OUT="${3:-}"

ABS="$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")"
STEM="$(basename "${FILE%.*}")"

if [[ "$COUNT" == "all" ]]; then
  COUNT="$(grep -cE 'class="[^"]*slide[^"]*"' "$FILE" || true)"
  [[ -z "$COUNT" || "$COUNT" -lt 1 ]] && COUNT=1
fi

if [[ -z "$OUT" ]]; then
  if [[ "$COUNT" -gt 1 ]]; then
    OUT="$(dirname "$FILE")/${STEM}-png"
    mkdir -p "$OUT"
  fi
fi

# ─── Render ────────────────────────────────────────────────────────
render_one() {
  local url="$1" target="$2"
  "$CHROME_BIN" \
    --headless=new \
    --disable-gpu \
    --hide-scrollbars \
    --no-sandbox \
    --virtual-time-budget=4000 \
    --window-size=1920,1080 \
    --screenshot="$target" \
    "$url" >/dev/null 2>&1
  echo "  ✔ $target"
}

if [[ "$COUNT" == "1" ]]; then
  OUT_FILE="${OUT:-$(dirname "$FILE")/${STEM}.png}"
  render_one "file://$ABS" "$OUT_FILE"
else
  for i in $(seq 1 "$COUNT"); do
    render_one "file://$ABS#/$i" "$OUT/${STEM}_$(printf '%02d' "$i").png"
  done
fi

echo "done: rendered $COUNT slide(s) from $FILE"
