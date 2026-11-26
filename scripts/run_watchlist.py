"""Builds this week's watchlist from live public data (no API key needed). About 5 minutes.

Run:  python scripts/run_watchlist.py            collect + score
      python scripts/run_watchlist.py --offline  re-score the last collection (no internet)

Sources: AniList (webtoon fans), Open Library (book readers), Wikipedia (mainstream gauge).
Raw collection (data/raw):
  watchlist_raw.csv               one line per story with its raw signals
  watchlist_history.csv           small time series (AniList fans, Wikipedia views)
  watchlist_raw_meta.json         collection date
Outputs (data/processed):
  watchlist.csv                   one line per story: signals, score, status, reasons
  watchlist_series.csv            time series for the story pages of the app
  watchlist_meta.json             snapshot date and counts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radar.config import PROCESSED, RAW  # noqa: E402
from radar.sources import anilist, openlibrary  # noqa: E402
from radar.watchlist import (resolve_wikipedia, wikipedia_views, wikipedia_metrics,  # noqa: E402
                             score, clean_books, revalidate)

KEEP = ["story_id", "format", "title", "author", "year", "genres", "status", "score",
        "accel", "unaware", "spreading", "fan_signal", "mainstream", "adaptation", "why",
        "cover_url", "source_url", "wiki_article", "wiki_description", "wiki_views_month",
        "wiki_momentum",
        "wiki_page_age_months", "fans_now", "growth_90d", "trending", "readers",
        "want_to_read", "last_24h", "previous_days_avg", "trending_z", "publication_status"]


def collect(n_webtoons: int = 60, books_per_genre: int = 40):
    today = pd.Timestamp.today().normalize()
    last_month = (today.to_period("M") - 1).start_time   # last complete month

    print("1/4 AniList: trending webtoons", flush=True)
    web = anilist.trending_webtoons(n_webtoons)
    hist = anilist.popularity_history(web["source_id"].tolist())
    past90 = hist[hist.days_ago == 90].set_index("source_id")["fans"]
    web["growth_90d"] = web["fans_now"] / web["source_id"].map(past90) - 1
    web["accel_signal"] = web["growth_90d"]       # acceleration: fan growth over 90 days
    web["activity_now"] = web["trending"]         # volume: AniList activity right now
    web["format"] = "Webtoon"
    web["story_id"] = "al-" + web["source_id"].astype(str)

    print("2/4 Open Library: trending recent fiction", flush=True)
    books = openlibrary.trending_books(per_genre=books_per_genre)
    books["accel_signal"] = books["trending_z"]   # acceleration: last 24 h vs previous week
    books["activity_now"] = books["last_24h"]     # volume: reader logs in the last 24 h
    books["format"] = "Book"
    books["story_id"] = "ol-" + books["source_id"].str.replace("/works/", "", regex=False)

    # AniList pages can overlap when the ranking moves during collection: one line per story
    stories = pd.concat([web, books], ignore_index=True).drop_duplicates("story_id")
    print(f"   {(stories.format == 'Webtoon').sum()} webtoons, {(stories.format == 'Book').sum()} books",
          flush=True)

    print("3/4 Wikipedia: matching pages and reading monthly views", flush=True)
    stories = resolve_wikipedia(stories)
    arts = sorted(stories["wiki_article"].dropna().unique())
    print(f"   {len(arts)} stories have an English Wikipedia page", flush=True)
    start = (last_month - pd.DateOffset(months=23)).strftime("%Y-%m-%d")
    end = (last_month + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
    views = wikipedia_views(arts, start=start, end=end)
    stories = stories.merge(wikipedia_metrics(views, last_month), on="wiki_article", how="left")

    # time series keyed by story
    h = hist.merge(web[["source_id", "story_id"]], on="source_id")
    rows = [{"story_id": r.story_id, "kind": "fans", "x": r.date.date().isoformat(),
             "value": r.fans} for r in h.itertuples()]
    rows += [{"story_id": r.story_id, "kind": "fans", "x": today.date().isoformat(),
              "value": r.fans_now} for r in web.itertuples()]
    v = views.merge(stories[["story_id", "wiki_article"]].dropna(), on="wiki_article")
    rows += [{"story_id": r.story_id, "kind": "wikipedia_views",
              "x": pd.Timestamp(r.date).date().isoformat(), "value": r.value}
             for r in v.itertuples()]
    history = pd.DataFrame(rows)

    stories.drop(columns=["subjects"], errors="ignore").to_csv(RAW / "watchlist_raw.csv",
                                                                index=False)
    history.to_csv(RAW / "watchlist_history.csv", index=False)
    (RAW / "watchlist_raw_meta.json").write_text(json.dumps({
        "snapshot": today.date().isoformat(),
        "wikipedia_last_month": last_month.strftime("%B %Y")}, indent=2), encoding="utf-8")


def build() -> pd.DataFrame:
    stories = pd.read_csv(RAW / "watchlist_raw.csv").drop_duplicates("story_id")
    history = pd.read_csv(RAW / "watchlist_history.csv").drop_duplicates()
    raw_meta = json.loads((RAW / "watchlist_raw_meta.json").read_text(encoding="utf-8"))
    stories["adaptation"] = stories["adaptation"].where(stories["adaptation"].notna(), None)
    stories["wiki_adapted"] = stories["wiki_adapted"].fillna(False).astype(bool)

    print("4/4 Scoring", flush=True)
    stories = clean_books(revalidate(stories))
    # drop Wikipedia curves of pages that no longer match, and of removed stories
    matched = set(stories.loc[stories["wiki_article"].notna(), "story_id"])
    history = history[(history["kind"] != "wikipedia_views") | history["story_id"].isin(matched)]
    history = history[history["story_id"].isin(set(stories["story_id"]))]
    wl = score(stories)
    wl = wl[[c for c in KEEP if c in wl.columns]]
    wl.to_csv(PROCESSED / "watchlist.csv", index=False)

    books = stories[stories["format"] == "Book"]
    extra = []
    for r in books.itertuples():
        extra.append({"story_id": r.story_id, "kind": "reader_activity",
                      "x": "Average day, previous week", "value": r.previous_days_avg})
        extra.append({"story_id": r.story_id, "kind": "reader_activity",
                      "x": "Last 24 hours", "value": r.last_24h})
    pd.concat([history, pd.DataFrame(extra)], ignore_index=True).to_csv(
        PROCESSED / "watchlist_series.csv", index=False)

    meta = {
        **raw_meta,
        "stories": int(len(wl)),
        "books": int((wl["format"] == "Book").sum()),
        "webtoons": int((wl["format"] == "Webtoon").sum()),
        "with_wikipedia_page": int(wl["wiki_article"].notna().sum()),
        "status_counts": wl["status"].value_counts().to_dict(),
        "sources": ["AniList (webtoon fans)", "Open Library (book readers)",
                    "Wikipedia (mainstream gauge)"],
    }
    (PROCESSED / "watchlist_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return wl


if __name__ == "__main__":
    if "--offline" not in sys.argv:
        collect()
    build()
