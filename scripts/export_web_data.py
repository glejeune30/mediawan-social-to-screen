"""Exports everything the web interface needs into web/data/radar.json.

Run:  python scripts/export_web_data.py      (run_watchlist.py calls it after each refresh too)

The interface recomputes scores and statuses itself (so its settings can change them live). It
receives the raw signals of every story, plus the Python result as a reference ("py").
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radar.config import RAW, PROCESSED  # noqa: E402
from radar.watchlist import clean_books, revalidate, score  # noqa: E402

OUT = ROOT / "web" / "data" / "radar.json"


def clean(v):
    """JSON-safe value: NaN -> None, infinity -> 999 (a page that did not exist 6 months ago)."""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        if math.isinf(v):
            return 999.0
        # 9 decimals: rounding harder can turn close signals into ties and shift percentile ranks
        return round(v, 9)
    if hasattr(v, "item"):          # numpy scalars
        return clean(v.item())
    return v


def main() -> None:
    raw = pd.read_csv(RAW / "watchlist_raw.csv").drop_duplicates("story_id")
    raw["adaptation"] = raw["adaptation"].where(raw["adaptation"].notna(), None)
    raw["wiki_adapted"] = raw["wiki_adapted"].fillna(False).astype(bool)
    stories = clean_books(revalidate(raw))
    ref = score(stories).set_index("story_id")

    series = pd.read_csv(PROCESSED / "watchlist_series.csv")
    out_stories = []
    for r in stories.itertuples():
        p = ref.loc[r.story_id]
        wiki = r.wiki_article if isinstance(r.wiki_article, str) else None
        out_stories.append({
            "id": r.story_id,
            "title": r.title,
            "author": r.author if isinstance(r.author, str) else "",
            "format": r.format,
            "year": None if pd.isna(r.year) else int(r.year),
            "genres": [g.strip() for g in str(r.genres).split(",") if g.strip() and str(r.genres) != "nan"],
            "cover": r.cover_url if isinstance(r.cover_url, str) else None,
            "src": r.source_url,
            "wikiArticle": wiki,
            "wikiUrl": f"https://en.wikipedia.org/wiki/{wiki.replace(' ', '_')}" if wiki else None,
            "adapted": p["status"] == "Already adapted",
            "adaptation": p["adaptation"] if isinstance(p["adaptation"], str) else None,
            "s": {k: clean(getattr(r, c)) for k, c in [
                ("growth90d", "growth_90d"), ("fansNow", "fans_now"), ("trending", "trending"),
                ("accelSignal", "accel_signal"), ("activityNow", "activity_now"),
                ("last24h", "last_24h"), ("prevDaysAvg", "previous_days_avg"),
                ("trendingZ", "trending_z"), ("readers", "readers"), ("wantToRead", "want_to_read"),
                ("wikiViews", "wiki_views_month"), ("wikiMomentum", "wiki_momentum"),
                ("wikiAgeMonths", "wiki_page_age_months")]},
            "py": {"score": clean(p["score"]), "status": p["status"], "accel": clean(p["accel"]),
                   "unaware": clean(p["unaware"]), "spreading": clean(p["spreading"])},
        })

    ids = {s["id"] for s in out_stories}
    ser: dict[str, dict[str, list]] = {}
    for r in series[series["story_id"].isin(ids)].itertuples():
        ser.setdefault(r.story_id, {}).setdefault(r.kind, []).append([r.x, clean(float(r.value))])
    for kinds in ser.values():
        for k, pts in kinds.items():
            if k != "reader_activity":
                pts.sort(key=lambda p: p[0])

    bt = pd.read_csv(PROCESSED / "backtest_results.csv")
    ctrl = pd.read_csv(PROCESSED / "control_results.csv")
    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "meta": json.loads((PROCESSED / "watchlist_meta.json").read_text(encoding="utf-8")),
        "stories": out_stories,
        "series": ser,
        "backtest": [{k: clean(v) for k, v in row.items()} for row in bt.to_dict("records")],
        "controls": [{k: clean(v) for k, v in row.items()} for row in ctrl[[
            "title", "format", "popularity", "radar_alert", "months_after_publication",
            "verdict", "deal", "source_url"]].to_dict("records")],
        "summary": json.loads((PROCESSED / "backtest_summary.json").read_text(encoding="utf-8")),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = pd.Series([s["py"]["status"] for s in out_stories]).value_counts().to_dict()
    print(f"saved {OUT} ({OUT.stat().st_size / 1e3:.0f} kB, {len(out_stories)} stories, {counts})")


if __name__ == "__main__":
    main()
