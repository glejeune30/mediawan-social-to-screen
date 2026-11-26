"""Google Trends search interest.

pytrends is an unofficial client and Google often answers "429 Too Many Requests".
Fallback: export the CSV by hand from trends.google.com (Explore > download icon) and save
it as data/manual/gtrends_<slug>.csv. This module reads that file if the API refuses.

Important: Google Trends values are relative (0-100, 100 = peak of the requested window).
Our indicators only use ratios (growth versus the recent past), so the scale does not matter.
"""
from __future__ import annotations

import re
import time
import pandas as pd

from radar.config import MANUAL


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _read_manual(keyword: str) -> pd.DataFrame | None:
    path = MANUAL / f"gtrends_{slug(keyword)}.csv"
    if not path.exists():
        return None
    raw = pd.read_csv(path, skiprows=1) if path.read_text(encoding="utf-8").startswith("Category") \
        else pd.read_csv(path)
    raw.columns = ["date", "value"]
    raw["date"] = pd.to_datetime(raw["date"])
    raw["value"] = pd.to_numeric(raw["value"].replace("<1", 0.5), errors="coerce")
    return raw


def interest_over_time(keyword: str, start: str, end: str, geo: str = "",
                       retries: int = 3) -> pd.DataFrame:
    """Monthly interest (Google returns monthly points for windows longer than ~5 years,
    weekly otherwise; we resample to monthly in both cases)."""
    try:
        from pytrends.request import TrendReq
        last_error = None
        for attempt in range(retries):
            try:
                py = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
                py.build_payload([keyword], timeframe=f"{start} {end}", geo=geo)
                df = py.interest_over_time()
                if df.empty:
                    break
                df = df.reset_index()[["date", keyword]].rename(columns={keyword: "value"})
                df = df.set_index("date").resample("MS").mean().reset_index()
                return df
            except Exception as e:  # 429 or network
                last_error = e
                time.sleep(20 * (attempt + 1))
        print(f"[google_trends] API failed for '{keyword}': {last_error}")
    except ImportError:
        print("[google_trends] pytrends not installed")
    manual = _read_manual(keyword)
    if manual is not None:
        print(f"[google_trends] using manual export for '{keyword}'")
        manual = manual[(manual["date"] >= start) & (manual["date"] <= end)]
        return manual.set_index("date").resample("MS").mean().reset_index()
    return pd.DataFrame(columns=["date", "value"])
