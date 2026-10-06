#!/bin/sh
# The gray-box demo, start to finish, on one device, with the evidence of
# every step: a screen recording and a trace for each act, screenshots of
# what the app said, the test reports, and a transcript of every command
# with what it printed.
#
#   scripts/demo.sh <serial|udid> [out-dir]
#
# MOBIUM names the mobium binary (default: mobium on PATH). The device needs
# MobiumApp installed, built with its gray-box library — any build since the
# Busy Demo's edge controls.
#
# Act 1  a tap right after work the screen does not show, launched the
#        ordinary way: it lands on a row about to be replaced
# Act 2  the same two taps, launched with --gray-box: the second one waits
#        for the app to say it is idle, and says how long
# Act 3  the same as a test, five times each way: flaky.test.json and
#        steady.test.json, which differ by one key
# Act 4  the edges: work that never ends is refused, naming it; on an
#        emulator or a simulator, the app crashing mid-work holds nothing up
#
# On a real phone everything recorded is MobiumApp's own screen; act 4's
# crash, which leaves the app and taps the status bar, runs only on a
# virtual device.
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
OUT="${2:-$ROOT/evidence/$(date +%Y-%m-%d)-$KIND}"
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
say() { printf '\n== %s\n\n' "$1"; printf '## %s\n\n' "$1" >> "$T"; }
note() { printf '%s\n\n' "$1"; printf '%s\n\n' "$1" >> "$T"; }
ms() { python3 -c 'import time; print(int(time.time()*1000))'; }

# open_demo launches MobiumApp — with --gray-box when asked — and opens the
# Busy Demo.
open_demo() {
  $M terminate "$APP" >/dev/null 2>&1
  if [ "$1" = gray ]; then run launch --gray-box "$APP"; else run launch "$APP"; fi
  $M scroll-to "label=Busy Demo" --direction down >/dev/null 2>&1
  # Mobium's own error says why — a locked phone, an app not installed, a
  # build without the Busy Demo — so it is passed on rather than guessed at.
  run tap "label=Busy Demo" || { echo "could not open the Busy Demo: $out" >&2; exit 1; }
}

VIDEO=1
# The recording starts before the trace and stops after it, so the trace
# holds the demo's own steps and nothing of its scaffolding. The trace keeps
# every call and its result but no screenshot or map: those are taken after
# each call, and every call waits for them — two taps took 5.1 s traced on a
# Pixel 8 Pro against 1.4 s without, long enough for the work to finish
# first and the race to vanish. The recording shows the screen instead.
start_capture() {
  if [ -n "$VIDEO" ] && ! $M record start >/dev/null 2>&1; then
    VIDEO=
    note "(This device cannot record its screen through Mobium; the acts have traces and screenshots.)"
  fi
  $M trace start --name "$1" --no-screenshots --no-maps >/dev/null
}
stop_capture() {
  $M trace stop -o "$OUT/$1.zip" >/dev/null
  if [ -n "$VIDEO" ]; then $M record stop -o "$OUT/$1.mp4" >/dev/null 2>&1; fi
}

{
  printf '# Gray box on %s\n\n' "$KIND"
  printf 'Recorded %s with `%s`, on %s.\n\n' "$(date '+%Y-%m-%d %H:%M %Z')" "$($MOBIUM --version 2>/dev/null | head -1)" "$KIND"
} >> "$T"

say "Act 1 — the tap that lands too early"
note "MobiumApp's Busy Demo, launched the ordinary way. Refresh quietly starts 0.4 to 1.6 seconds of work and leaves the old rows up; then Row B is tapped at once. Every Mobium action waits until its target is on screen, still, enabled and uncovered — and Row B is all four the whole time."
open_demo plain
start_capture "Act 1: launched the ordinary way"
ACT1=; ATTEMPTS=0
# The work takes 0.4 to 1.6 s at random, so a tap now and then lands after
# it — the flakiness itself. Up to five tries, and the count is kept.
while [ "$ATTEMPTS" -lt 5 ]; do
  ATTEMPTS=$((ATTEMPTS + 1))
  sleep 2
  run tap testid=busyQuiet
  run tap testid=busyRowB
  run text testid=busyOutcome
  ACT1="$out"
  case "$ACT1" in *": stale") break ;; esac
done
$M screenshot -o "$OUT/act1-after-tap.png" >/dev/null
stop_capture act1
note "Row B said: **$ACT1** (attempt $ATTEMPTS)."

say "Act 2 — ask the app"
note "The same two taps, launched with --gray-box. MobiumApp links Mobium's gray-box library, which says in the device log when the app starts work and when the new rows are on screen."
open_demo gray
start_capture "Act 2: launched with the gray box"
sleep 2
run tap testid=busyQuiet
run tap testid=busyRowB
WAITED=$(echo "$out" | sed -n 's/^gray box: //p')
run text testid=busyOutcome
ACT2="$out"
$M screenshot -o "$OUT/act2-after-tap.png" >/dev/null
stop_capture act2
note "Row B said: **$ACT2**. The tap: *$WAITED*."

say "Act 3 — as a test, five times each way"
note "tests/flaky.test.json and tests/steady.test.json are the same test; the second adds \"grayBox\": true."
CFG="$OUT/mobium.config.json"
printf '{\n  "testDir": "%s/tests",\n  "projects": [{"name": "%s", "device": "%s"}]\n}\n' "$ROOT" "$KIND" "$DEV" > "$CFG"
cd "$ROOT"
run test --config "$CFG" tests/flaky.test.json --reporter list,html --output "$OUT/report-flaky"
FLAKY=$(echo "$out" | grep -E '^[0-9]+ passed' | tail -1)
run test --config "$CFG" tests/steady.test.json --reporter list,html --trace on --output "$OUT/report-steady"
STEADY=$(echo "$out" | grep -E '^[0-9]+ passed' | tail -1)
rm -f "$CFG"
note "Flaky: **$FLAKY**. Steady: **$STEADY**."

say "Act 4 — the edges"
note "Keep polling starts work that never ends. A tap then is not held forever: after 10 seconds it is refused, naming what the app said kept it busy."
open_demo gray
start_capture "Act 4: work that never ends"
sleep 2
run tap testid=busyPoll
t0=$(ms)
run tap testid=busyRowA
POLL_MS=$(( $(ms) - t0 ))
POLL="$out"
$M screenshot -o "$OUT/act4-polling.png" >/dev/null
CRASH=
if [ -n "$VIRTUAL" ]; then
  note "Crash during a refresh dies holding its work. The next tap is not held up by the dead app, and says why."
  open_demo gray
  sleep 1
  run tap testid=busyCrash
  sleep 3
  # Android may say the app stopped, in a dialog of its own; closing it is
  # what anyone does next. Otherwise the tap is on the status bar, which
  # opens nothing — a point on the home screen can be an app's icon.
  if [ "$($M current 2>/dev/null)" = android ]; then run tap "text=Close app"; else run tap 300 30; fi
  CRASH="$out"
fi
stop_capture act4
$M terminate "$APP" >/dev/null 2>&1

# The two first acts side by side, when both were recorded.
if [ -f "$OUT/act1.mp4" ] && [ -f "$OUT/act2.mp4" ] && command -v ffmpeg >/dev/null; then
  d1=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/act1.mp4")
  d2=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/act2.mp4")
  long=$(python3 -c "print(max($d1, $d2))")
  # Each side's caption is drawn by a browser, so no ffmpeg font support is
  # needed: a strip of the page's own type, overlaid at the bottom.
  chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  caption() {
    printf '<body style="margin:0;background:#172033;color:#fff;font:600 46px -apple-system,Helvetica,sans-serif;display:flex;align-items:center;justify-content:center;height:120px">%s</body>' "$1" > "$OUT/.caption.html"
    "$chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=720,120 \
      --screenshot="$2" "file://$OUT/.caption.html" >/dev/null 2>&1
  }
  over=
  if [ -x "$chrome" ]; then
    caption "Launched normally" "$OUT/.cap1.png" && caption "Launched with --gray-box" "$OUT/.cap2.png" && over=1
  fi
  if [ -n "$over" ]; then
    graph="[0:v]fps=30,scale=-2:1600,tpad=stop_mode=clone:stop_duration=$long[a0];[2:v]scale=720:-1[c1];[a0][c1]overlay=(W-w)/2:H-h-40[a];[1:v]fps=30,scale=-2:1600,tpad=stop_mode=clone:stop_duration=$long[b0];[3:v]scale=720:-1[c2];[b0][c2]overlay=(W-w)/2:H-h-40[b];[a][b]hstack=inputs=2,trim=duration=$long"
    set -- -i "$OUT/act1.mp4" -i "$OUT/act2.mp4" -i "$OUT/.cap1.png" -i "$OUT/.cap2.png"
  else
    graph="[0:v]fps=30,scale=-2:1600,tpad=stop_mode=clone:stop_duration=$long[a];[1:v]fps=30,scale=-2:1600,tpad=stop_mode=clone:stop_duration=$long[b];[a][b]hstack=inputs=2,trim=duration=$long"
    set -- -i "$OUT/act1.mp4" -i "$OUT/act2.mp4"
  fi
  ffmpeg -loglevel error -y "$@" -filter_complex "$graph" \
    -c:v libx264 -pix_fmt yuv420p "$OUT/act1-vs-act2.mp4" && note "Side by side: act1-vs-act2.mp4."
  rm -f "$OUT/.caption.html" "$OUT/.cap1.png" "$OUT/.cap2.png"
fi

python3 - "$OUT/summary.json" <<EOF
import json, sys
json.dump({
  "device": "$KIND",
  "act1": {"row_b": """$ACT1""", "attempts": $ATTEMPTS},
  "act2": {"row_b": """$ACT2""", "tap": """$WAITED"""},
  "act3": {"flaky": "$FLAKY", "steady": "$STEADY"},
  "act4": {"poll_refused_after_ms": $POLL_MS, "poll": """$POLL""", "crash": """$CRASH"""},
  "video": bool("$VIDEO"),
}, open(sys.argv[1], "w"), indent=2)
EOF
# A real phone's UDID or serial names the phone: the traces record it with
# every call, so it becomes the device's kind.
if [ -n "$VIRTUAL" ]; then
  python3 "$ROOT/scripts/scrub.py" "$OUT" >/dev/null
else
  python3 "$ROOT/scripts/scrub.py" "$OUT" --redact "$DEV=$KIND" >/dev/null
fi
echo "evidence: $OUT"
ls "$OUT"
