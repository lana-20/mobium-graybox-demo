# Hooks on ios-simulator

Recorded 2026-10-05 23:55 PDT with `mobium version 0.1.0-dev`, on ios-simulator.

## Act 5 — ask the app to do something

MobiumApp registers three hooks with its gray-box library: raiseToast, screen and signIn. Each call below is held to what the app then shows.

```
$ mobium launch --gray-box dev.mobium.mobiumapp
launched dev.mobium.mobiumapp, with the gray box: every action waits for the app to say it is idle
```

```
$ mobium hook screen
hook screen answered: "home"
gray box: the app was idle
```

```
$ mobium hook raiseToast "Toast raised by test script"
hook raiseToast answered: "shown"
gray box: the app was idle
```

```
$ mobium text testid=hookToast
Toast raised by test script
```

```
$ mobium hook raiseToast "Привет, café — 5 ✓"
hook raiseToast answered: "shown"
gray box: the app was idle
```

```
$ mobium text testid=hookToast
Привет, café — 5 ✓
```

```
$ mobium hook signIn mobium
hook signIn answered: "signed in as mobium"
gray box: the app was idle
```

```
$ mobium text testid=welcomeText
Welcome, mobium!
```

```
$ mobium hook screen
hook screen answered: "secret"
gray box: waited 38 ms for the app to go idle
```

```
$ mobium hook raiseTost typo
error: the app has no hook named raiseTost; registered: raiseToast, screen, signIn
```

The toast said **Toast raised by test script**, then **Привет, café — 5 ✓**; the welcome screen said **Welcome, mobium!**; the typo was refused.

