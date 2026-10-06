#!/usr/bin/env python3
"""Takes this machine's paths, and a real phone's id, out of a run's
evidence: the repository's own path becomes relative and the home directory
"~", and each --redact ID=LABEL replaces a device id with a label, in the
transcript, the summary, the reports and inside each trace. Evidence goes
into a repository others read: an absolute path names whoever recorded it,
and a phone's UDID or serial names the phone.

    scripts/scrub.py evidence/<run> [...] [--redact ID=LABEL ...]
"""
import pathlib
import sys
import zipfile

ROOT = str(pathlib.Path(__file__).resolve().parent.parent) + "/"
HOME = str(pathlib.Path.home())
TEXT = {".md", ".json", ".html", ".txt", ".trace", ".network", ".xml", ".js"}


REDACT = {}


def clean(text):
    text = text.replace(ROOT, "").replace(HOME, "~")
    for device, label in REDACT.items():
        text = text.replace(device, label)
    return text


def scrub_zip(path):
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    changed = False
    out = []
    for info, data in items:
        if pathlib.Path(info.filename).suffix in TEXT:
            new = clean(data.decode("utf-8", "replace")).encode()
            changed |= new != data
            data = new
        out.append((info, data))
    if changed:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for info, data in out:
                z.writestr(info, data)
    return changed


def main(runs):
    n = 0
    for run in map(pathlib.Path, runs):
        for f in run.rglob("*"):
            if f.is_dir():
                continue
            if f.suffix == ".zip":
                n += scrub_zip(f)
            elif f.suffix in TEXT or f.name.startswith(".last-run"):
                text = f.read_text(errors="replace")
                if clean(text) != text:
                    f.write_text(clean(text))
                    n += 1
    print(f"scrubbed {n} files")


args, runs = sys.argv[1:], []
while args:
    a = args.pop(0)
    if a == "--redact":
        device, _, label = args.pop(0).partition("=")
        REDACT[device] = label
    else:
        runs.append(a)
main(runs)
