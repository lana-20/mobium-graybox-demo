# Ask the app

A tap that lands too early, made steady by asking the app when it is done —
with [Mobium](https://github.com/mobiumdev/mobium)'s gray box, on
[MobiumApp](https://github.com/mobiumdev/mobium-app), on Android and iOS,
virtual and real.

Everything here runs. `scripts/demo.sh` drives one device through four acts
and keeps the evidence of each: a screen recording, a trace, screenshots of
what the app said, the test reports, and a transcript of every command with
what it printed. [`evidence/`](evidence/README.md) holds the runs, and its
table is generated from them.

## The problem

MobiumApp's Busy Demo has a button, **Refresh quietly**, that starts 0.4 to
1.6 seconds of work and leaves the old rows up while it runs; then a new
generation of rows replaces them. Tapping a row says whether it was
`current` or `stale`.

```
$ mobium tap testid=busyQuiet
$ mobium tap testid=busyRowB
$ mobium text testid=busyOutcome
row B, generation 1: stale
```

Nothing in those commands is wrong. Every Mobium action waits until its
target is on screen, still, enabled and not covered — and Row B is all four
of those the whole time the work runs. The screen cannot say the work is
not done. Only the app can.

## The four acts

| Act | What happens | What it shows |
| --- | --- | --- |
| 1. The tap that lands too early | launched the ordinary way: Refresh quietly, then Row B | Row B is stale |
| 2. Ask the app | the same two taps, launched with `--gray-box` | the second tap waits for the app — `gray box: waited 1148 ms for the app to go idle (busy: quiet)`, on the emulator — and Row B is current |
| 3. As a test | [`tests/flaky.test.json`](tests/flaky.test.json) and [`tests/steady.test.json`](tests/steady.test.json), five times each | the same test, one key apart: five failures, then five passes |
| 4. The edges | work that never ends; the app crashing mid-work | refused after 10 s, naming the work; a dead app holds nothing up |

The timing above is from the emulator run; [`evidence/README.md`](evidence/README.md)
has every run's.

## One key

The two test files differ by one line:

```diff
   "app": "dev.mobium.mobiumapp",
+  "grayBox": true,
   "beforeEach": [
```

From the command line it is `mobium launch --gray-box`; from the clients,
`launch(app, gray_box=True)` in Python, `launch(app, { grayBox: true })` in
JavaScript, `LaunchWithGrayBox` in Go and .NET, `launchWithGrayBox` in Java.

## How the app says it is busy

MobiumApp links Mobium's gray-box library, a local Expo module in
`modules/graybox` (Swift and Kotlin). The Busy Demo tells it when work
starts, and that the work is finished only once the new rows are rendered:

```ts
const refresh = (visible: boolean) => {
  const tag = visible ? 'refresh' : 'quiet';
  pending.current += 1;
  GrayBox.busy(tag);
  // ... the work; when it is done, the new rows ...
};

useEffect(() => {
  while (finished.current.length) {
    pending.current -= 1;
    GrayBox.idle(finished.current.shift()!);
  }
}, [gen]);
```

The library is silent unless the app was launched with the gray box on — the
argument `-MobiumGrayBox YES` on iOS, the intent extra `MobiumGrayBox=true` on
Android — so the same build is safe in anyone's hands. When it is on, it
writes one line to the device log for each change, which Mobium reads as it
arrives:

```
MOBIUM-GRAYBOX on                 the library is listening
MOBIUM-GRAYBOX busy=1 tag=quiet   work started; 1 thing in flight
MOBIUM-GRAYBOX still busy=1       every half second while it is
MOBIUM-GRAYBOX busy=0 tag=quiet   that work finished, and is on screen
MOBIUM-GRAYBOX lift               a finger came up
MOBIUM-GRAYBOX away / back        the app left the foreground / returned
```

## Run it

You need Mobium built from `main`, and MobiumApp from `main` installed on the
device — its README says how to build it for each.

```sh
git clone https://github.com/mobiumdev/mobium.git && make -C mobium build
export MOBIUM=$PWD/mobium/bin/mobium

scripts/demo.sh emulator-5554                          # an Android emulator
scripts/demo.sh 457C7DC2-C706-45D9-8D68-1D26953E28B1   # an iOS simulator
python3 scripts/summarize.py                           # rebuild evidence/README.md
```

A run ends by taking this machine's paths out of its evidence
(`scripts/scrub.py`): the repository's path becomes relative and the home
directory `~`, in the transcript, the reports and inside each trace.

A run writes `evidence/<date>-<device kind>/`. Traces are in Vibium's record
format: open one at https://player.vibium.dev to step through every call and
what it answered. The acts' traces keep no screenshots, on purpose: a trace
takes a screenshot and reads the screen after every call, and every call
waits for that — on a Pixel 8 Pro the two taps took 5.1 s traced and 1.4 s
not, long enough for the work to finish first and the race to disappear.
Watching changed the timing. So the screen recording shows the screen, and
act 3's steady run, where the gray box waits anyway, keeps a full trace. On a real phone, everything recorded is
MobiumApp's own screen, and act 4's crash — which leaves the app — runs only
on a virtual device. A real iPhone's recording is WebDriverAgent's screen
stream, about ten frames a second at full size.

## The deck

`index.html` is the talk's slide deck, 29 slides: open it in a browser
(arrow keys move, S shows the speaker notes, F goes full screen). It is
built from `deck/deck.json` and one file per slide in `deck/slides/`, with
the recordings and posters in `deck/media/`:

```sh
python3 scripts/build_deck.py     # -> index.html, which GitHub Pages can serve as is
```

The demo slides loop act 1 against act 2 for each device, from the runs in
`evidence/`.

## What the gray box does not do

- **Detect work.** The app says when it is busy. Work it does not declare is
  not waited for, and an app that says it is idle too early is believed.
- **Wait on an app that cannot answer.** One that went to the background,
  crashed holding its work, or that Mobium has stopped hearing is not waited
  on — and the result says which.
- **Reach an app without the library.** Anything from an app store is driven
  the ordinary way.
