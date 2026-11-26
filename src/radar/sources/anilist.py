"""AniList GraphQL API (public, no key needed, about 30 requests per minute).

Role in the radar: live *community* signal for webtoons / manhwa.
- `popularity` = number of AniList users who put the series on their list (a fan community).
- AniList keeps a daily snapshot of it, so we can compare today with 30, 60, 90, 180 days ago.
- `relations` tell us whether an anime adaptation is already listed (= rights probably gone).

We only read public, aggregate data about series. No user data is collected.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

from radar.config import USER_AGENT

ENDPOINT = "https://graphql.anilist.co"
PAUSE = 2.2  # seconds between calls, to stay under the public rate limit

LIST_QUERY = """
query ($page: Int, $perPage: Int, $country: CountryCode) {
  Page(page: $page, perPage: $perPage) {
    media(type: MANGA, countryOfOrigin: $country, isAdult: false, sort: TRENDING_DESC) {
      id
      title { romaji english }
      siteUrl
      status
      startDate { year month }
      genres
      popularity
      favourites
      trending
      averageScore
      coverImage { large }
      staff(perPage: 3, sort: RELEVANCE) { edges { role node { name { full } } } }
      relations { edges { relationType node { type format status startDate { year } } } }
    }
  }
}
"""

TRENDS_QUERY = """
query ($ids: [Int], $gt: Int, $lt: Int, $page: Int) {
  Page(page: $page, perPage: 50) {
    pageInfo { hasNextPage }
    mediaTrends(mediaId_in: $ids, date_greater: $gt, date_lesser: $lt, sort: DATE) {
      mediaId
      date
      popularity
    }
  }
}
"""


def _post(query: str, variables: dict, retries: int = 4) -> dict:
    for attempt in range(retries):
        r = requests.post(ENDPOINT, json={"query": query, "variables": variables},
                          headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                          timeout=40)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 30)) + 1)
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        data = r.json()
        if "errors" in data:
            raise RuntimeError(data["errors"])
        return data["data"]
    raise RuntimeError("AniList rate limit: try again in a minute")


def _authors(media: dict) -> str:
    names = []
    for e in media.get("staff", {}).get("edges", []):
        role = (e.get("role") or "").lower()
        if "story" in role or "original" in role or "art" in role:
            n = e["node"]["name"]["full"]
            if n and n not in names:
                names.append(n)
    return ", ".join(names[:2])


def _adaptation(media: dict) -> str | None:
    """Text describing an anime adaptation listed on AniList, or None."""
    found = []
    for e in media.get("relations", {}).get("edges", []):
        node = e["node"]
        if node.get("type") == "ANIME":
            year = (node.get("startDate") or {}).get("year")
            if node.get("status") == "NOT_YET_RELEASED":
                found.append(f"Anime announced{f' ({year})' if year else ''}")
            else:
                found.append(f"Anime{f' ({year})' if year else ''}")
    return found[0] if found else None


def trending_webtoons(n: int = 60, country: str = "KR") -> pd.DataFrame:
    """The n series with the most activity right now on AniList (non-adult)."""
    rows, page = [], 1
    while len(rows) < n:
        # always 50 per page: AniList pages are numbered for a fixed page size
        data = _post(LIST_QUERY, {"page": page, "perPage": 50, "country": country})
        media = data["Page"]["media"]
        if not media:
            break
        for m in media:
            rows.append({
                "source_id": m["id"],
                "title": m["title"]["english"] or m["title"]["romaji"],
                "alt_title": m["title"]["romaji"],
                "author": _authors(m),
                "year": (m.get("startDate") or {}).get("year"),
                "genres": ", ".join(m.get("genres") or []),
                "cover_url": (m.get("coverImage") or {}).get("large"),
                "source_url": m["siteUrl"],
                "publication_status": (m.get("status") or "").replace("_", " ").capitalize(),
                "fans_now": m["popularity"],
                "favourites": m["favourites"],
                "trending": m["trending"],
                "adaptation": _adaptation(m),
            })
        page += 1
    # the ranking can move between two pages: keep one line per series
    return pd.DataFrame(rows).drop_duplicates("source_id").head(n).reset_index(drop=True)


def popularity_history(ids: list[int], days_ago=(30, 60, 90, 180)) -> pd.DataFrame:
    """Number of fans (AniList popularity) for each series, `d` days ago."""
    now = int(time.time())
    rows = []
    for d in days_ago:
        centre = now - d * 86400
        for i in range(0, len(ids), 25):
            batch, page = ids[i:i + 25], 1
            while True:
                data = _post(TRENDS_QUERY, {"ids": batch, "gt": centre - 86400,
                                            "lt": centre + 86400, "page": page})
                for t in data["Page"]["mediaTrends"]:
                    rows.append({"source_id": t["mediaId"], "days_ago": d,
                                 "date": pd.to_datetime(t["date"], unit="s").normalize(),
                                 "fans": t["popularity"]})
                if not data["Page"]["pageInfo"]["hasNextPage"]:
                    break
                page += 1
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # one value per series and horizon (closest record)
    return df.sort_values("date").groupby(["source_id", "days_ago"], as_index=False).last()
