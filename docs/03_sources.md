# 3. Data sources: what we use and why

The brief asks for 3 or 4 well-chosen public sources, official APIs where possible, and no
personal data. We split them into **early signals** (niche communities) and a **mainstream gauge**.

| Role | Source | Access | History | Status |
|---|---|---|---|---|
| Early signal | **AniList API** (webtoon / manhwa fans who list a series) | Public GraphQL API, no key, ~30 requests/min | Daily snapshots of each series' fan count | **Live** in the prototype (`anilist.py`) |
| Early signal | **Open Library search API** (readers logging books as want-to-read / reading / read) | Public API, no key | Last 24 h and previous 7 days of activity | **Live** in the prototype (`openlibrary.py`) |
| Early signal | **YouTube Data API v3** (BookTube, webtoon reviewers, recap channels) | Official, free key, 10,000 units/day (≈100 searches) | Yes, search can filter by publication date | Code ready (`src/radar/sources/youtube.py`), needs a key |
| Early signal | **Reddit API** (r/Fantasy, r/RomanceBooks, r/YAlit, r/booktok, r/webtoons, r/manhwa…) | Official, free "script" app | Limited (≈ last 1,000 results; Pushshift closed in 2023) | Code ready (`reddit.py`), needs a key. Used for the live radar |
| Early signal | **Webtoon and Wattpad public rankings** | Public pages; check terms of use before any automated collection | Only from the day we start snapshots | To do (week 2) |
| Mainstream gauge | **Google Trends** | Unofficial client (pytrends), often rate-limited; manual CSV export as fallback | Since 2004 | Working (`google_trends.py`) |
| Mainstream gauge | **Wikipedia pageviews** | Official Wikimedia API, no key | Since July 2015 | **Live** (`wikipedia.py`): page matching, monthly views, "adapted into" categories |
| Ground truth (books) | **NYT Books API** (bestseller history) | Official, free key | Yes | Code ready (`nyt_bestsellers.py`), needs a key |

## Why not TikTok or Instagram directly?

- TikTok's Research API is reserved for approved academic researchers; approval does not fit a
  three-week project. TikTok Creative Center can be consulted by hand for context.
- Instagram's API does not give public search over posts.
- BookTok content is largely mirrored on YouTube (BookTube, Shorts) and discussed on Reddit, so we
  capture the same communities through official APIs.

## Rules we follow

- Official APIs and public rankings only, respecting each platform's terms of use and rate limits.
- We store **aggregates only** (counts of posts, videos, views per title per period). No usernames,
  no private individuals.
- API keys stay in a local `.env` file, never in the repository.
