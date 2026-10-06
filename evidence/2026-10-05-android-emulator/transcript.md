# Gray box on android-emulator

Recorded 2026-10-05 20:07 PDT with `mobium version 0.1.0-dev`, on android-emulator.

## Act 1 — the tap that lands too early

MobiumApp's Busy Demo, launched the ordinary way. Refresh quietly starts 0.4 to 1.6 seconds of work and leaves the old rows up; then Row B is tapped at once. Every Mobium action waits until its target is on screen, still, enabled and uncovered — and Row B is all four the whole time.

```
$ mobium launch dev.mobium.mobiumapp
launched dev.mobium.mobiumapp
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (540, 901)
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (540, 1722)
```

```
$ mobium text testid=busyOutcome
row B, generation 1: stale
```

Row B said: **row B, generation 1: stale** (attempt 1).

## Act 2 — ask the app

The same two taps, launched with --gray-box. MobiumApp links Mobium's gray-box library, which says in the device log when the app starts work and when the new rows are on screen.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)
gray box: waited 41 ms for the app to go idle
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (540, 901)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (540, 1722)
gray box: waited 1148 ms for the app to go idle (busy: quiet)
```

```
$ mobium text testid=busyOutcome
row B, generation 2: current
```

Row B said: **row B, generation 2: current**. The tap: *waited 1148 ms for the app to go idle (busy: quiet)*.

## Act 3 — as a test, five times each way

tests/flaky.test.json and tests/steady.test.json are the same test; the second adds "grayBox": true.

```
$ mobium test --config evidence/2026-10-05-android-emulator/mobium.config.json tests/flaky.test.json --reporter list,html --output evidence/2026-10-05-android-emulator/report-flaky
waiting for the UiAutomator2 server to start...
  FAIL  [android-emulator · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (1) (6.9s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.017s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [android-emulator · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (2) (7s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.023s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [android-emulator · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (3) (7s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.025s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [android-emulator · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (4) (7.4s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.024s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [android-emulator · emulator-5554] flaky.test.json › a row tapped after a quiet refresh is current (5) (7.1s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.03s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
0 passed, 5 failed (35.5s)
html report: evidence/2026-10-05-android-emulator/report-flaky/index.html
error: 5 of 5 tests failed
```

```
$ mobium test --config evidence/2026-10-05-android-emulator/mobium.config.json tests/steady.test.json --reporter list,html --trace on --output evidence/2026-10-05-android-emulator/report-steady
waiting for the UiAutomator2 server to start...
  ok    [android-emulator · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (1) (12.6s)
  ok    [android-emulator · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (2) (16.3s)
  ok    [android-emulator · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (3) (12s)
  ok    [android-emulator · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (4) (11.6s)
  ok    [android-emulator · emulator-5554] steady.test.json › a row tapped after a quiet refresh is current (5) (11.3s)
5 passed (1m3.7s)
html report: evidence/2026-10-05-android-emulator/report-steady/index.html
```

Flaky: **0 passed, 5 failed (35.5s)**. Steady: **5 passed (1m3.7s)**.

## Act 4 — the edges

Keep polling starts work that never ends. A tap then is not held forever: after 10 seconds it is refused, naming what the app said kept it busy.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)
gray box: waited 42 ms for the app to go idle
```

```
$ mobium tap testid=busyPoll
tapped testid=busyPoll at (540, 1372)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowA
error: testid=busyRowA failed check idle: the app says it is still busy after 10s, with poll — something in the app never finishes; to act on the screen as it is, launch the app again without gray_box
```

Crash during a refresh dies holding its work. The next tap is not held up by the dead app, and says why.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)
gray box: waited 31 ms for the app to go idle
```

```
$ mobium tap testid=busyCrash
tapped testid=busyCrash at (540, 1528)
gray box: the app was idle
```

```
$ mobium tap 300 30
tapped (300, 30)
gray box: not waited — the app stopped saying it is busy 3s ago (it was busy with doomed)
```

Side by side: act1-vs-act2.mp4.

