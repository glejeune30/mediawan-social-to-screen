"""Turns a Markdown file into a clean A4 PDF (team colours), using Edge or Chrome to print.

Run:  python scripts/md_to_pdf.py docs/comment_ca_marche_FR.md docs/comment_ca_marche_FR.pdf
Needs the `markdown` package and Microsoft Edge (or Google Chrome).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

CSS = """
@page { size: A4; margin: 15mm 16mm 15mm 16mm; }
* { box-sizing: border-box; }
body { font-family: Calibri, "Segoe UI", Arial, sans-serif; color: #1F1A2E; font-size: 11.5pt;
       line-height: 1.48; margin: 0; }
.kicker { color: #FF5A4E; font-weight: 700; font-size: 9pt; letter-spacing: .08em;
          text-transform: uppercase; margin-bottom: 4pt; }
h1 { font-family: Cambria, Georgia, serif; font-size: 22pt; line-height: 1.15; margin: 0 0 6pt; }
h2 { font-family: Cambria, Georgia, serif; font-size: 15pt; margin: 16pt 0 6pt; padding-top: 6pt;
     border-top: 1px solid #E4E0EC; break-after: avoid; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 10pt 0 4pt; color: #5B3F8C; break-after: avoid; }
p { margin: 0 0 7pt; orphans: 3; widows: 3; }
ul { margin: 0 0 8pt 16pt; padding: 0; }
li { margin-bottom: 3pt; }
blockquote { margin: 8pt 0; padding: 9pt 12pt; background: #F1EEF7; border-radius: 8pt;
             font-size: 12.5pt; }
blockquote p { margin: 0; }
code { font-family: Consolas, monospace; font-size: 9.5pt; background: #F1EEF7; padding: 1pt 4pt;
       border-radius: 4pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt; font-size: 10.5pt;
        break-inside: avoid; }
th, td { text-align: left; padding: 5pt 7pt; border-bottom: 1px solid #E4E0EC; vertical-align: top; }
th { background: #F1EEF7; font-weight: 700; }
em { color: #6B6680; }
strong { color: #1F1A2E; }
"""


def convert(src: Path, out: Path, kicker: str = "Business Deep Dive · Mediawan × Albert School · Team 21") -> None:
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"])
    title = src.stem.replace("_", " ")
    html = ("<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
            f"<title>{title}</title><style>{CSS}</style></head><body>"
            f"<div class='kicker'>{kicker}</div>{body}</body></html>")
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        raise SystemExit("Microsoft Edge or Google Chrome is needed to print the PDF.")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run",
                        f"--user-data-dir={Path(tmp) / 'profile'}", "--no-pdf-header-footer",
                        "--print-to-pdf-no-header", f"--print-to-pdf={out.resolve()}",
                        page.as_uri()], check=True, timeout=120)
    print(f"saved {out}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: python scripts/md_to_pdf.py input.md output.pdf")
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
