"""Proof of concept for On the Grill 1: would a simple, fixed rule applied to free public data
have flagged four recent adaptations before the adaptation deal was announced?

Run:  python scripts/run_poc.py            (fetch + compute)
      python scripts/run_poc.py --offline  (recompute from data/raw without refetching series)

Roles of the two free sources in this first test:
  - Google Trends  -> the alert rule is applied to it (it has history back to 2004)
  - Wikipedia      -> mainstream-awareness marker: when did the story get its first article?
                      (pageviews are kept for the charts)
YouTube and Reddit (early community signals) need API keys and come next.

Outputs:
  data/raw/poc_raw.csv                 raw monthly series (title, source, window, date, value)
  data/processed/poc_timeseries.csv    series + momentum + alerts
  data/processed/backtest_results.csv  one line per title: alert, Wikipedia page, deal, lead time
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radar.config import SEEDS, RAW, PROCESSED  # noqa: E402
from radar.sources import wikipedia, google_trends  # noqa: E402
from radar.indicators import source_alerts, first_alert, known_at  # noqa: E402

END = "2026-10-31"


def pages(t) -> list[str]:
    return str(t.wikipedia_article).split("|")


def fetch(seeds: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, t in seeds.iterrows():
        print(f"== {t.title}", flush=True)
        start = max(pd.Timestamp(t.first_published) - pd.DateOffset(months=12),
                    pd.Timestamp("2015-07-01"))
        announce = pd.Timestamp(t.announcement_date)

        wp = wikipedia.monthly_pageviews(pages(t)[0], start=start, end=END)
        frames.append(wp.assign(source="wikipedia", title=t.title, window="full"))
        print(f"   wikipedia: {len(wp)} months", flush=True)

        # Backtest window: ends at the announcement, so the 0-100 scale only uses
        # information that existed before the deal.
        gt_bt = google_trends.interest_over_time(
            t.gt_keyword, start.strftime("%Y-%m-%d"), announce.strftime("%Y-%m-%d"))
        frames.append(gt_bt.assign(source="google_trends", title=t.title, window="backtest"))
        print(f"   google trends (backtest window): {len(gt_bt)} months", flush=True)
        time.sleep(15)

        # Context window (charts only): what happened after the deal.
        gt_full = google_trends.interest_over_time(
            t.gt_keyword, start.strftime("%Y-%m-%d"), END[:10])
        frames.append(gt_full.assign(source="google_trends", title=t.title, window="full"))
        print(f"   google trends (full window): {len(gt_full)} months", flush=True)
        time.sleep(15)

    raw = pd.concat(frames, ignore_index=True)[["title", "source", "window", "date", "value"]]
    raw.to_csv(RAW / "poc_raw.csv", index=False)
    return raw


def compute(seeds: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw["date"] = pd.to_datetime(raw["date"])
    series, results = [], []
    for _, t in seeds.iterrows():
        announce = pd.Timestamp(t.announcement_date)
        row = {"title": t.title, "category": t.category,
               "first_published": t.first_published,
               "announcement_date": announce.date(), "announcement_event": t.announcement_event}

        gt = raw[(raw.title == t.title) & (raw.source == "google_trends")
                 & (raw.window == "backtest")]
        alert = None
        if not gt.empty:
            a = source_alerts(gt[["date", "value"]], "google_trends")
            a["title"], a["window"] = t.title, "backtest"
            series.append(a)
            alert = first_alert(a, before=announce, after=t.first_published)
            live = a[(a["date"] >= pd.Timestamp(t.first_published).to_period("M").start_time)
                     & (a["date"] + pd.offsets.MonthBegin(1) <= announce)]
            finite = live["momentum"].replace(float("inf"), float("nan"))
            row["max_momentum_before_deal"] = (round(float(finite.max()), 2)
                                               if finite.notna().any() else None)
        row["radar_alert"] = alert.date() if alert is not None else None
        # Conservative lead time: counted from the END of the alert month (when it is known).
        row["lead_months"] = (round((announce - known_at(alert)).days / 30.44, 1)
                              if alert is not None else None)

        created = []
        for p in pages(t):
            try:
                c = wikipedia.creation_date(p)
                if c is not None:
                    created.append(c)
            except Exception as e:
                print(f"   (creation date unavailable for {p}: {e})")
        row["first_wikipedia_page"] = min(created).date() if created else None
        results.append(row)

    ts = pd.concat(series, ignore_index=True)
    context = raw[raw.window == "full"].copy()   # Wikipedia + full Google Trends, for charts
    ts = pd.concat([ts, context], ignore_index=True)
    ts.to_csv(PROCESSED / "poc_timeseries.csv", index=False)
    res = pd.DataFrame(results)
    res.to_csv(PROCESSED / "backtest_results.csv", index=False)
    return ts, res


if __name__ == "__main__":
    seeds = pd.read_csv(SEEDS / "backtest_titles.csv")
    raw = pd.read_csv(RAW / "poc_raw.csv") if "--offline" in sys.argv else fetch(seeds)
    _, res = compute(seeds, raw)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 20)
    print(res[["title", "radar_alert", "first_wikipedia_page", "announcement_date",
               "lead_months", "max_momentum_before_deal"]].to_string(index=False))
