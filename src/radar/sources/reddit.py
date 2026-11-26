"""Reddit (official API through PRAW; create a free "script" app at reddit.com/prefs/apps).

Role in the radar: fan-community discussion, the earliest place a title gets recommended.

Limit: the official API only returns roughly the last 1,000 results of a search, and the
public Pushshift archive closed in 2023. So Reddit is used for the *live* radar (weekly
snapshots that we store ourselves), not for long historical backtests.

We only keep aggregate counts (posts, comments, score). No usernames are stored.
"""
from __future__ import annotations

import pandas as pd

from radar.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

DEFAULT_SUBREDDITS = [
    "books", "Fantasy", "RomanceBooks", "YAlit", "booktok", "suggestmeabook",
    "webtoons", "manhwa", "graphic_novels",
]


def _client():
    if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET):
        raise RuntimeError("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
    import praw
    return praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET,
                       user_agent=REDDIT_USER_AGENT)


def weekly_mentions(query: str, subreddits: list[str] | None = None,
                    time_filter: str = "year") -> pd.DataFrame:
    """Posts mentioning the query, aggregated per week: posts, comments, score."""
    reddit = _client()
    subs = "+".join(subreddits or DEFAULT_SUBREDDITS)
    rows = []
    for post in reddit.subreddit(subs).search(f'"{query}"', sort="new",
                                             time_filter=time_filter, limit=None):
        rows.append({
            "created": pd.to_datetime(post.created_utc, unit="s"),
            "subreddit": str(post.subreddit),
            "comments": post.num_comments,
            "score": post.score,
        })
    if not rows:
        return pd.DataFrame(columns=["date", "posts", "comments", "score", "subreddits"])
    df = pd.DataFrame(rows)
    df["date"] = df["created"].dt.to_period("W").dt.start_time
    return (df.groupby("date")
              .agg(posts=("created", "size"), comments=("comments", "sum"),
                   score=("score", "sum"), subreddits=("subreddit", "nunique"))
              .reset_index())
