#!/bin/sh
# Act 5 of the gray-box demo: ask the app to do something. Hooks are
# functions the app registered by name; a test calls them with
# `mobium hook` and gets back what they returned. Recorded with the same
# evidence as acts 1 to 4: a screen recording, a trace, screenshots of what
# the app showed, and a transcript of every command with what it printed.
#
#   scripts/hooks.sh <serial|udid> [out-dir]
#
# MOBIUM names the mobium binary (default: mobium on PATH). The device needs
# MobiumApp with hooks: mobiumdev/mobium-app#20 or later.
#
#   1. screen      the app says which screen is showing
#   2. raiseToast  "Toast raised by test script" — the app draws it at the
#                  top; on Android it also raises a system toast
#   3. raiseToast  a message no keyboard layout holds whole
#   4. signIn      the welcome screen, without the login form
#   5. a typo      refused, naming the hooks the app did register
#
# Everything recorded is MobiumApp's own screen, on a real phone too.
set -u
DEV="${1:-}"
if [ -z "$DEV" ]; then echo "usage: $0 <serial|udid> [out-dir]" >&2; exit 2; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MOBIUM="${MOBIUM:-mobium}"
APP=dev.mobium.mobiumapp
case "$DEV" in
  emulator-*) KIND=android-emulator VIRTUAL=1 ;;
  *-*-*-*-*) KIND=ios-simulator VIRTUAL=1 ;;
  ????????-????????????????) KIND=iphone VIRTUAL= ;;
  *) KIND=android-phone VIRTUAL= ;;
esac
OUT="${2:-$ROOT/evidence/$(date +%Y-%m-%d)-$KIND-hooks}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
T="$OUT/transcript.md"
: > "$T"
M="$MOBIUM --device $DEV"

# run prints a command and what it printed, to the screen and the
# transcript, and keeps its output in $out and its status in $rc.
run() {
  out=$($M "$@" 2>&1)
  rc=$?
  shown="mobium"
  for a in "$@"; do
    case "$a" in *" "*) shown="$shown \"$a\"" ;; *) shown="$shown $a" ;; esac
  done
  printf '$ %s\n%s\n\n' "$shown" "$out"
  printf '```\n$ %s\n%s\n```\n\n' "$shown" "$out" >> "$T"
  return $rc
}
note() { printf '%s\n\n' "$1"; printf '%s\n\n' "$1" >> "$T"; }
ms() { python3 -c 'import time; print(int(time.time()*1000))'; }
fail() { echo "FAIL: $*" >&2; exit 1; }

{
  printf '# Hooks on %s\n\n' "$KIND"
  printf 'Recorded %s with `%s`, on %s.\n\n' "$(date '+%Y-%m-%d %H:%M %Z')" "$($MOBIUM --version 2>/dev/null | head -1)" "$KIND"
  printf '## Act 5 — ask the app to do something\n\n'
} >> "$T"
note "MobiumApp registers three hooks with its gray-box library: raiseToast, screen and signIn. Each call below is held to what the app then shows."

$M terminate "$APP" >/dev/null 2>&1
run launch --gray-box "$APP" || fail "launch: $out"

VIDEO=1
if ! $M record start >/dev/null 2>&1; then
  VIDEO=
  note "(This device cannot record its screen through Mobium; the act has a trace and screenshots.)"
fi
# The trace keeps every call and its result, without screenshots or maps:
# the recording shows the screen.
$M trace start --name "Act 5: hooks" --no-screenshots --no-maps >/dev/null
sleep 1

run hook screen || fail "hook screen: $out"
SCREEN="$out"
sleep 1

t0=$(ms)
run hook raiseToast "Toast raised by test script" || fail "hook raiseToast: $out"
TOAST_MS=$(( $(ms) - t0 ))
TOAST="$out"
run text testid=hookToast || fail "no toast on screen: $out"
SHOWN="$out"
[ "$SHOWN" = "Toast raised by test script" ] || fail "the toast says \"$SHOWN\""
$M screenshot -o "$OUT/toast.png" >/dev/null
sleep 3

run hook raiseToast "Привет, café — 5 ✓" || fail "hook raiseToast: $out"
run text testid=hookToast || fail "no toast on screen: $out"
UNICODE="$out"
[ "$UNICODE" = "Привет, café — 5 ✓" ] || fail "the toast says \"$UNICODE\""
$M screenshot -o "$OUT/toast-unicode.png" >/dev/null
sleep 3

run hook signIn mobium || fail "hook signIn: $out"
SIGNIN="$out"
run text testid=welcomeText || fail "no welcome screen: $out"
WELCOME="$out"
run hook screen
AFTER="$out"
$M screenshot -o "$OUT/signed-in.png" >/dev/null
sleep 2

if run hook raiseTost "typo"; then fail "a hook the app never registered was answered: $out"; fi
TYPO="$out"
sleep 1

$M trace stop -o "$OUT/act5.zip" >/dev/null
if [ -n "$VIDEO" ]; then $M record stop -o "$OUT/act5.mp4" >/dev/null 2>&1; fi
$M terminate "$APP" >/dev/null 2>&1
note "The toast said **$SHOWN**, then **$UNICODE**; the welcome screen said **$WELCOME**; the typo was refused."

python3 - "$OUT/summary.json" <<EOF
import json, sys
json.dump({
  "device": "$KIND",
  "act5": {
    "screen": """$SCREEN""",
    "raise_toast": """$TOAST""", "raise_toast_ms": $TOAST_MS, "toast_shown": """$SHOWN""",
    "toast_unicode": """$UNICODE""",
    "sign_in": """$SIGNIN""", "welcome": """$WELCOME""", "screen_after": """$AFTER""",
    "typo": """$TYPO""",
  },
  "video": bool("$VIDEO"),
}, open(sys.argv[1], "w"), indent=2, ensure_ascii=False)
EOF
# A real phone's UDID or serial names the phone: the trace records it with
# every call, so it becomes the device's kind.
if [ -n "$VIRTUAL" ]; then
  python3 "$ROOT/scripts/scrub.py" "$OUT" >/dev/null
else
  python3 "$ROOT/scripts/scrub.py" "$OUT" --redact "$DEV=$KIND" >/dev/null
fi
echo "evidence: $OUT"
ls "$OUT"
