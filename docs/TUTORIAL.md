# Tutorial: from a flaky test to a steady one

The [quick start](QUICKSTART.md) showed one tap. This tutorial makes it a
test, runs it from Python, pushes the gray box to its edges, turns it round
so the test asks the app to do something, and ends with what your own app
needs to write.

Every command and output below was run on 5 October 2026 from a fresh clone
of this repository, with Mobium installed by `go install` and MobiumApp built
fresh, on a Pixel 7 emulator (Android 15). Before starting: the quick start's
steps 1 to 3 — Mobium installed, MobiumApp on a running emulator.

## Contents

- [1. The test that flakes](#1-the-test-that-flakes)
- [2. One key](#2-one-key)
- [3. From Python](#3-from-python)
- [4. What the result says](#4-what-the-result-says)
- [5. Work that never ends](#5-work-that-never-ends)
- [6. Ask the app to do something](#6-ask-the-app-to-do-something)
- [7. Your own app](#7-your-own-app)
- [8. Proving it on your devices](#8-proving-it-on-your-devices)

## 1. The test that flakes

Clone this repository and go into it:

```sh
git clone https://github.com/lana-20/mobium-graybox-demo.git
cd mobium-graybox-demo
```

[`mobium.config.json`](../mobium.config.json) names the device the tests run
on, `emulator-5554`, the first emulator's usual name — change it if
`mobium devices` names yours differently. [`tests/flaky.test.json`](../tests/flaky.test.json)
opens the Busy Demo, refreshes quietly, taps Row B, and waits up to three
seconds for the row to say `current` — five times, each from a fresh launch:

```json
{
  "app": "dev.mobium.mobiumapp",
  "beforeEach": [
    {"scroll_to": {"target": "label=Busy Demo", "direction": "down"}},
    {"tap": "label=Busy Demo"}
  ],
  "tests": [
    {
      "name": "a row tapped after a quiet refresh is current (${run})",
      "each": [{"run": 1}, {"run": 2}, {"run": 3}, {"run": 4}, {"run": 5}],
      "steps": [
        {"tap": "testid=busyQuiet"},
        {"tap": "testid=busyRowB"},
        {"wait_for": {"target": "testid=busyOutcome", "condition": "text", "text": ": current", "timeout_ms": 3000}}
      ]
    }
  ]
}
```

```sh
mobium test tests/flaky.test.json
```

```
  FAIL  [android · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (1) (7.1s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.024s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [android · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (2) (7.1s)
  FAIL  [android · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (3) (8.1s)
  FAIL  [android · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (4) (7.2s)
  FAIL  [android · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (5) (6.9s)
0 passed, 5 failed (36.4s)
error: 5 of 5 tests failed
```

(Each failure names its step and what the row said; the lines after the
first are trimmed here.) Inside a test, steps follow each other in
milliseconds, so the race is lost every time on this emulator. On a slower
device some pass — a real Pixel passed three in five — which is what makes a
test like this flaky rather than plainly broken. A sleep would hide it on a
fast day and fail on a slow one.

## 2. One key

[`tests/steady.test.json`](../tests/steady.test.json) is the same file with
one line added:

```diff
   "app": "dev.mobium.mobiumapp",
+  "grayBox": true,
   "beforeEach": [
```

```sh
mobium test tests/steady.test.json
```

```
  ok    [android · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (1) (6.1s)
  ok    [android · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (2) (5.9s)
  ok    [android · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (3) (6.4s)
  ok    [android · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (4) (7.1s)
  ok    [android · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (5) (5.9s)
5 passed (31.4s)
```

The steps are the same, and no sleep was added. Each test's launch now turns
the app's gray-box library on, and every step waits for the app to say it is
idle before finding its target.

## 3. From Python

The Python client isn't on PyPI yet; pip installs it straight from GitHub:

```sh
python3 -m venv .venv
.venv/bin/pip install "mobium @ git+https://github.com/mobiumdev/mobium.git#subdirectory=clients/python"
```

[`examples/graybox_tap.py`](../examples/graybox_tap.py) runs the race both
ways and prints what the row said. The heart of it:

```python
def busy_demo(device, gray_box):
    """Launch MobiumApp, normally or with the gray box, and open the Busy Demo."""
    device.terminate(APP)
    device.launch(APP, gray_box=gray_box)
    device.scroll_to("label=Busy Demo", direction="down")
    device.tap("label=Busy Demo")


def quiet_refresh_then_row_b(device):
    """Refresh quietly, tap Row B at once, and return what the row said."""
    time.sleep(2)  # any earlier refresh is over, so each try starts clean
    device.tap("testid=busyQuiet")
    device.tap("testid=busyRowB")
    device.wait_for("testid=busyOutcome", condition="text", text="row B")
    return device.text("testid=busyOutcome")
```

```sh
MOBIUM_DEVICE=emulator-5554 .venv/bin/python examples/graybox_tap.py
```

```
launched normally:   row B, generation 1: stale
with the gray box:   row B, generation 2: current
```

Three runs, the same answer each time.

One thing the first draft of this script got wrong, and the reason for its
`wait_for`: it read the row's verdict straight after the tap, and from
Python — faster than the command line — the read sometimes came back
`nothing tapped yet`. The row writes its verdict as it handles the tap, a
moment later. The gray box waits for the work the app declares, not for the
screen to redraw after every tap, so a read that depends on a tap's own
redraw still waits for it on the screen.

## 4. What the result says

Every action says what the gray box did. With `--json`, it is in `app_idle`:

```sh
mobium tap testid=busyRowB --json
```

```json
{
  "action": "tap",
  "app_idle": {
    "waited_ms": 737,
    "waits": [
      {
        "busy": [
          "quiet"
        ],
        "waited_ms": 737
      }
    ]
  },
  "target": "testid=busyRowB",
  "x": 540,
  "y": 1722
}
```

When the gray box did not wait, the result says why: the app said it was in
the background, it stopped renewing its busy state (it crashed, or was
suspended), or Mobium was not hearing it.

## 5. Work that never ends

The Busy Demo's **Keep polling** starts work that never finishes. A tap
then is not held forever:

```sh
mobium launch --gray-box dev.mobium.mobiumapp
mobium scroll-to "label=Busy Demo" --direction down
mobium tap "label=Busy Demo"
mobium tap testid=busyPoll
mobium tap testid=busyRowA
```

```
$ mobium tap testid=busyPoll
tapped testid=busyPoll at (540, 1372)
gray box: the app was idle

$ mobium tap testid=busyRowA
error: testid=busyRowA failed check idle: the app says it is still busy after 10s, with poll — something in the app never finishes; to act on the screen as it is, launch the app again without gray_box
```

After 10 seconds the action is refused with exit status 6, a timeout, naming
what the app said kept it busy. The remedy it names works: launched without
the gray box, the app is driven by what is on screen.

## 6. Ask the app to do something

Waiting is the app talking to the test. Hooks are the other direction: the
app registers a function by name, and a test calls it and gets back what it
returned — sign in, seed data, raise a toast, without walking the UI to get
there.

MobiumApp registers three: `raiseToast`, `screen` and `signIn`. In its
simplest form, `raiseToast` is this:

```js
// the app, in a build made for testing
GrayBox.register("raiseToast", (message) => {
  ToastAndroid.show(message, ToastAndroid.SHORT);
  return "shown";
});
```

MobiumApp's own also draws a toast of its own at the top of the screen
(`testID="hookToast"`), which is what an iPhone shows and what a test can
read back. From the command line:

```sh
mobium launch --gray-box dev.mobium.mobiumapp
mobium hook screen
mobium hook raiseToast "Toast raised by test script"
mobium text testid=hookToast
mobium hook signIn mobium
mobium text testid=welcomeText
mobium hook raiseTost typo
```

```
$ mobium hook screen
hook screen answered: "home"
gray box: the app was idle

$ mobium hook raiseToast "Toast raised by test script"
hook raiseToast answered: "shown"
gray box: the app was idle

$ mobium text testid=hookToast
Toast raised by test script

$ mobium hook signIn mobium
hook signIn answered: "signed in as mobium"
gray box: the app was idle

$ mobium text testid=welcomeText
Welcome, mobium!

$ mobium hook raiseTost typo
error: the app has no hook named raiseTost; registered: raiseToast, screen, signIn
```

`signIn` put the app on its welcome screen without the login form ever
being shown. The misspelled call was refused with exit status 2, an invalid
argument, naming the hooks that exist. A hook called on an app launched
without `--gray-box` is refused too, naming the launch that fixes it.

From Python, it is [`examples/hook_toast.py`](../examples/hook_toast.py):

```python
device.launch(APP, gray_box=True)

print("hook returned:", repr(device.hook("raiseToast", "Toast raised by test script")))
print("app's toast:  ", repr(device.text("testid=hookToast")))

try:
    device.hook("raiseTost", "typo")
except InvalidArgumentError as e:
    print("typo:", type(e).__name__, "-", e)
```

```
$ MOBIUM_DEVICE=emulator-5554 python3 examples/hook_toast.py
hook returned: 'shown'
app's toast:   'Toast raised by test script'
typo: InvalidArgumentError - the app has no hook named raiseTost; registered: raiseToast, screen, signIn
```

A hook's arguments are strings, and what it returns comes back as JSON: a
string, a number, an object. While a hook runs, and until two frames after
it answers, the app counts as busy, so the next action lands on the screen
the hook produced. And a message no keyboard layout holds whole — 
`"Привет, café — 5 ✓"` — arrives as sent, on every device: the call travels
ASCII-escaped.

Register hooks only in builds made for testing. A hook in a shipped build
is a door into the app; the gray box keeps it shut unless the launch opened
it, but it should not be there at all.

## 7. Your own app

The gray box needs the app to say two things: when work starts, and when it
is finished **and on screen**. In MobiumApp that is two calls around the
Busy Demo's refresh — `GrayBox.busy('quiet')` when it starts, and
`GrayBox.idle('quiet')` in an effect that runs after the new rows render.

**A React Native app** can copy MobiumApp's local Expo module,
[`modules/graybox`](https://github.com/mobiumdev/mobium-app/tree/main/modules/graybox):
about 90 lines of Swift and 70 of Kotlin, with the JavaScript shim beside
them.

**A native app** writes the lines itself. The whole contract is one line in
the device log per change — on iOS under the `os_log` subsystem
`dev.mobium.graybox`, at the default (notice) level with its values public;
on Android to logcat under the tag `MobiumGrayBox`, at info:

```
MOBIUM-GRAYBOX on                 once, at start
MOBIUM-GRAYBOX busy=1 tag=fetch   work started; the count of work in flight
MOBIUM-GRAYBOX still busy=1       every half second while the count is above 0
MOBIUM-GRAYBOX busy=0 tag=fetch   that work finished, and is on screen
MOBIUM-GRAYBOX lift               a finger came up
MOBIUM-GRAYBOX away / back        the app left the foreground / returned
```

Only when the app was launched with the gray box on — `-MobiumGrayBox YES`
on iOS, the intent extra `MobiumGrayBox=true` on Android — so the same build
is quiet in anyone else's hands. This is how MobiumApp's library writes them:

```swift
// iOS
static let log = Logger(subsystem: "dev.mobium.graybox", category: "busy")
static let enabled = UserDefaults.standard.bool(forKey: "MobiumGrayBox")

static func write(_ what: String) {
  let t = Int64(Date().timeIntervalSince1970 * 1000)
  log.notice("MOBIUM-GRAYBOX \(what, privacy: .public) t=\(t, privacy: .public)")
}
```

```kotlin
// Android
if (!activity.intent.getBooleanExtra("MobiumGrayBox", false)) return

fun write(what: String) {
  Log.i("MobiumGrayBox", "MOBIUM-GRAYBOX $what t=${System.currentTimeMillis()}")
}
```

`still` is what keeps a crashed app from holding a test hostage: Mobium
treats busy as a lease, and a count nobody has restated for 1.5 seconds is
not waited on. Restate it from a native timer, so a busy JavaScript thread
still renews it and a dead process doesn't. `lift` lets Mobium give work a
tap starts 150 ms to be announced; MobiumApp's library says it from a touch
recognizer on the key window (iOS) and the window's callback (Android).

**Hooks** need two things more. A text field whose accessibility identifier
(iOS) or content description (Android) is `mobium-mailbox`, added only in a
gray-box launch, small and kept on top: Mobium writes each call into it as
one line of JSON, `{"i":"<id>","h":"<name>","a":["<arg>", ...]}`, with
everything outside ASCII escaped. The app clears the field, runs the hook,
and answers on the same log:

```
MOBIUM-GRAYBOX hook id=<id> ok "shown"
MOBIUM-GRAYBOX hook id=<id> error <what went wrong>
```

The answer after `ok` is JSON. An error that begins `no hook named` is
reported as an unknown hook; any other is the hook failing, with its text.

## 8. Proving it on your devices

A fix has nothing to prove until the problem has shown up in the same run.
[`scripts/demo.sh`](../scripts/demo.sh) runs all of this on one device —
the race, the gray box, both test files, and the edges — and keeps a screen
recording, a trace, screenshots, the reports and a transcript of each:

```sh
MOBIUM=$(go env GOPATH)/bin/mobium scripts/demo.sh emulator-5554
MOBIUM=$(go env GOPATH)/bin/mobium scripts/hooks.sh emulator-5554
python3 scripts/summarize.py
```

[`scripts/hooks.sh`](../scripts/hooks.sh) is section 6 as a recorded act:
the toasts, the sign-in and the refused typo, with a screen recording, a
trace, screenshots and a transcript.

[`evidence/`](../evidence/README.md) holds the runs behind the deck: a Pixel 7
emulator, an iPhone 17 Pro simulator, a real Pixel 8 Pro and a real iPhone
15 Plus. Mobium's own checks, `docs/checks/graybox.sh`, `graybox-edges.sh`
and `graybox-hooks.sh`, hold the same demo to the app's verdict on every
device.
