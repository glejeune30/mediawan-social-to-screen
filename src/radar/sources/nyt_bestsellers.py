"""New York Times Books API (official, free key at developer.nytimes.com).

Role in the radar: "ground truth" for books. The week a title first enters a NYT list is
the week it is clearly mainstream (and rights are likely gone or expensive).
"""
from __future__ import annotations

import time
import pandas as pd
import requests

from radar.config import NYT_API_KEY

BASE = "https://api.nytimes.com/svc/books/v3"


def best_sellers_history(title: str) -> pd.DataFrame:
    """Every list appearance of a title. Columns: list_name, date, rank."""
    if not NYT_API_KEY:
        raise RuntimeError("Set NYT_API_KEY in .env")
    r = requests.get(f"{BASE}/lists/best-sellers/history.json",
                     params={"title": title, "api-key": NYT_API_KEY}, timeout=30)
    r.raise_for_status()
    rows = []
    for book in r.json().get("results", []):
        for rk in book.get("ranks_history", []):
            rows.append({"list_name": rk["list_name"],
                         "date": pd.Timestamp(rk["published_date"]),
                         "rank": rk["rank"]})
    time.sleep(12)  # NYT allows ~5 calls per minute
    return pd.DataFrame(rows)


def first_entry(title: str) -> pd.Timestamp | None:
    hist = best_sellers_history(title)
    return None if hist.empty else hist["date"].min()
