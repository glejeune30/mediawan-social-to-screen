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


_SESSION: requests.Session | None = None


def _session() -> requests.Session:
    """One shared connection (keep-alive): faster and gentler on Wikimedia's servers."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers["User-Agent"] = USER_AGENT
    return _SESSION


def _get(url: str, params: dict | None = None, retries: int = 5) -> requests.Response:
    """GET with polite back-off: Wikimedia answers 429 when called too fast."""
    for attempt in range(retries):
        r = _session().get(url, params=params, timeout=30)
        if r.status_code != 429:
            time.sleep(0.5 if "api.php" in url else 1.0)  # stay well under the rate limits
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


def _query(params: dict, lang: str = "en") -> dict:
    base = {"action": "query", "format": "json", "formatversion": 2}
    r = _get(ACTION_API.format(lang=lang), params={**base, **params})
    r.raise_for_status()
    return r.json()


def page_info(titles: list[str], with_categories: bool = False) -> dict[str, dict]:
    """For each requested title: the final page (after redirects) with its short description,
    whether it is a disambiguation page and (optionally) its categories. Missing pages are left
    out. Up to 50 titles per request."""
    out: dict[str, dict] = {}
    prop = "description|pageprops" + ("|categories" if with_categories else "")
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        js = _query({"titles": "|".join(batch), "redirects": 1, "prop": prop,
                     "ppprop": "disambiguation", "cllimit": "max", "clshow": "!hidden"})
        q = js.get("query", {})
        alias = {t: t for t in batch}
        for n in q.get("normalized", []):
            for k, v in alias.items():
                if v == n["from"]:
                    alias[k] = n["to"]
        for rd in q.get("redirects", []):
            for k, v in alias.items():
                if v == rd["from"]:
                    alias[k] = rd["to"]
        pages = {p["title"]: p for p in q.get("pages", []) if not p.get("missing")}
        # categories can be paginated: fetch the rest if needed
        cont = js.get("continue")
        while cont and "clcontinue" in cont:
            more = _query({"titles": "|".join(batch), "redirects": 1, "prop": "categories",
                           "cllimit": "max", "clshow": "!hidden", **cont})
            for p in more.get("query", {}).get("pages", []):
                if p["title"] in pages and p.get("categories"):
                    pages[p["title"]].setdefault("categories", []).extend(p["categories"])
            cont = more.get("continue")
        for requested, final in alias.items():
            p = pages.get(final)
            if p:
                out[requested] = {
                    "title": p["title"],
                    "description": (p.get("description") or "").lower(),
                    "disambiguation": "disambiguation" in (p.get("pageprops") or {}),
                    "categories": [c["title"].removeprefix("Category:")
                                   for c in p.get("categories", [])],
                }
    return out


def search_titles(text: str, limit: int = 5) -> list[str]:
    js = _query({"list": "search", "srsearch": text, "srlimit": limit, "srnamespace": 0})
    return [s["title"] for s in js.get("query", {}).get("search", [])]


def search_pages(text: str, limit: int = 4) -> list[dict]:
    """Full-text search returning pages with their short description, in one request."""
    js = _query({"generator": "search", "gsrsearch": text, "gsrlimit": limit,
                 "gsrnamespace": 0, "prop": "description|pageprops",
                 "ppprop": "disambiguation"})
    pages = sorted(js.get("query", {}).get("pages", []), key=lambda p: p.get("index", 99))
    return [{"title": p["title"], "description": (p.get("description") or "").lower(),
             "disambiguation": "disambiguation" in (p.get("pageprops") or {}),
             "categories": []} for p in pages]


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
