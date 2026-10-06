# Gray box on android-phone

Recorded 2026-10-05 20:03 PDT with `mobium version 0.1.0-dev`, on android-phone.

## Act 1 — the tap that lands too early

MobiumApp's Busy Demo, launched the ordinary way. Refresh quietly starts 0.4 to 1.6 seconds of work and leaves the old rows up; then Row B is tapped at once. Every Mobium action waits until its target is on screen, still, enabled and uncovered — and Row B is all four the whole time.

```
$ mobium launch dev.mobium.mobiumapp
launched dev.mobium.mobiumapp
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (504, 2129)
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (504, 771)
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (504, 1474)
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
tapped label=Busy Demo at (504, 2129)
gray box: waited 20 ms for the app to go idle
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (504, 771)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (504, 1474)
gray box: waited 709 ms for the app to go idle (busy: quiet)
```

```
$ mobium text testid=busyOutcome
row B, generation 2: current
```

Row B said: **row B, generation 2: current**. The tap: *waited 709 ms for the app to go idle (busy: quiet)*.

## Act 3 — as a test, five times each way

tests/flaky.test.json and tests/steady.test.json are the same test; the second adds "grayBox": true.

```
$ mobium test --config evidence/2026-10-05-android-phone/mobium.config.json tests/flaky.test.json --reporter list,html --output evidence/2026-10-05-android-phone/report-flaky
waiting for the UiAutomator2 server to start...
  FAIL  [android-phone · Pixel_8_Pro] flaky.test.json › a row tapped after a quiet refresh is current (1) (9.7s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.204s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  ok    [android-phone · Pixel_8_Pro] flaky.test.json › a row tapped after a quiet refresh is current (2) (6.6s)
  FAIL  [android-phone · Pixel_8_Pro] flaky.test.json › a row tapped after a quiet refresh is current (3) (9.7s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.18s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  ok    [android-phone · Pixel_8_Pro] flaky.test.json › a row tapped after a quiet refresh is current (4) (6.2s)
  ok    [android-phone · Pixel_8_Pro] flaky.test.json › a row tapped after a quiet refresh is current (5) (6.5s)
3 passed, 2 failed (38.7s)
html report: evidence/2026-10-05-android-phone/report-flaky/index.html
error: 2 of 5 tests failed
```

```
$ mobium test --config evidence/2026-10-05-android-phone/mobium.config.json tests/steady.test.json --reporter list,html --trace on --output evidence/2026-10-05-android-phone/report-steady
waiting for the UiAutomator2 server to start...
  ok    [android-phone · Pixel_8_Pro] steady.test.json › a row tapped after a quiet refresh is current (1) (28.7s)
  ok    [android-phone · Pixel_8_Pro] steady.test.json › a row tapped after a quiet refresh is current (2) (27s)
  ok    [android-phone · Pixel_8_Pro] steady.test.json › a row tapped after a quiet refresh is current (3) (28.1s)
  ok    [android-phone · Pixel_8_Pro] steady.test.json › a row tapped after a quiet refresh is current (4) (27.5s)
  ok    [android-phone · Pixel_8_Pro] steady.test.json › a row tapped after a quiet refresh is current (5) (26.5s)
5 passed (2m17.8s)
html report: evidence/2026-10-05-android-phone/report-steady/index.html
```

Flaky: **3 passed, 2 failed (38.7s)**. Steady: **5 passed (2m17.8s)**.

## Act 4 — the edges

Keep polling starts work that never ends. A tap then is not held forever: after 10 seconds it is refused, naming what the app said kept it busy.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (504, 2129)
gray box: waited 19 ms for the app to go idle
```

```
$ mobium tap testid=busyPoll
tapped testid=busyPoll at (504, 1174)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowA
error: testid=busyRowA failed check idle: the app says it is still busy after 10s, with poll — something in the app never finishes; to act on the screen as it is, launch the app again without gray_box
```

Side by side: act1-vs-act2.mp4.

