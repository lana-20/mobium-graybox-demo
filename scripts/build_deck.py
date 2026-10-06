#!/usr/bin/env python3
"""Build a standalone, self-contained deck.html from deck.json + slides/*.html.

The slide files are the source of truth and are byte-identical to the ones in the
Claude artifact. This script only wraps them in a viewer: it never edits a slide.

A slide names an uploaded file the artifact's way, `/_blob/<id>`. deck/media/assets.json
maps each id to its copy in deck/media/, and the viewer gets that path instead; a
picture carrying `data-video` becomes a looping, muted <video> with it as the poster.

    python3 scripts/build_deck.py          # -> index.html (what Pages serves)
"""
import json, re, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck"

def main() -> int:
    index = json.loads((DECK / "deck.json").read_text())
    order, title = index["order"], index["title"]

    hrefs, seen = [], set()
    for face in index.get("faces", {}).values():
        h = face.get("href")
        if h and h not in seen:
            seen.add(h); hrefs.append(h)

    assets_file = DECK / "media" / "assets.json"
    assets = json.loads(assets_file.read_text()) if assets_file.exists() else {}
    unmapped = set()

    def local(m):
        blob = m.group(1)
        if blob not in assets or not (DECK / "media" / assets[blob]).exists():
            unmapped.add(blob); return m.group(0)
        return f"deck/media/{assets[blob]}"

    def video(m):
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]*)"', tag)
        vid = re.search(r'\bdata-video="([^"]*)"', tag)
        alt = re.search(r'\balt="([^"]*)"', tag)
        style = re.search(r'\bstyle="([^"]*)"', tag)
        return (f'<video src="{vid.group(1)}" poster="{src.group(1) if src else ""}" '
                f'aria-label="{alt.group(1) if alt else ""}" style="{style.group(1) if style else ""}" '
                f'autoplay muted loop playsinline></video>')

    slides, notes, missing = [], [], []
    for sid in order:
        f = DECK / "slides" / f"{sid}.html"
        if not f.exists():
            missing.append(sid); continue
        raw = f.read_text().strip()
        m = re.search(r"<section\b.*</section>", raw, re.S)
        if not m:
            print(f"error: {f} has no <section>", file=sys.stderr); return 1
        section = m.group(0)
        a = re.search(r"<aside>(.*?)</aside>", section, re.S)
        note = re.sub(r"<[^>]+>", "", a.group(1)).strip() if a else ""
        notes.append(note)
        section = re.sub(r"/?_blob/([0-9a-f]{32})", local, section)
        section = re.sub(r"<img\b[^>]*\bdata-video=[^>]*>", video, section)
        slides.append(f'<div class="slide" data-id="{sid}">{section}</div>')

    if unmapped:
        print(f"error: no file in deck/media for asset(s): {', '.join(sorted(unmapped))} — add them to deck/media/assets.json", file=sys.stderr)
        return 1
    if missing:
        print(f"error: no file for slide id(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    font_links = "\n".join(f'<link rel="stylesheet" href="{h}">' for h in hrefs)
    notes_json = json.dumps(notes)

    out = TEMPLATE.format(
        title=html.escape(title),
        font_links=font_links,
        slides="\n".join(slides),
        notes=notes_json,
        count=len(slides),
    )
    out_path = ROOT / "index.html"
    out_path.write_text(out)
    print(f"wrote {out_path} - {len(slides)} slides, {len(hrefs)} font link(s)")
    return 0

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{font_links}
<style>
  html, body {{ margin:0; height:100%; background:#0B0E11; overflow:hidden; }}
  body {{ font-family: Rubik, Arial, sans-serif; }}
  #stage {{ position:fixed; inset:0; overflow:hidden; }}
  .slide {{ position:absolute; inset:0; visibility:hidden; }}
  .slide.is-active {{ visibility:visible; }}
  /* The slide format assumes a border-box canvas with no default margins:
     padding sits INSIDE 1920x1080, and spacing comes from flex/grid gap only.
     Without this reset a section lays out at 2176x1368 and spills off-screen. */
  .slide > section, .slide > section * {{ box-sizing:border-box; margin:0; }}
  /* Centered by absolute positioning, not by grid: a 1920px item makes an auto
     grid track 1920px wide, so place-items centers inside the TRACK and the
     slide drifts off the viewport. translate(-50%,-50%) then scale is stable. */
  .slide > section {{
    position:absolute; left:50%; top:50%; width:1920px; height:1080px; overflow:hidden;
    transform-origin:center center; box-shadow:0 24px 80px rgba(0,0,0,.55);
  }}
  .slide > section > aside {{ display:none; }}
  #bar {{
    position:fixed; left:0; right:0; bottom:0; height:3px; background:rgba(255,255,255,.08);
  }}
  #bar > i {{ display:block; height:100%; background:#E0A526; width:0; transition:width .18s ease; }}
  #hud {{
    position:fixed; right:18px; bottom:16px; font-family:'Fira Code', ui-monospace, monospace;
    font-size:13px; color:#7C8890; letter-spacing:1px; user-select:none;
  }}
  #help {{
    position:fixed; left:18px; bottom:16px; font-family:'Fira Code', ui-monospace, monospace;
    font-size:12px; color:#4A545B; letter-spacing:.5px; user-select:none;
  }}
  #notes {{
    position:fixed; left:0; right:0; bottom:0; max-height:38vh; overflow:auto;
    background:#12181E; color:#C7D0D8; border-top:1px solid #26313A;
    padding:20px 26px 26px; font-size:16px; line-height:1.55; display:none;
  }}
  #notes.on {{ display:block; }}
  #notes b {{ display:block; color:#E0A526; font-family:'Fira Code', ui-monospace, monospace;
    font-size:12px; letter-spacing:1.5px; text-transform:uppercase; padding-bottom:6px; }}
  @media print {{
    html, body {{ background:#fff; overflow:visible; height:auto; }}
    #stage {{ position:static; display:block; }}
    #bar, #hud, #help, #notes {{ display:none !important; }}
    .slide {{ position:static; visibility:visible !important; page-break-after:always;
              display:block; width:1920px; height:1080px; }}
    .slide > section {{ box-shadow:none; transform:none !important;
                        position:relative; left:auto; top:auto; }}
    @page {{ size:1920px 1080px; margin:0; }}
  }}
</style>
</head>
<body>
<div id="stage">
{slides}
</div>
<div id="bar"><i></i></div>
<div id="hud"></div>
<div id="help">&larr; &rarr; move &nbsp;·&nbsp; S notes &nbsp;·&nbsp; F full screen</div>
<div id="notes"></div>
<script>
(function () {{
  var NOTES = {notes};
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var hud = document.getElementById('hud');
  var bar = document.querySelector('#bar > i');
  var notesEl = document.getElementById('notes');
  var i = 0, showNotes = false;

  function fit() {{
    var s = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    slides.forEach(function (el) {{
      el.firstElementChild.style.transform = 'translate(-50%, -50%) scale(' + s + ')';
    }});
  }}
  function render() {{
    slides.forEach(function (el, n) {{ el.classList.toggle('is-active', n === i); }});
    hud.textContent = (i + 1) + ' / ' + {count};
    bar.style.width = ((i + 1) / {count} * 100) + '%';
    notesEl.innerHTML = '';
    if (NOTES[i]) {{
      var b = document.createElement('b'); b.textContent = 'Speaker notes';
      var p = document.createElement('div'); p.textContent = NOTES[i];
      notesEl.appendChild(b); notesEl.appendChild(p);
    }}
    notesEl.classList.toggle('on', showNotes && !!NOTES[i]);
    if (location.hash.slice(1) !== String(i + 1)) {{
      history.replaceState(null, '', '#' + (i + 1));
    }}
  }}
  function go(n) {{ i = Math.max(0, Math.min({count} - 1, n)); render(); }}

  document.addEventListener('keydown', function (e) {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{ go(i + 1); e.preventDefault(); }}
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ go(i - 1); e.preventDefault(); }}
    else if (e.key === 'Home') {{ go(0); }}
    else if (e.key === 'End') {{ go({count} - 1); }}
    else if (e.key === 's' || e.key === 'S') {{ showNotes = !showNotes; render(); }}
    else if (e.key === 'f' || e.key === 'F') {{
      if (document.fullscreenElement) {{ document.exitFullscreen(); }}
      else {{ document.documentElement.requestFullscreen(); }}
    }}
  }});
  document.addEventListener('click', function (e) {{
    if (e.target.closest('#notes') || e.target.closest('a')) {{ return; }}
    go(e.clientX < window.innerWidth * 0.25 ? i - 1 : i + 1);
  }});
  window.addEventListener('resize', fit);

  var start = parseInt(location.hash.slice(1), 10);
  if (start > 0 && start <= {count}) {{ i = start - 1; }}
  fit(); render();
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
