"""Puts the prototype screenshots into one PDF (an email-safe version of the interface).

Run:  python scripts/export_screenshots_pdf.py
Input:  presentation/assets/{prototype,radar_map,story,backtest}.png
Output: exports/story_radar_screenshots.pdf
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "presentation" / "assets"
OUT = ROOT / "exports" / "story_radar_screenshots.pdf"
PAGES = ["prototype.png", "radar_map.png", "story.png", "backtest.png"]

images = []
for name in PAGES:
    path = ASSETS / name
    if path.exists():
        img = Image.open(path).convert("RGB")
        img.thumbnail((2000, 2000))          # keeps the PDF small enough for email
        images.append(img)
OUT.parent.mkdir(exist_ok=True)
images[0].save(OUT, save_all=True, append_images=images[1:], resolution=150, quality=88)
print(f"saved {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {len(images)} pages)")
