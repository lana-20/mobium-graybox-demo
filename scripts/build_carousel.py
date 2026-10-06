#!/usr/bin/env python3
"""Builds the LinkedIn carousel: ten 1080 x 1350 slides about Mobium's gray
box, one per page when printed.

    python3 scripts/build_carousel.py [--fragment PATH]

Writes carousel/index.html (a whole page, for GitHub Pages) and, with
--fragment, the same slides without the document skeleton, for a host that
supplies its own. carousel/mobium-gray-box.pdf is printed from index.html by
headless Chrome. Every figure on a slide is from evidence/README.md.
"""
import argparse
import base64
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "carousel"
MEDIA = OUT / "media"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def data_uri(name):
    path = MEDIA / name
    kind = "image/png" if name.endswith(".png") else "image/jpeg"
    return f"data:{kind};base64,{base64.b64encode(path.read_bytes()).decode()}"


TITLE = "Ask the App: Mobium's Gray Box"

STYLE = """
/* Layout: ten 4:5 slides, sized in container units so one design serves a
   phone screen, a desktop column and a 1080 x 1350 printed page. */
:root {
  --ink: #0E1426;        /* slide ground: the logo's own dark setting */
  --well: #0A0F1D;       /* code and screenshot wells */
  --rule: #253049;
  --paper: #EDEAE3;      /* text */
  --dim: #94A0AB;
  --brass: #E0A526;      /* the one accent */
  --go: #6FBF95;         /* current, passed */
  --stop: #E2735C;       /* stale, failed */
  --display: "Rubik", "Helvetica Neue", Arial, sans-serif;
  --mono: "Fira Code", "SF Mono", Menlo, Consolas, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html, body { background: var(--ink); color: var(--paper); }
body { margin: 0; font-family: var(--display); padding-block: 24px 48px; padding-inline: 16px; }
.deck { display: grid; gap: 24px; justify-items: center; }
.slide {
  container-type: inline-size;
  width: min(540px, 100%);
  aspect-ratio: 4 / 5;
  background: var(--ink);
  border: 1px solid var(--rule);
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}
.in {
  position: absolute; inset: 0;
  padding: 8cqw 8cqw 7cqw;
  display: flex; flex-direction: column; gap: 3.4cqw;
}
.top { display: flex; justify-content: space-between; align-items: center; }
.eyebrow { font-family: var(--mono); font-size: 2.3cqw; letter-spacing: 0.32cqw; text-transform: uppercase; color: var(--brass); }
.count { font-family: var(--mono); font-size: 2.1cqw; color: var(--dim); font-variant-numeric: tabular-nums; }
h1, h2 { margin: 0; font-weight: 600; letter-spacing: -0.15cqw; text-wrap: balance; }
h1 { font-size: 9.6cqw; line-height: 1.02; }
h2 { font-size: 6.6cqw; line-height: 1.08; }
p { margin: 0; font-size: 3.15cqw; line-height: 1.42; color: var(--paper); font-weight: 300; text-wrap: pretty; }
p.dim { color: var(--dim); }
b { font-weight: 600; }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; gap: 3cqw; }
.mark { width: 7cqw; height: 7cqw; object-fit: contain; }
.sig { font-family: var(--mono); font-size: 2.1cqw; color: var(--dim); text-align: right; line-height: 1.5; }
pre {
  margin: 0; background: var(--well); border: 1px solid var(--rule); border-radius: 1.6cqw;
  padding: 3cqw 3.4cqw; font-family: var(--mono); font-size: 2.55cqw; line-height: 1.6;
  color: #BDC6CE; white-space: pre-wrap; overflow-wrap: anywhere;
}
pre .p { color: #5E6A76; }
pre .c { color: #6E7A86; }
pre .k { color: var(--brass); }
pre .s { color: #9AD3B1; }
pre .go { color: var(--go); font-weight: 500; }
pre .stop { color: var(--stop); font-weight: 500; }
.verdict { font-family: var(--mono); font-size: 3.3cqw; }
.verdict .stop { color: var(--stop); } .verdict .go { color: var(--go); }
.shots { display: grid; grid-template-columns: 1fr 1fr; gap: 3cqw; min-height: 0; flex: 1; }
.shot { display: flex; flex-direction: column; gap: 1.4cqw; min-height: 0; }
.shot img { width: 100%; flex: 1; min-height: 0; object-fit: cover; object-position: top; border-radius: 1.6cqw; border: 1px solid var(--rule); background: #fff; }
.shot span { font-family: var(--mono); font-size: 2.2cqw; letter-spacing: 0.2cqw; text-transform: uppercase; }

/* 1: cover */
.cover h1 .late { color: var(--brass); }
.logo { width: 34cqw; height: auto; display: block; margin-left: -3cqw; }
.cover .rows { display: grid; gap: 1.6cqw; margin-top: 2cqw; }
.cover .row { display: flex; justify-content: space-between; align-items: baseline; font-family: var(--mono); font-size: 3.2cqw; padding: 2.4cqw 3cqw; border-radius: 1.4cqw; background: var(--well); border: 1px solid var(--rule); }
.cover .row em { font-style: normal; font-size: 2.3cqw; color: var(--dim); }

/* 2: the four checks */
.checks { display: grid; grid-template-columns: 1fr 1fr; gap: 1.8cqw; }
.check { display: flex; justify-content: space-between; align-items: center; padding: 2.4cqw 3cqw; background: var(--well); border: 1px solid var(--rule); border-radius: 1.4cqw; font-family: var(--mono); font-size: 2.8cqw; }
.check b { color: var(--go); font-weight: 500; font-size: 2.3cqw; letter-spacing: 0.2cqw; text-transform: uppercase; }

/* 3: the race, drawn to one time scale: 0 to 2.0 s across the track */
.race { display: grid; gap: 3cqw; margin-block: 3cqw; }
.lane { display: grid; grid-template-columns: 17cqw 1fr; align-items: center; gap: 2cqw; font-family: var(--mono); font-size: 2.2cqw; color: var(--dim); }
.track { position: relative; height: 8.5cqw; background: var(--well); border: 1px solid var(--rule); border-radius: 1cqw; }
.bar { position: absolute; top: 0.9cqw; bottom: 0.9cqw; border-radius: 0.6cqw; display: flex; align-items: center; padding-left: 1.6cqw; font-size: 2.4cqw; color: var(--ink); font-weight: 500; white-space: nowrap; overflow: hidden; }
.tick { position: absolute; top: -0.6cqw; bottom: -0.6cqw; width: 0.5cqw; border-radius: 0.3cqw; }
.axis { display: grid; grid-template-columns: 17cqw 1fr; gap: 2cqw; font-family: var(--mono); font-size: 1.9cqw; color: var(--dim); }
.axis .scale { display: flex; justify-content: space-between; }

/* 6: results */
table { border-collapse: collapse; width: 100%; font-size: 2.7cqw; }
th, td { text-align: left; padding: 2cqw 1.6cqw; border-bottom: 1px solid var(--rule); }
th { font-family: var(--mono); font-weight: 400; font-size: 2cqw; letter-spacing: 0.2cqw; text-transform: uppercase; color: var(--dim); }
td.n { font-family: var(--mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
td.stop { color: var(--stop); } td.go { color: var(--go); }
tr:last-child td { border-bottom: 0; }

/* 7, 9: lists */
.list { display: grid; gap: 2.6cqw; }
.item { display: grid; grid-template-columns: 1fr; gap: 0.8cqw; padding-left: 3cqw; border-left: 0.5cqw solid var(--rule); }
.item b { font-size: 3.3cqw; font-weight: 500; }
.item span { font-size: 2.8cqw; font-weight: 300; color: var(--dim); line-height: 1.4; }

/* 10: call to action */
.cta .links { display: grid; gap: 1.6cqw; }
.cta pre { font-size: 2.3cqw; }
.cta .link { font-family: var(--mono); font-size: 2.9cqw; color: var(--paper); padding: 2cqw 3cqw; background: var(--well); border: 1px solid var(--rule); border-radius: 1.4cqw; display: grid; gap: 0.6cqw; }
.cta .link em { font-style: normal; font-size: 2.1cqw; color: var(--dim); letter-spacing: 0.15cqw; text-transform: uppercase; }
a { color: inherit; text-decoration: none; }
a:focus-visible { outline: 2px solid var(--brass); outline-offset: 2px; }

@page { size: 1080px 1350px; margin: 0; }
@media print {
  body { padding: 0; }
  .deck { display: block; }
  .slide { width: 1080px; border: 0; border-radius: 0; break-after: page; }
}
"""


def slide(n, eyebrow, body, extra=""):
    return f"""<section class="slide {extra}" aria-label="Slide {n} of 10">
  <div class="in">
    <div class="top"><span class="eyebrow">{eyebrow}</span><span class="count">{n:02d} / 10</span></div>
{body}
  </div>
</section>"""


def foot(mark, right="mobium &middot; gray box"):
    return f"""    <div class="foot"><img class="mark" src="{mark}" alt="Mobium"><span class="sig">{right}</span></div>"""


def slides():
    mark = data_uri("mark.png")
    stale, current = data_uri("stale.jpg"), data_uri("current.jpg")
    pixel, iphone = data_uri("pixel-toast.jpg"), data_uri("iphone-toast.jpg")
    out = []

    logo = data_uri("logo-dark.png")
    out.append(slide(1, "Mobium &middot; gray box", f"""    <img class="logo" src="{logo}" alt="Mobium">
    <h1>The tap was right.<br><span class="late">It landed too early.</span></h1>
    <p>Why a test that does everything right still flakes on mobile, and how Mobium asks the app when it is done. Measured on an emulator, a simulator, a Pixel 8 Pro and an iPhone 15 Plus.</p>
    <div class="rows">
      <div class="row"><span>row B, generation 1: <b style="color:var(--stop)">stale</b></span><em>launched normally</em></div>
      <div class="row"><span>row B, generation 2: <b style="color:var(--go)">current</b></span><em>with --gray-box</em></div>
    </div>
{foot(mark, "swipe &rarr;")}""", "cover"))

    out.append(slide(2, "The problem", f"""    <h2>Every wait passed. The tap still missed.</h2>
<pre><span class="p">$</span> mobium tap testid=busyQuiet
<span class="p">$</span> mobium tap testid=busyRowB
<span class="p">$</span> mobium text testid=busyOutcome
<span class="stop">row B, generation 1: stale</span></pre>
    <p>Before it taps, Mobium waits for the target to pass four checks. Row B passed all four the whole time:</p>
    <div class="checks">
      <div class="check"><span>on screen</span><b>passed</b></div>
      <div class="check"><span>still</span><b>passed</b></div>
      <div class="check"><span>enabled</span><b>passed</b></div>
      <div class="check"><span>uncovered</span><b>passed</b></div>
    </div>
    <p>It was also about to be replaced, and nothing on screen said so.</p>
{foot(mark, "real iPhone 15 Plus, iOS 26.6.2")}"""))

    # The race, to scale: the track is 2.0 s wide. The work runs 0.4 to
    # 1.6 s; this one took 1.0 s. The tap comes at about 0.15 s.
    pct = lambda s: f"{s / 2.0 * 100:.1f}%"
    out.append(slide(3, "Why it flakes", f"""    <h2>Only the app knows it is still busy.</h2>
    <p>MobiumApp's Busy Demo starts 0.4 to 1.6 seconds of work and leaves the old rows up while it runs. A tap that comes before the new rows lands on a row that is about to go.</p>
    <div class="race" role="img" aria-label="Timeline, 0 to 2 seconds: the refresh work runs from 0 to 1.0 seconds while the old rows stay up; the new rows appear at 1.0 seconds; the tap at about 0.15 seconds lands on the old rows.">
      <div class="lane"><span>work</span><div class="track"><div class="bar" style="left:0;width:{pct(1.0)};background:var(--brass)">refresh quietly</div></div></div>
      <div class="lane"><span>on screen</span><div class="track"><div class="bar" style="left:0;width:{pct(1.0)};background:#5E6A76;color:var(--paper)">old rows</div><div class="bar" style="left:{pct(1.0)};width:{pct(1.0)};background:var(--go)">new rows</div></div></div>
      <div class="lane"><span>the tap</span><div class="track"><div class="tick" style="left:{pct(0.15)};background:var(--stop)"></div></div></div>
      <div class="axis"><span></span><div class="scale"><span>0 s</span><span>0.5</span><span>1.0</span><span>1.5</span><span>2.0</span></div></div>
    </div>
    <p class="dim">On a real Pixel and iPhone, 7 to 9 taps in 10 landed stale.</p>
{foot(mark)}"""))

    out.append(slide(4, "The fix, in the app", f"""    <h2>So the app says when it is busy.</h2>
<pre><span class="k">const</span> refresh = () =&gt; {{
  GrayBox.<span class="k">busy</span>(<span class="s">'quiet'</span>);
  <span class="c">// the work, then the new rows</span>
}};
<span class="c">// once the new rows have rendered:</span>
GrayBox.<span class="k">idle</span>(<span class="s">'quiet'</span>);</pre>
    <p>MobiumApp links Mobium's gray-box library, in Swift and Kotlin. It writes one line to the device log for each change, and Mobium already reads that log:</p>
<pre>MOBIUM-GRAYBOX busy=1 tag=quiet
MOBIUM-GRAYBOX still busy=1
MOBIUM-GRAYBOX busy=0 tag=quiet</pre>
{foot(mark)}"""))

    out.append(slide(5, "The fix, in the test", f"""    <h2>One flag. The tap waits for the app.</h2>
<pre><span class="p">$</span> mobium launch <span class="k">--gray-box</span> dev.mobium.mobiumapp
<span class="p">$</span> mobium tap testid=busyRowB
<span class="k">gray box: waited 955 ms for the app to go idle (busy: quiet)</span></pre>
    <div class="shots">
      <figure class="shot" style="margin:0"><span style="color:var(--stop)">launched normally</span><img src="{stale}" alt="iPhone: row B, generation 1: stale"></figure>
      <figure class="shot" style="margin:0"><span style="color:var(--go)">with --gray-box</span><img src="{current}" alt="iPhone: row B, generation 2: current"></figure>
    </div>
{foot(mark, "real iPhone 15 Plus")}"""))

    out.append(slide(6, "As a test", f"""    <h2>The same test, one key apart.</h2>
<pre>  <span class="s">"app"</span>: <span class="s">"dev.mobium.mobiumapp"</span>,
<span class="go">+ "grayBox": true,</span></pre>
    <p>Five runs each way, on four devices:</p>
    <table>
      <thead><tr><th>Device</th><th>Without</th><th>With</th><th>Waited</th></tr></thead>
      <tbody>
        <tr><td>Pixel 7 emulator</td><td class="n stop">0 of 5</td><td class="n go">5 of 5</td><td class="n">1148 ms</td></tr>
        <tr><td>iPhone 17 Pro simulator</td><td class="n stop">0 of 5</td><td class="n go">5 of 5</td><td class="n">1202 ms</td></tr>
        <tr><td>Pixel 8 Pro</td><td class="n stop">3 of 5</td><td class="n go">5 of 5</td><td class="n">709 ms</td></tr>
        <tr><td>iPhone 15 Plus</td><td class="n stop">0 of 5</td><td class="n go">5 of 5</td><td class="n">955 ms</td></tr>
      </tbody>
    </table>
    <p class="dim">Passing 3 of 5 is what flaky looks like: it depends on how long the work happened to take.</p>
{foot(mark)}"""))

    out.append(slide(7, "The edges", f"""    <h2>A wait that knows when to stop.</h2>
    <div class="list">
      <div class="item"><b>Work that never ends</b><span>Refused after 10 seconds, naming what kept the app busy.</span></div>
      <div class="item"><b>The app goes home, or crashes</b><span>Not waited on. Busy is a lease the app renews twice a second, and a dead app stops renewing it.</span></div>
      <div class="item"><b>The log stream drops</b><span>The result says Mobium could not hear the app, and it listens again.</span></div>
      <div class="item"><b>Every result says what it waited for</b><span>&ldquo;waited 955 ms (busy: quiet)&rdquo;, &ldquo;the app was idle&rdquo;, or why it did not wait.</span></div>
    </div>
    <p class="dim">All six edge checks pass on all four devices.</p>
{foot(mark)}"""))

    out.append(slide(8, "The other way round", f"""    <h2>The test asks the app to do something.</h2>
<pre><span class="c">// the app, in a build made for testing</span>
GrayBox.<span class="k">register</span>(<span class="s">"raiseToast"</span>, (message) =&gt; {{
  ToastAndroid.show(message, ToastAndroid.SHORT);
  <span class="k">return</span> <span class="s">"shown"</span>;
}});
<span class="c"># the test</span>
device.<span class="k">hook</span>(<span class="s">"raiseToast"</span>, <span class="s">"Toast raised by test script"</span>)  <span class="go"># 'shown'</span></pre>
    <div class="shots">
      <figure class="shot" style="margin:0"><span style="color:var(--dim)">Pixel 8 Pro</span><img src="{pixel}" alt="Pixel: the app's toast at the top and Android's toast at the bottom"></figure>
      <figure class="shot" style="margin:0"><span style="color:var(--dim)">iPhone 15 Plus</span><img src="{iphone}" alt="iPhone: the app's toast at the top"></figure>
    </div>
{foot(mark, "sign in, seed data, raise a toast")}"""))

    out.append(slide(9, "The trust model", f"""    <h2>A door the app opens, and only for the test.</h2>
    <div class="list">
      <div class="item"><b>The app opts in</b><span>It links a small library and says what it is doing. Work it does not declare is not waited for.</span></div>
      <div class="item"><b>Silent unless the test turns it on</b><span>A launch argument on iOS, an intent extra on Android. Anyone opening the same build sees nothing.</span></div>
      <div class="item"><b>Only what the app registered</b><span>A hook is called by name. Any other name is refused, with the list of names that exist.</span></div>
      <div class="item"><b>Builds made for testing</b><span>Keep hooks out of what ships. An app without the library is driven the ordinary way.</span></div>
    </div>
{foot(mark)}"""))

    out.append(slide(10, "Try it", f"""    <img class="logo" src="{logo}" alt="Mobium" style="width:22cqw">
    <h2>See the race, then fix it, in a few minutes.</h2>
<pre><span class="p">$</span> go install github.com/mobiumdev/mobium/cmd/mobium@latest
<span class="p">$</span> mobium launch --gray-box dev.mobium.mobiumapp</pre>
    <div class="links">
      <a class="link" href="https://github.com/mobiumdev/mobium"><em>Mobium</em>github.com/mobiumdev/mobium</a>
      <a class="link" href="https://github.com/lana-20/mobium-graybox-demo"><em>Quick start, tutorial, evidence</em>github.com/lana-20/mobium-graybox-demo</a>
      <a class="link" href="https://lana-20.github.io/mobium-graybox-demo/"><em>The talk, with every device's recordings</em>lana-20.github.io/mobium-graybox-demo</a>
    </div>
{foot(mark, "Lana Begunova<br>mobile automation for AI agents and humans")}""", "cta"))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", help="also write the slides without the document skeleton here")
    args = ap.parse_args()
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Rubik:wght@300;400;500;600&display=swap">')
    body = f'<main class="deck">\n{slides()}\n</main>'
    fragment = f"<title>{TITLE}</title>\n{fonts}\n<style>{STYLE}</style>\n{body}\n"
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"{fragment.replace(body, '')}</head>\n<body>\n{body}\n</body>\n</html>\n")
    (OUT / "index.html").write_text(page)
    if args.fragment:
        pathlib.Path(args.fragment).write_text(fragment)
    pdf = OUT / "mobium-gray-box.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=5000", f"--print-to-pdf={pdf}",
                    (OUT / "index.html").as_uri()], check=True, capture_output=True)
    print(f"carousel: {OUT / 'index.html'}, {pdf}")


if __name__ == "__main__":
    main()
