"""Open Library search API (Internet Archive, public, no key needed).

Role in the radar: live *reader community* signal for books.
Open Library readers log books as "want to read", "currently reading" or "already read".
The search index exposes, for every book, its recent logging activity:
- `trending_score_hourly_sum`: activity over the last 24 hours
- `trending_score_daily_0..6`: activity on each of the previous days
- `trending_z_score`: how unusual the last 24 hours are compared with the previous days
We query recent fiction in Mediawan's genres, sorted by that trending score.

Only public, aggregate counts per book are used. No reader data is collected.
"""
from __future__ import annotations

import re
import time

import pandas as pd
import requests

from radar.config import USER_AGENT

SEARCH = "https://openlibrary.org/search.json"
COVER = "https://covers.openlibrary.org/b/id/{}-M.jpg"

GENRE_QUERIES = {
    "Fantasy": 'subject:"fantasy"',
    "Romance": 'subject:"romance"',
    "Young adult": 'subject:"young adult fiction"',
    "Thriller & mystery": '(subject:"thriller" OR subject:"suspense" OR subject:"mystery")',
    "Science fiction": 'subject:"science fiction"',
}

FIELDS = ",".join([
    "key", "title", "author_name", "first_publish_year", "cover_i", "subject",
    "want_to_read_count", "currently_reading_count", "already_read_count",
    "trending_z_score", "trending_score_hourly_sum",
    *[f"trending_score_daily_{i}" for i in range(7)],
])

# Volumes of manga / comics series are not new stories: drop them.
SERIES_VOLUME = re.compile(r"(\bvol\.?\s*\d+|\bvolume\s*\d+|\s\d{1,3}$|#\d+)", re.IGNORECASE)
NON_STORY_SUBJECTS = ("manga", "comic books, strips", "cookbooks", "self-help")


def trending_books(per_genre: int = 40, since: int = 2022, min_readers: int = 10) -> pd.DataFrame:
    rows: dict[str, dict] = {}
    for genre, q in GENRE_QUERIES.items():
        params = {"q": f"{q} first_publish_year:[{since} TO *] language:eng",
                  "sort": "trending", "fields": FIELDS, "limit": per_genre}
        r = requests.get(SEARCH, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
        r.raise_for_status()
        time.sleep(1)
        for d in r.json().get("docs", []):
            key = d["key"]
            if key in rows:
                rows[key]["genre_set"].add(genre)
                continue
            subjects = [s.lower() for s in d.get("subject", [])]
            title = d.get("title", "")
            if SERIES_VOLUME.search(title) or any(
                    any(ns in s for ns in NON_STORY_SUBJECTS) for s in subjects):
                continue
            readers = (d.get("want_to_read_count") or 0) + (d.get("currently_reading_count") or 0) \
                + (d.get("already_read_count") or 0)
            if readers < min_readers:
                continue
            daily = [d.get(f"trending_score_daily_{i}") or 0 for i in range(7)]
            rows[key] = {
                "source_id": key,
                "title": title,
                "alt_title": None,
                "author": ", ".join((d.get("author_name") or [])[:2]),
                "year": d.get("first_publish_year"),
                "genre_set": {genre},
                "subjects": subjects,
                "cover_url": COVER.format(d["cover_i"]) if d.get("cover_i") else None,
                "source_url": f"https://openlibrary.org{key}",
                "readers": readers,
                "want_to_read": d.get("want_to_read_count") or 0,
                "last_24h": d.get("trending_score_hourly_sum") or 0,
                "previous_days_avg": round(sum(daily) / 7, 2),
                "trending_z": d.get("trending_z_score") or 0.0,
                "adaptation": None,
            }
    out = []
    for row in rows.values():
        g = row.pop("genre_set")
        subjects = row.pop("subjects")
        if "Fantasy" in g and ("Romance" in g or any("romance" in s for s in subjects)):
            g.add("Romantasy")
        row["genres"] = ", ".join(sorted(g))
        out.append(row)
    return pd.DataFrame(out)
