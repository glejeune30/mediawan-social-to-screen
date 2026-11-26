"""YouTube Data API v3 (official, free key from Google Cloud Console).

Role in the radar: an early "creator" signal. BookTube, webtoon reviewers and recap channels
start talking about a title before the mainstream does.

Metric: number of videos published per month that match the title, and their total views.
The API lets us filter by publication date, so we can rebuild history for the backtest.

Quota: 10,000 units per day by default. One search call costs 100 units, so about 100
searches a day. Fetching 24 months for one title costs ~24 searches + a few video lookups.
"""
from __future__ import annotations

import pandas as pd

from radar.config import YOUTUBE_API_KEY


def _client():
    if not YOUTUBE_API_KEY:
        raise RuntimeError("Set YOUTUBE_API_KEY in .env (see .env.example)")
    from googleapiclient.discovery import build
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)


def monthly_videos(query: str, start: str, end: str, max_per_month: int = 50) -> pd.DataFrame:
    """For each month between start and end: number of matching videos (capped at
    max_per_month, one page of results) and the sum of their current view counts."""
    yt = _client()
    rows = []
    for month in pd.date_range(start, end, freq="MS"):
        after = month.strftime("%Y-%m-%dT00:00:00Z")
        before = (month + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%dT00:00:00Z")
        res = yt.search().list(
            q=f'"{query}"', part="id", type="video", maxResults=max_per_month,
            publishedAfter=after, publishedBefore=before, order="relevance",
        ).execute()
        ids = [i["id"]["videoId"] for i in res.get("items", [])]
        views = 0
        if ids:
            stats = yt.videos().list(part="statistics", id=",".join(ids)).execute()
            views = sum(int(v["statistics"].get("viewCount", 0)) for v in stats.get("items", []))
        rows.append({"date": month, "videos": len(ids), "views": views})
    return pd.DataFrame(rows)
