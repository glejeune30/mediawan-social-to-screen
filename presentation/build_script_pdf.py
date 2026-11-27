"""Builds presentation/OTG1_speaker_script.pdf from OTG1_speaker_script.md.

Run:  python presentation/build_script_pdf.py                      (English script)
      python presentation/build_script_pdf.py SCRIPT.md OUT.pdf    (any script, e.g. the French one)
Needs the `markdown` package and Microsoft Edge (or Google Chrome), used to print the page to PDF.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SRC = HERE / "OTG1_speaker_script.md"
OUT = HERE / "OTG1_speaker_script.pdf"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

SPEAKERS = {"CHRISTINE": "#FF5A4E", "FIONA": "#5B3F8C", "GABIN": "#1F6F64", "GABRIEL": "#1F1A2E"}

CSS = """
@page { size: A4; margin: 16mm 17mm 16mm 17mm; }
* { box-sizing: border-box; }
body { font-family: Calibri, "Segoe UI", Arial, sans-serif; color: #1F1A2E; font-size: 12.5pt;
       line-height: 1.5; margin: 0; }
h1 { font-family: Cambria, Georgia, serif; font-size: 24pt; margin: 0 0 4pt; }
h2 { font-family: Cambria, Georgia, serif; font-size: 15pt; margin: 18pt 0 6pt; padding-top: 6pt;
     border-top: 1px solid #E4E0EC; break-after: avoid; page-break-after: avoid; }
h2:first-of-type { border-top: none; }
p { margin: 0 0 8pt; orphans: 3; widows: 3; }
strong { color: #1F1A2E; }
code { font-family: Consolas, monospace; font-size: 10pt; background: #F1EEF7; padding: 1pt 4pt;
       border-radius: 4pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 11pt;
        break-inside: avoid; }
th, td { text-align: left; padding: 5pt 8pt; border-bottom: 1px solid #E4E0EC; vertical-align: top; }
th { background: #F1EEF7; font-weight: 700; }
hr { border: none; height: 0; margin: 10pt 0; }
.who { display: inline-block; color: #fff; font-weight: 700; font-size: 9.5pt;
       letter-spacing: .04em; padding: 1pt 7pt; border-radius: 10pt; margin-right: 6pt;
       vertical-align: 1pt; text-transform: uppercase; }
.opt { color: #6B6680; font-style: italic; }
.kicker { color: #FF5A4E; font-weight: 700; font-size: 9.5pt; letter-spacing: .08em;
          text-transform: uppercase; }
.newpage { break-before: page; page-break-before: always; }
ol li, ul li { margin-bottom: 5pt; }
"""


def to_html(md_text: str) -> str:
    # speaker labels at the start of a paragraph: "CHRISTINE: ..." -> coloured chip
    def chip(m):
        name = m.group(1)
        return f'<span class="who" style="background:{SPEAKERS[name]}">{name.title()}</span>'
    md_text = re.sub(r"^(CHRISTINE|FIONA|GABIN|GABRIEL): ", chip, md_text, flags=re.M)
    # optional sentences in [brackets] (not links) -> muted italics
    md_text = re.sub(r"\[([^\]\n]+(?:\n[^\]\n]+)*)\](?!\()",
                     lambda m: f'<span class="opt">[{m.group(1)}]</span>', md_text)
    body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    body = body.replace("<h2>Version française", '<h2 class="newpage">Version française')
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>OTG1 speaker script, Team 21</title><style>{CSS}</style></head><body>"
            "<div class='kicker'>Business Deep Dive · Mediawan × Albert School · Team 21</div>"
            f"{body}</body></html>")


def main() -> None:
    import sys
    global OUT
    src = Path(sys.argv[1]) if len(sys.argv) > 2 else SRC
    if len(sys.argv) > 2:
        OUT = Path(sys.argv[2]).resolve()
    html = to_html(src.read_text(encoding="utf-8"))
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        raise SystemExit("Microsoft Edge or Google Chrome is needed to print the PDF.")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "script.html"
        page.write_text(html, encoding="utf-8")
        profile = Path(tmp) / "profile"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run",
                        f"--user-data-dir={profile}", "--no-pdf-header-footer",
                        "--print-to-pdf-no-header", f"--print-to-pdf={OUT}", page.as_uri()],
                       check=True, timeout=120)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
