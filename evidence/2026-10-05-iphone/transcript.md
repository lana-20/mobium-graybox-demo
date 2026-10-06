# Gray box on iphone

Recorded 2026-10-05 20:24 PDT with `mobium version 0.1.0-dev`, on iphone.

## Act 1 — the tap that lands too early

MobiumApp's Busy Demo, launched the ordinary way. Refresh quietly starts 0.4 to 1.6 seconds of work and leaves the old rows up; then Row B is tapped at once. Every Mobium action waits until its target is on screen, still, enabled and uncovered — and Row B is all four the whole time.

```
$ mobium launch dev.mobium.mobiumapp
launched dev.mobium.mobiumapp
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (645, 2545)
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (645, 1011)
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (645, 1905)
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
tapped label=Busy Demo at (645, 2545)
gray box: waited 37 ms for the app to go idle
```

```
$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (645, 1011)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowB
tapped testid=busyRowB at (645, 1905)
gray box: waited 955 ms for the app to go idle (busy: quiet)
```

```
$ mobium text testid=busyOutcome
row B, generation 2: current
```

Row B said: **row B, generation 2: current**. The tap: *waited 955 ms for the app to go idle (busy: quiet)*.

## Act 3 — as a test, five times each way

tests/flaky.test.json and tests/steady.test.json are the same test; the second adds "grayBox": true.

```
$ mobium test --config evidence/2026-10-05-iphone/mobium.config.json tests/flaky.test.json --reporter list,html --output evidence/2026-10-05-iphone/report-flaky
  FAIL  [iphone · iPhone 15 Plus] flaky.test.json › a row tapped after a quiet refresh is current (1) (10.2s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.239s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [iphone · iPhone 15 Plus] flaky.test.json › a row tapped after a quiet refresh is current (2) (10.2s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.22s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [iphone · iPhone 15 Plus] flaky.test.json › a row tapped after a quiet refresh is current (3) (10.1s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.266s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [iphone · iPhone 15 Plus] flaky.test.json › a row tapped after a quiet refresh is current (4) (9.9s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.24s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
  FAIL  [iphone · iPhone 15 Plus] flaky.test.json › a row tapped after a quiet refresh is current (5) (10.4s)
        step 3 (app_wait_for): [timeout] step 3 of 3 (app_wait_for) failed: timed out after 3.258s waiting for testid=busyOutcome to contain ": current" — its text is "row B, generation 1: stale"; steps 1-2 ran before it, and nothing after
0 passed, 5 failed (50.8s)
html report: evidence/2026-10-05-iphone/report-flaky/index.html
error: 5 of 5 tests failed
```

```
$ mobium test --config evidence/2026-10-05-iphone/mobium.config.json tests/steady.test.json --reporter list,html --trace on --output evidence/2026-10-05-iphone/report-steady
  ok    [iphone · iPhone 15 Plus] steady.test.json › a row tapped after a quiet refresh is current (1) (31.9s)
  ok    [iphone · iPhone 15 Plus] steady.test.json › a row tapped after a quiet refresh is current (2) (31.5s)
  ok    [iphone · iPhone 15 Plus] steady.test.json › a row tapped after a quiet refresh is current (3) (31.2s)
  ok    [iphone · iPhone 15 Plus] steady.test.json › a row tapped after a quiet refresh is current (4) (31.6s)
  ok    [iphone · iPhone 15 Plus] steady.test.json › a row tapped after a quiet refresh is current (5) (31.3s)
5 passed (2m37.5s)
html report: evidence/2026-10-05-iphone/report-steady/index.html
```

Flaky: **0 passed, 5 failed (50.8s)**. Steady: **5 passed (2m37.5s)**.

## Act 4 — the edges

Keep polling starts work that never ends. A tap then is not held forever: after 10 seconds it is refused, naming what the app said kept it busy.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (645, 2545)
gray box: waited 30 ms for the app to go idle
```

```
$ mobium tap testid=busyPoll
tapped testid=busyPoll at (645, 1525)
gray box: the app was idle
```

```
$ mobium tap testid=busyRowA
error: testid=busyRowA failed check idle: the app says it is still busy after 10s, with poll — something in the app never finishes; to act on the screen as it is, launch the app again without gray_box
```

Side by side: act1-vs-act2.mp4.

