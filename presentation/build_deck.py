"""Builds presentation/OTG1_deck.pptx (On the Grill 1, 27 Nov 2026).

Run:  python presentation/build_deck.py
The evidence slide reads data/processed/backtest_results.csv, so rerun this script after
scripts/run_poc.py to refresh the numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "presentation" / "OTG1_deck.pptx"
RESULTS = ROOT / "data" / "processed" / "backtest_results.csv"

# ---------- palette: "screening room" ink + coral radar ping ----------
INK = RGBColor(0x1F, 0x1A, 0x2E)       # dominant dark (title / closing slides, text)
PLUM = RGBColor(0x5B, 0x3F, 0x8C)      # secondary
LILAC = RGBColor(0xEE, 0xEA, 0xF5)     # card tint on white
CORAL = RGBColor(0xFF, 0x5A, 0x4E)     # single sharp accent: the radar alert
MUTED = RGBColor(0x6B, 0x66, 0x80)     # captions
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xB9, 0xB2, 0xCC)      # light text on dark
GRID = RGBColor(0xD9, 0xD5, 0xE3)

HEAD = "Cambria"
BODY = "Calibri"

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.6)

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]


# ---------- helpers ----------
def bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def text(slide, x, y, w, h, runs, size=16, color=INK, font=BODY, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, name=None, space_after=0):
    """runs: str, or list of paragraphs; a paragraph is str or list of (text, {opts})."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paragraphs = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        pieces = para if isinstance(para, list) else [(para, {})]
        for t, o in pieces:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = o.get("color", color)
    return tb


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None, name=None,
        radius=0.08):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    if name:
        s.name = name
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.25)
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def ring(slide, cx, cy, r, color, width=1.5, name=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - r, cy - r, 2 * r, 2 * r)
    s.fill.background()
    s.line.color.rgb = color
    s.line.width = Pt(width)
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def dot(slide, cx, cy, r, color, name=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - r, cy - r, 2 * r, 2 * r)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def numbered(slide, cx, cy, n, color=CORAL, r=Inches(0.28)):
    """Motif: a radar ping (number in a coral disc with a faint ring)."""
    ring(slide, cx, cy, int(r * 1.45), color, width=1)
    d = dot(slide, cx, cy, r, color)
    tf = d.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(n)
    run.font.name = BODY
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = WHITE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return d


def title(slide, t, color=INK):
    text(slide, MARGIN, Inches(0.5), W - 2 * MARGIN, Inches(1.0), t, size=34, font=HEAD,
         bold=True, color=color, anchor=MSO_ANCHOR.TOP, name="Title")


def footer(slide, n, dark=False):
    c = SOFT if dark else MUTED
    text(slide, MARGIN, H - Inches(0.45), Inches(8), Inches(0.3),
         "From Social to Screen  ·  Mediawan × Albert School  ·  On the Grill 1", size=10, color=c,
         name="Footer")
    text(slide, W - MARGIN - Inches(1), H - Inches(0.45), Inches(1), Inches(0.3), str(n),
         size=10, color=c, align=PP_ALIGN.RIGHT, name="Slide number")


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def fmt_months(v: float) -> str:
    return f"{v:.0f}" if v >= 10 else f"{v:.1f}"


# ---------- data for the evidence slide ----------
res = pd.read_csv(RESULTS, parse_dates=["announcement_date", "radar_alert"]) \
    if RESULTS.exists() else None

# =====================================================================
# 1. Title (dark)
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, INK)
cx, cy = W - Inches(3.2), Inches(3.6)
for i, r in enumerate([2.6, 1.95, 1.3, 0.65]):
    ring(s, cx, cy, Inches(r), PLUM if i < 3 else CORAL, width=1.25, name=f"Radar ring {i+1}")
dot(s, cx + Inches(1.05), cy - Inches(0.95), Inches(0.13), CORAL, name="Radar ping")
ring(s, cx + Inches(1.05), cy - Inches(0.95), Inches(0.28), CORAL, width=1, name="Ping halo")
dot(s, cx - Inches(1.5), cy + Inches(0.6), Inches(0.07), SOFT, name="Radar blip 1")
dot(s, cx + Inches(0.3), cy + Inches(1.6), Inches(0.07), SOFT, name="Radar blip 2")
dot(s, cx - Inches(0.6), cy - Inches(1.9), Inches(0.07), SOFT, name="Radar blip 3")

text(s, MARGIN, Inches(1.1), Inches(7.6), Inches(0.4), "BUSINESS DEEP DIVE  ·  MEDIAWAN × ALBERT SCHOOL",
     size=12, color=CORAL, bold=True)
text(s, MARGIN, Inches(1.6), Inches(7.0), Inches(2.0), ["From Social", "to Screen"], size=58,
     font=HEAD, bold=True, color=WHITE, name="Title")
text(s, MARGIN, Inches(3.75), Inches(6.6), Inches(1.2),
     "An early-warning radar that spots the next adaptable story while its rights are still affordable",
     size=22, color=SOFT)
text(s, MARGIN, Inches(5.6), Inches(7.2), Inches(0.9),
     ["On the Grill 1  ·  27 November 2026  ·  Team 21",
      "Christine Durand, Fiona Loison, Gabin Dupre Duval, Gabriel Lejeune"],
     size=14, color=SOFT, space_after=4)
notes(s, "Hello, we are [team]. In the next five minutes: the problem we chose, the decision our "
         "radar helps Mediawan make, and a first test on real adaptations.")

# =====================================================================
# 2. Problem (light): stat callouts
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "By the time a story is mainstream, its rights are gone")
text(s, MARGIN, Inches(1.45), Inches(11.5), Inches(0.6),
     "Stories now break in online communities first: BookTok, BookTube, Reddit, Webtoon, Wattpad.",
     size=18, color=MUTED)

cards = [
    ("5 months", "Fourth Wing",
     "between the novel's release (May 2023) and Amazon MGM Studios developing the series (Oct 2023)."),
    ("0 pages", "Heartstopper",
     "on English Wikipedia when Netflix ordered the series (20 Jan 2021). The first one appeared a week later."),
    ("4 years", "Solo Leveling",
     "of growing global fandom for the webtoon (2018) before the anime was announced (July 2022)."),
]
cw, ch, gap = Inches(3.85), Inches(3.3), Inches(0.3)
x0, y0 = MARGIN, Inches(2.4)
for i, (big, who, desc) in enumerate(cards):
    x = x0 + i * (cw + gap)
    box(s, x, y0, cw, ch, LILAC, name=f"Card {who}")
    text(s, x + Inches(0.35), y0 + Inches(0.35), cw - Inches(0.5), Inches(1.1), big, size=46,
         font=HEAD, bold=True, color=CORAL if i == 1 else INK)
    text(s, x + Inches(0.35), y0 + Inches(1.55), cw - Inches(0.7), Inches(0.45), who, size=18,
         bold=True, color=INK)
    text(s, x + Inches(0.35), y0 + Inches(2.05), cw - Inches(0.7), Inches(1.4), desc, size=15,
         color=INK)
text(s, MARGIN, Inches(5.95), Inches(12), Inches(0.4),
     "Sources: Amazon MGM / Deadline (Oct 2023), Netflix (20 Jan 2021), Crunchyroll at Anime Expo "
     "(3 Jul 2022), Wikipedia page history.", size=10, color=MUTED, italic=True)
footer(s, 2)
notes(s, "Stories are now born online. Fourth Wing: five months from release to a TV deal. "
         "Heartstopper: when Netflix ordered it, it did not even have a Wikipedia page, so a "
         "mainstream tool would have missed it. Solo Leveling: four years of fandom before the "
         "anime. The window to option a story is short, and it opens in communities, not in charts.")

# =====================================================================
# 3. Decision (light): three statuses
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "One question for Mediawan's development teams")
box(s, MARGIN, Inches(1.5), W - 2 * MARGIN, Inches(1.25), INK, name="Question banner")
text(s, MARGIN + Inches(0.45), Inches(1.5), W - 2 * MARGIN - Inches(0.9), Inches(1.25),
     "“Which book or webtoon should we look at, and option, this quarter, "
     "before its rights become expensive?”", size=24, font=HEAD, italic=True, color=WHITE,
     anchor=MSO_ANCHOR.MIDDLE)

statuses = [
    ("Watch", "Early buzz in one community.", "Keep it on the list.", SOFT),
    ("Prepare", "Accelerating and spreading.", "Read it, check who holds the rights.", PLUM),
    ("Act now", "Strong growth while the mainstream is still unaware.",
     "Contact the rights holder.", CORAL),
]
cw, gap = Inches(3.85), Inches(0.3)
y0 = Inches(3.15)
for i, (name, what, act, c) in enumerate(statuses):
    x = MARGIN + i * (cw + gap)
    box(s, x, y0, cw, Inches(2.35), LILAC, name=f"Status {name}")
    dot(s, x + Inches(0.55), y0 + Inches(0.55), Inches(0.17), c)
    text(s, x + Inches(0.9), y0 + Inches(0.32), cw - Inches(1.2), Inches(0.5), name, size=22,
         bold=True, color=INK)
    text(s, x + Inches(0.35), y0 + Inches(1.0), cw - Inches(0.7), Inches(0.6), what, size=15,
         color=INK)
    text(s, x + Inches(0.35), y0 + Inches(1.65), cw - Inches(0.7), Inches(0.6), act, size=15,
         bold=True, color=PLUM)
text(s, MARGIN, Inches(5.85), W - 2 * MARGIN, Inches(0.8),
     [[("Scope: ", {"bold": True}),
       ("books and webtoons with screen potential (YA, romantasy, fantasy, thriller, manhwa), "
        "English-speaking communities first, any country of origin. A weekly watchlist.", {})]],
     size=15, color=INK)
footer(s, 3)
notes(s, "Our radar answers one business question: which story should the development teams of "
         "Mediawan's labels look at and option this quarter, before the price goes up. Every week, "
         "each story gets a status: Watch, Prepare, or Act now. We focus on books and webtoons "
         "because Mediawan adapts both in fiction and animation, and because an option is a "
         "concrete, costly decision.")

# =====================================================================
# 4. Gap in existing tools (light): 2x2 + verdict
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Existing tools see topics, not stories")
tools = [
    ("Google Trends", "Sees a story once millions search for it: too late."),
    ("Exploding Topics, Glimpse", "Fast-growing keywords and products, not stories or rights."),
    ("TikTok Creative Center", "Hashtags and sounds on one platform, built for advertisers."),
    ("Parrot Analytics", "Demand for shows already on screen, not for source material."),
]
cw, chh, gx, gy = Inches(3.75), Inches(1.95), Inches(0.3), Inches(0.3)
x0, y0 = MARGIN, Inches(1.6)
for i, (name, miss) in enumerate(tools):
    x = x0 + (i % 2) * (cw + gx)
    y = y0 + (i // 2) * (chh + gy)
    box(s, x, y, cw, chh, LILAC, name=f"Tool {name}")
    text(s, x + Inches(0.3), y + Inches(0.3), cw - Inches(0.6), Inches(0.5), name, size=18,
         bold=True, color=INK)
    text(s, x + Inches(0.3), y + Inches(0.85), cw - Inches(0.6), Inches(1.0), miss, size=15,
         color=INK)
vx = x0 + 2 * cw + gx + Inches(0.45)
vw = W - MARGIN - vx
box(s, vx, y0, vw, 2 * chh + gy, INK, name="Our angle")
text(s, vx + Inches(0.4), y0 + Inches(0.4), vw - Inches(0.8), Inches(0.5), "OUR ANGLE", size=12,
     bold=True, color=CORAL)
text(s, vx + Inches(0.4), y0 + Inches(0.9), vw - Inches(0.8), Inches(3.0),
     [[("One score per story", {"bold": True, "color": WHITE})],
      [("across several communities,", {"color": SOFT})],
      [("timed to the rights window", {"bold": True, "color": WHITE})],
      [("and tested against real deals.", {"color": SOFT})]],
     size=20, space_after=6)
footer(s, 4)
notes(s, "We looked at what already exists. Google Trends is free but sees a story when it is "
         "already huge. Exploding Topics and Glimpse track keywords and products. TikTok Creative "
         "Center tracks hashtags on one platform. Parrot Analytics measures demand for shows that "
         "already exist. None of them gives one score per story, across communities, timed to the "
         "moment an option is still cheap. That is our angle.")

# =====================================================================
# 5. How the radar works (light): 3 questions -> status, sources
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
title(s, "Three questions, asked every week for every story")
qs = [
    ("Is the buzz accelerating?", "Recent months compared with the months before."),
    ("Is it spreading?", "Growing in several communities, not just one."),
    ("Is the mainstream still unaware?", "Niche buzz grows faster than Google searches."),
]
y0 = Inches(1.65)
for i, (q, d) in enumerate(qs):
    y = y0 + i * Inches(1.05)
    numbered(s, MARGIN + Inches(0.35), y + Inches(0.35), i + 1)
    text(s, MARGIN + Inches(0.95), y + Inches(0.02), Inches(5.6), Inches(0.45), q, size=20,
         bold=True, color=INK)
    text(s, MARGIN + Inches(0.95), y + Inches(0.47), Inches(5.6), Inches(0.4), d, size=15,
         color=MUTED)
# arrow to status
ax = MARGIN + Inches(6.7)
arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, ax, Inches(2.6), Inches(0.7), Inches(0.5))
arrow.fill.solid()
arrow.fill.fore_color.rgb = CORAL
arrow.line.fill.background()
arrow.name = "Arrow to score"
sx = ax + Inches(0.95)
box(s, sx, Inches(1.95), W - MARGIN - sx, Inches(1.8), INK, name="Score card")
text(s, sx + Inches(0.4), Inches(2.2), Inches(4), Inches(0.4), "EMERGENCE SCORE", size=12,
     bold=True, color=CORAL)
text(s, sx + Inches(0.4), Inches(2.6), Inches(4.2), Inches(1.0),
     [[("0 to 100 per story", {"bold": True, "color": WHITE, "size": 22})],
      [("Watch  ·  Prepare  ·  Act now", {"color": SOFT, "size": 18})]], space_after=8)

# sources band
y1 = Inches(4.75)
box(s, MARGIN, y1, W - 2 * MARGIN, Inches(1.85), LILAC, name="Sources band")
text(s, MARGIN + Inches(0.4), y1 + Inches(0.25), Inches(6), Inches(0.4),
     "EARLY SIGNALS  (where stories are born)", size=12, bold=True, color=PLUM)
text(s, MARGIN + Inches(0.4), y1 + Inches(0.7), Inches(6.2), Inches(1.0),
     ["YouTube: BookTube and webtoon reviewers", "Reddit: fan communities",
      [("AniList and Open Library: fans and readers ", {}),
       ("(live in our prototype)", {"bold": True, "color": CORAL})]],
     size=15, color=INK, space_after=2)
text(s, MARGIN + Inches(7.0), y1 + Inches(0.25), Inches(5), Inches(0.4),
     "MAINSTREAM GAUGE  (who already knows)", size=12, bold=True, color=PLUM)
text(s, MARGIN + Inches(7.0), y1 + Inches(0.7), Inches(4.9), Inches(1.0),
     ["Google Trends: search interest", "Wikipedia: pageviews",
      "Public data only, official APIs, no personal data"], size=15, color=INK, space_after=2)
footer(s, 5)
notes(s, "How does it work, without the technical detail? Every week, for every story, the radar "
         "asks three questions. Is the buzz accelerating? Is it spreading across communities? And "
         "is the mainstream still unaware? The answers make a score from 0 to 100 and a status. We "
         "listen where stories are born, YouTube, Reddit, Webtoon and Wattpad charts, and we "
         "compare with a mainstream gauge, Google Trends and Wikipedia. Public data only.")

# =====================================================================
# 6. Evidence (light): timeline of alerts vs deals (from the backtest)
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, WHITE)
flagged = res[res["lead_months"].notna()] if res is not None else None
if flagged is not None and len(flagged):
    title(s, f"First test: {len(flagged)} of {len(res)} stories flagged before the deal")
    lo, hi = flagged["lead_months"].min(), flagged["lead_months"].max()
    summ_path = ROOT / "data" / "processed" / "backtest_summary.json"
    summ = json.loads(summ_path.read_text(encoding="utf-8")) if summ_path.exists() else None
    sub = f"{fmt_months(lo)} to {fmt_months(hi)} months of warning"
    if summ:
        sub += (f", but alone it also fires for {summ['controls_flagged']} of "
                f"{summ['controls_total']} popular stories never adapted")
    text(s, MARGIN, Inches(1.3), W - 2 * MARGIN, Inches(0.45), sub, size=18, color=MUTED)
else:
    title(s, "First test: alerts versus deal announcements")

# time axis
t0, t1 = pd.Timestamp("2018-01-01"), pd.Timestamp("2024-01-01")
ax_x, ax_w = MARGIN + Inches(3.0), Inches(6.4)
y_top = Inches(2.15)
row_h = Inches(0.85)


def tx(d):
    d = pd.Timestamp(d)
    return int(ax_x + ax_w * ((d - t0) / (t1 - t0)))


for yr in range(2018, 2025):
    x = tx(f"{yr}-01-01")
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, y_top - Inches(0.15), x,
                                y_top + 4 * row_h)
    ln.line.color.rgb = GRID
    ln.line.width = Pt(0.75)
    text(s, x - Inches(0.4), y_top + 4 * row_h + Inches(0.05), Inches(0.8), Inches(0.3), str(yr),
         size=11, color=MUTED, align=PP_ALIGN.CENTER)

if res is not None:
    for i, r in res.reset_index(drop=True).iterrows():
        y = y_top + i * row_h + Inches(0.3)
        text(s, MARGIN, y - Inches(0.2), Inches(2.85), Inches(0.4), r["title"], size=15,
             bold=True, color=INK, anchor=MSO_ANCHOR.MIDDLE)
        deal_x = tx(r["announcement_date"])
        if pd.notna(r["radar_alert"]):
            al_x = tx(r["radar_alert"])
            box(s, al_x, y - Inches(0.06), max(deal_x - al_x, Inches(0.05)), Inches(0.12),
                CORAL, shape=MSO_SHAPE.RECTANGLE, name=f"Window {r['title']}")
            dot(s, al_x, y, Inches(0.13), CORAL, name=f"Alert {r['title']}")
        if pd.notna(r.get("first_wikipedia_page")):
            wx = tx(r["first_wikipedia_page"])
            wk = dot(s, wx, y, Inches(0.16), WHITE, name=f"Wikipedia {r['title']}")
            wk.line.color.rgb = PLUM
            wk.line.width = Pt(2.25)
        dot(s, deal_x, y, Inches(0.13), INK, name=f"Deal {r['title']}")
        if pd.notna(r["lead_months"]):
            lead, lc, lb = f"{fmt_months(r['lead_months'])} months early", CORAL, True
        else:
            lead, lc, lb = "Missed: slow burner", MUTED, False
        text(s, ax_x + ax_w + Inches(0.3), y - Inches(0.2), Inches(2.7), Inches(0.4), lead,
             size=15, bold=lb, color=lc, anchor=MSO_ANCHOR.MIDDLE)

# legend
ly = y_top + 4 * row_h + Inches(0.5)
dot(s, MARGIN + Inches(0.12), ly + Inches(0.14), Inches(0.1), CORAL)
text(s, MARGIN + Inches(0.35), ly, Inches(2), Inches(0.3), "Radar alert", size=12, color=INK)
lg = dot(s, MARGIN + Inches(2.0), ly + Inches(0.14), Inches(0.1), WHITE)
lg.line.color.rgb = PLUM
lg.line.width = Pt(2)
text(s, MARGIN + Inches(2.23), ly, Inches(2.6), Inches(0.3), "First Wikipedia page", size=12,
     color=INK)
dot(s, MARGIN + Inches(4.4), ly + Inches(0.14), Inches(0.1), INK)
text(s, MARGIN + Inches(4.63), ly, Inches(3.5), Inches(0.3), "Adaptation deal announced",
     size=12, color=INK)
text(s, MARGIN, ly + Inches(0.4), W - 2 * MARGIN, Inches(0.5),
     "One rule, fixed in advance: Google searches over 3 months at least double the 6 months before, "
     "two months in a row. Control group: 16 popular stories with no adaptation listed, chosen before "
     "looking at their curves; 4 had in fact been optioned (e.g. Netflix's Twisted deal, flagged "
     "about 3 years earlier).",
     size=11, color=MUTED, italic=True)
footer(s, 6)
notes(s, "We ran a first test with free data only, on four real adaptations. The rule is simple "
         "and fixed in advance: Google searches for the title double compared with the previous "
         "six months, two months in a row. Coral is when the radar would have raised the alert. "
         "Dark is when the deal was announced. For Solo Leveling and A Good Girl's Guide to "
         "Murder, the alert came before the story even had a Wikipedia page. Heartstopper was "
         "missed: it grew tenfold between 2018 and 2020, but slowly, never doubling in a few "
         "months. That tells us two things: we need an indicator for slow, steady growth, and we "
         "need the community sources. And to be honest about the limits, these are known "
         "successes. Next we test titles that buzzed but were never adapted, to count false "
         "alarms.")

# =====================================================================
# 7. Next steps + asks (dark)
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg(s, INK)
title(s, "Next: from a test to a weekly watchlist", color=WHITE)
colw = Inches(5.7)
text(s, MARGIN, Inches(1.6), colw, Inches(0.4), "BEFORE ON THE GRILL 2  ·  4 DECEMBER", size=12,
     bold=True, color=CORAL)
steps = ["Add the early signals: YouTube and Reddit",
         "Cut false alarms: combine the three questions, test on the same control group",
         "Tune our prototype, already live on public data, with your feedback"]
for i, st in enumerate(steps):
    y = Inches(2.2) + i * Inches(1.0)
    numbered(s, MARGIN + Inches(0.3), y + Inches(0.3), i + 1)
    text(s, MARGIN + Inches(0.85), y, colw - Inches(0.9), Inches(0.7), st, size=18, color=WHITE,
         anchor=MSO_ANCHOR.MIDDLE)
qx = MARGIN + colw + Inches(0.6)
qw = W - MARGIN - qx
box(s, qx, Inches(1.6), qw, Inches(3.75), PLUM, name="Questions for the jury")
text(s, qx + Inches(0.4), Inches(1.9), qw - Inches(0.8), Inches(0.4), "WHAT WE NEED FROM YOU",
     size=12, bold=True, color=WHITE)
text(s, qx + Inches(0.4), Inches(2.45), qw - Inches(0.8), Inches(3.6),
     ["Which genres and formats matter most to your labels right now?",
      "How many months of warning do your teams need to option a story?",
      "One or two past deals, won or lost, we could test against?"],
     size=18, color=WHITE, space_after=14)
footer(s, 7, dark=True)
notes(s, "Before On the Grill 2 we will add YouTube and Reddit, test on titles that were never "
         "adapted, and turn this into a weekly watchlist you can filter. To make it useful for "
         "you, we need three answers: which genres matter most, how much warning your teams need, "
         "and a past deal we could test against. Thank you.")

# =====================================================================
# 8. Backup (light): the prototype, shown only if the jury asks
# =====================================================================
SHOT = ROOT / "presentation" / "assets" / "prototype.png"
if SHOT.exists():
    import json as _json
    from PIL import Image

    s = prs.slides.add_slide(BLANK)
    bg(s, WHITE)
    text(s, MARGIN, Inches(0.25), Inches(6), Inches(0.35), "BACKUP  ·  ONLY IF ASKED", size=12,
         bold=True, color=CORAL)
    title(s, "What the user sees: our prototype, live on public data")
    meta_path = ROOT / "data" / "processed" / "watchlist_meta.json"
    meta = _json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    # screenshot, scaled to fit the area under the title
    area_x, area_y, area_w, area_h = MARGIN, Inches(1.45), Inches(8.3), Inches(5.2)
    with Image.open(SHOT) as im:
        ratio = im.width / im.height
    w = min(area_w, int(area_h * ratio))
    h = int(w / ratio)
    frame = box(s, area_x - Inches(0.06), area_y - Inches(0.06), w + Inches(0.12),
                h + Inches(0.12), LILAC, name="Screenshot frame", radius=0.03)
    pic = s.shapes.add_picture(str(SHOT), area_x, area_y, width=w, height=h)
    pic.name = "Prototype screenshot"
    cx = area_x + w + Inches(0.5)
    cw2 = W - MARGIN - cx
    counts = meta.get("status_counts", {})
    facts = [
        (str(meta.get("stories", "—")), "stories tracked this week"),
        (str(counts.get("Act now", "—")), "to act on now"),
        (str(counts.get("Prepare", "—")), "to prepare"),
    ]
    for i, (big, small) in enumerate(facts):
        y = area_y + i * Inches(1.25)
        text(s, cx, y, cw2, Inches(0.7), big, size=36, font=HEAD, bold=True,
             color=CORAL if i == 1 else INK)
        text(s, cx, y + Inches(0.68), cw2, Inches(0.4), small, size=14, color=MUTED)
    text(s, cx, area_y + Inches(3.85), cw2, Inches(1.4),
         ["Each story: a status, a score and the reasons.",
          "Sources: AniList, Open Library, Wikipedia."],
         size=14, color=INK, space_after=6)
    footer(s, 8)

# Speaker notes: taken from the script so the deck and the script never disagree.
SCRIPT = ROOT / "presentation" / "OTG1_speaker_script.md"
if SCRIPT.exists():
    english = SCRIPT.read_text(encoding="utf-8").split("## Version française")[0]
    # only the numbered sections ("## 1. ...") are slide notes
    sections = [s for s in english.split("\n## ")[1:] if s[:1].isdigit()]
    for slide, sec in zip(prs.slides, sections):
        body = sec.split("\n", 1)[1].replace("---", "").strip()
        notes(slide, " ".join(line.strip() for line in body.splitlines()).replace("  ", "\n\n"))

prs.save(OUT)
print(f"saved {OUT}")
