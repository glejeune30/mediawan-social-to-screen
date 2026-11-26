"""Wikipedia pageviews (official Wikimedia REST API, no key needed, history since July 2015).

Role in the radar: a "mainstream awareness" gauge. When people start looking a title up
on Wikipedia, it is leaving its niche.
"""
from __future__ import annotations

import time
import urllib.parse
import pandas as pd
import requests

from radar.config import USER_AGENT

PAGEVIEWS = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{project}/all-access/user/{article}/monthly/{start}/{end}"
)
ACTION_API = "https://{lang}.wikipedia.org/w/api.php"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def _get(url: str, params: dict | None = None, retries: int = 4) -> requests.Response:
    """GET with polite back-off: Wikimedia answers 429 when called too fast."""
    for attempt in range(retries):
        r = _session().get(url, params=params, timeout=30)
        if r.status_code != 429:
            time.sleep(1)  # stay well under the rate limit
            return r
        time.sleep(5 * (attempt + 1))
    return r


def monthly_pageviews(article: str, start: str = "2015-07-01", end: str = "2026-10-31",
                      project: str = "en.wikipedia") -> pd.DataFrame:
    """Monthly human pageviews of one article. Returns columns date, value."""
    url = PAGEVIEWS.format(
        project=project,
        article=urllib.parse.quote(article, safe=""),
        start=pd.Timestamp(start).strftime("%Y%m%d00"),
        end=pd.Timestamp(end).strftime("%Y%m%d00"),
    )
    r = _get(url)
    if r.status_code == 404:  # article did not exist yet in that window
        return pd.DataFrame(columns=["date", "value"])
    r.raise_for_status()
    items = r.json().get("items", [])
    df = pd.DataFrame({
        "date": pd.to_datetime([i["timestamp"][:8] for i in items]),
        "value": [i["views"] for i in items],
    })
    return df


def creation_date(article: str, lang: str = "en") -> pd.Timestamp | None:
    """Date the article was first created (a proxy for 'the mainstream noticed it')."""
    params = {
        "action": "query", "prop": "revisions", "titles": article.replace("_", " "),
        "rvlimit": 1, "rvdir": "newer", "rvprop": "timestamp", "format": "json",
        "redirects": 1,
    }
    r = _get(ACTION_API.format(lang=lang), params=params)
    r.raise_for_status()
    pages = r.json()["query"]["pages"]
    for page in pages.values():
        revs = page.get("revisions")
        if revs:
            return pd.Timestamp(revs[0]["timestamp"]).tz_localize(None)
    return None
