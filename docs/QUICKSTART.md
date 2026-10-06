# Quick start: see the gray box work

Install Mobium, put MobiumApp on an emulator, watch a tap land on a row that
is about to be replaced, then watch the same tap wait for the app and land on
the new one.

Every command and output below was run from scratch on 5 October 2026, on a
Mac with a Pixel 7 emulator (Android 15): Mobium installed with `go install`,
MobiumApp cloned and built fresh. The iOS simulator works the same way;
[its steps are at the end](#on-an-ios-simulator).

## Contents

- [1. What you need](#1-what-you-need)
- [2. Install Mobium](#2-install-mobium)
- [3. Put MobiumApp on the emulator](#3-put-mobiumapp-on-the-emulator)
- [4. Watch the tap land too early](#4-watch-the-tap-land-too-early)
- [5. Ask the app](#5-ask-the-app)
- [On an iOS simulator](#on-an-ios-simulator)
- [Next](#next)

## 1. What you need

- **Go 1.24 or later**, to install Mobium.
- **An Android emulator**, running. Any recent one; this was a Pixel 7 image,
  Android 15. Android Studio's Device Manager makes one, or `avdmanager` on
  the command line.
- **Node 20 or later and JDK 17 or later**, to build MobiumApp. This run used
  Node 24 and JDK 21.
- **git**.

## 2. Install Mobium

```sh
go install github.com/mobiumdev/mobium/cmd/mobium@latest
mobium --version
```

```
mobium version v0.0.0-20261006042137-dcd27a426bb0
```

That took 20 seconds. (Mobium has no tagged release yet, so `@latest` is the
newest commit on `main`. The steps below ran on this version and the one
before it, with the same results apart from timings.) `mobium` lands in `$(go env GOPATH)/bin`, which should
be on your `PATH`. Check that it sees the emulator:

```sh
mobium devices
```

```
emulator-5554                          device     (android emulator, model: sdk_gphone64_arm64, navigation: gestures)
```

## 3. Put MobiumApp on the emulator

MobiumApp is Mobium's own app under test, and it carries Mobium's gray-box
library. Build it as a Release build, which bundles its JavaScript, so it
runs without a development server:

```sh
git clone https://github.com/mobiumdev/mobium-app.git
cd mobium-app
npm install
npx expo prebuild --platform android
npx expo run:android --variant release
cd ..
```

The last command builds the app, installs it on the running emulator and
opens it. Here it took 48 seconds, with npm's and Gradle's caches already
warm; the first build on a machine takes longer while Gradle downloads its
dependencies.

## 4. Watch the tap land too early

MobiumApp's **Busy Demo** has a button, **Refresh quietly**, that starts 0.4
to 1.6 seconds of work and leaves the old rows up while it runs; then a new
generation of rows replaces them. Each row says whether the one you tapped was
`current` or `stale`.

Open it, refresh quietly, and tap Row B straight away:

```sh
mobium launch dev.mobium.mobiumapp
mobium scroll-to "label=Busy Demo" --direction down
mobium tap "label=Busy Demo"
mobium tap testid=busyQuiet
mobium tap testid=busyRowB
mobium text testid=busyOutcome
```

```
$ mobium launch dev.mobium.mobiumapp
waiting for the UiAutomator2 server to start...
launched dev.mobium.mobiumapp

$ mobium scroll-to "label=Busy Demo" --direction down
label=Busy Demo is on screen after 1 scroll down — @e16 Busy Demo (button)

$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)

$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (540, 901)

$ mobium tap testid=busyRowB
tapped testid=busyRowB at (540, 1722)

$ mobium text testid=busyOutcome
row B, generation 1: stale
```

Every Mobium action already waits until its target is on screen, still,
enabled and not covered — and Row B was all four the whole time. Nothing on
the screen says the work is not done. The race depends on how long the work
happens to take: on this emulator ten tries in ten landed stale, and on a
real Pixel and iPhone seven to nine in ten did.

## 5. Ask the app

Launch the same app with `--gray-box`, and run the same taps:

```sh
mobium launch --gray-box dev.mobium.mobiumapp
mobium scroll-to "label=Busy Demo" --direction down
mobium tap "label=Busy Demo"
mobium tap testid=busyQuiet
mobium tap testid=busyRowB
mobium text testid=busyOutcome
```

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle

$ mobium scroll-to "label=Busy Demo" --direction down
label=Busy Demo is on screen after 1 scroll down — @e16 Busy Demo (button)

$ mobium tap "label=Busy Demo"
tapped label=Busy Demo at (540, 2266)
gray box: waited 41 ms for the app to go idle

$ mobium tap testid=busyQuiet
tapped testid=busyQuiet at (540, 901)
gray box: the app was idle

$ mobium tap testid=busyRowB
tapped testid=busyRowB at (540, 1722)
gray box: waited 707 ms for the app to go idle (busy: quiet)

$ mobium text testid=busyOutcome
row B, generation 2: current
```

The tap on Row B waited 707 ms — as long as the work took, no longer — for
the app to say it was done, and landed on the new rows. Every result says
what it waited for.

`--gray-box` launches the app with the intent extra `MobiumGrayBox=true`
(on iOS, the launch argument `-MobiumGrayBox YES`). MobiumApp's library is
silent without it, so the same build behaves normally for anyone who opens it
from the home screen.

## On an iOS simulator

Everything above works on an iOS simulator, with Xcode instead of the
Android tools. Verified on an iPhone 17 Pro simulator, iOS 26.5, from the
same fresh clone of MobiumApp:

```sh
cd mobium-app
npx expo prebuild --platform ios
npx expo run:ios --configuration Release --device "iPhone 17 Pro"
cd ..
```

That built, installed and opened MobiumApp in 82 seconds, with CocoaPods'
cache warm. Then the same commands. If an Android emulator is running too,
Mobium picks it by default: name the simulator with `--device` and its UDID
from `mobium devices`.

```
$ mobium --device 457C7DC2-C706-45D9-8D68-1D26953E28B1 launch dev.mobium.mobiumapp
waiting for WebDriverAgent to start...
the simulator is on its home screen: a new session starts WebDriverAgent, whose runner takes the foreground and leaves it to the home screen, not to the app that was in front — app_launch brings an app back...
launched dev.mobium.mobiumapp
...
$ mobium --device 457C7DC2-C706-45D9-8D68-1D26953E28B1 text testid=busyOutcome
row B, generation 1: stale

$ mobium --device 457C7DC2-C706-45D9-8D68-1D26953E28B1 launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
...
$ mobium --device 457C7DC2-C706-45D9-8D68-1D26953E28B1 tap testid=busyRowB
tapped testid=busyRowB at (603, 1965)
gray box: waited 1341 ms for the app to go idle (busy: quiet)

$ mobium --device 457C7DC2-C706-45D9-8D68-1D26953E28B1 text testid=busyOutcome
row B, generation 2: current
```

The first command starts WebDriverAgent on the simulator, which takes a few
seconds the first time. On iOS `--gray-box` launches the app with the
argument `-MobiumGrayBox YES`, stopping it first if it was running, so the
argument reaches it.

Writing this quick start found that last part missing: a gray-box launch of
an app already running on iOS brought it forward without the argument, and
it never heard the gray box. Fixed in Mobium the same day
([mobiumdev/mobium#132](https://github.com/mobiumdev/mobium/pull/132)).

## Next

- **[The tutorial](TUTORIAL.md)**: the same race as a test that fails five
  times in five and passes five in five with one key, from Python, at its
  edges, and in your own app.
- **[The deck](https://lana-20.github.io/mobium-graybox-demo/)**: the talk
  this repository was built for, with each device's recordings.
- **Mobium's own guide**:
  [gray box](https://mobiumdev.github.io/guides/graybox) and
  [its tutorial](https://mobiumdev.github.io/guides/graybox-tutorial).
