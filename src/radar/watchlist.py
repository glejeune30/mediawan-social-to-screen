"""Live watchlist (v0): link each story to Wikipedia, score it, give it a status.

The three questions of the radar, as computed in v0 (sources without API keys):
  1. Is the buzz accelerating?  community signal, ranked within its format (books / webtoons)
       - webtoons: growth of AniList fans over 90 days (70 %) + AniList activity now (30 %)
       - books:    Open Library reading-log activity, last 24 h versus the previous week (70 %)
                   + volume of that activity (30 %)
  2. Is it spreading?           Wikipedia: page created in the last 12 months, or views growing
                                (+25 % versus the previous 6 months)
  3. Is the mainstream unaware? Wikipedia: no English page = unaware; otherwise, the fewer
                                monthly views the better (log scale; "unaware" below ~6,000 a month)

Status rules (fixed, same for every story):
  Already adapted  an adaptation is listed (AniList anime relation, Wikipedia "adapted into"
                   category, or a South Korean TV series / film page under the webtoon's title)
  Act now          acceleration in the top 10 % of its format AND mainstream still unaware
  Prepare          acceleration in the top 40 % of its format
  Watch            everything else that is tracked
Score (0-100, used to rank): 60 % acceleration + 25 % unawareness + 15 % spreading.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from radar.sources import wikipedia

WEBTOON_WORDS = ("manhwa", "webtoon", "web novel", "comic", "manga", "webcomic")
SCREEN_WORDS = ("television series", "tv series", "miniseries", "drama", "film")
STATUS_ORDER = ["Act now", "Prepare", "Watch", "Already adapted"]
ACT_NOW, PREPARE = 0.9, 0.6     # acceleration percentiles: top 10 % / top 40 % of the format
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def is_screen_adaptation(desc: str, title: str, fmt: str) -> bool:
    """A TV series / film page found under the story's own title = it has been adapted.
    Accepted for Korean pages (webtoons) or distinctive titles (3 words or more)."""
    desc = desc or ""
    if not any(w in desc for w in SCREEN_WORDS):
        return False
    if any(w in desc for w in ("novel", "manhwa", "webtoon", "comic")):
        return False   # the page is about the story itself, not its adaptation
    distinctive = len(re.findall(r"\w+", title or "")) >= 3
    return (fmt == "Webtoon" and "south korean" in desc) or distinctive


def clean_books(df: pd.DataFrame) -> pd.DataFrame:
    """Drop book lines that are not a reader signal for a new story:
    - no reading-log activity at all in the last 8 days,
    - titles not in the Latin alphabet (our scope is English-speaking readers),
    - books written by Open Library's own team (boosted by internal activity, e.g. its programme lead)."""
    book = df["format"] == "Book"
    active = (df["last_24h"].fillna(0) + 7 * df["previous_days_avg"].fillna(0)) > 0
    latin = df["title"].fillna("").map(
        lambda t: sum(c.isascii() for c in t) >= 0.8 * max(len(t), 1))
    staff = df["author"].fillna("").str.contains("Karpeles", case=False)
    return df[~book | (active & latin & ~staff)]


def _clean(t: str) -> str:
    t = re.sub(r"\s*\(.*?\)\s*$", "", t or "").strip().lower().replace("’", "'")
    return re.sub(r"^the\s+", "", t)


def _same_title(page_title: str, story_title: str) -> bool:
    a, b = _clean(page_title), _clean(story_title)
    return len(min(a, b, key=len)) >= 3 and (a.startswith(b) or b.startswith(a))


def _valid(page: dict | None, row) -> bool:
    """Is this Wikipedia page about the story (or about its screen adaptation)?"""
    if not page or page["disambiguation"]:
        return False
    desc = page["description"] or ""
    author = row.author if isinstance(row.author, str) else ""
    surname = author.split(",")[0].split()[-1].lower() if author.strip() else ""
    by_author = bool(surname) and surname in desc
    # same title, or (books) a page of the same author's series, e.g. a redirect to book 1
    same = _same_title(page["title"], row.title)
    if not (same or (row.format == "Book" and by_author)):
        return False
    if is_screen_adaptation(desc, row.title, row.format):
        return True
    if row.format == "Book":
        year = getattr(row, "year", None)
        m = YEAR.search(desc)
        if same and m and pd.notna(year) and abs(int(m.group(0)) - int(year)) > 1:
            return False           # another book with the same title
        if " by " in desc and not by_author:
            return False           # same title, other author
        return "novel" in desc or by_author
    return any(w in desc for w in WEBTOON_WORDS)


def revalidate(stories: pd.DataFrame) -> pd.DataFrame:
    """Re-check stored matches with the current rules; clear the ones that fail."""
    stories = stories.copy()
    for i, r in stories.iterrows():
        if isinstance(r.wiki_article, str):
            page = {"title": r.wiki_article, "description": r.get("wiki_description") or "",
                    "disambiguation": False}
            if not _valid(page, r):
                for c in ["wiki_article", "wiki_description", "wiki_views_month",
                          "wiki_momentum", "wiki_page_age_months"]:
                    stories.at[i, c] = np.nan
                stories.at[i, "wiki_adapted"] = False
    return stories


def _variants(row) -> list[str]:
    if row.format == "Book":
        return [f"{row.title} (novel)", row.title, f"{row.title} (book)"]
    out = [f"{row.title} (manhwa)", f"{row.title} (webtoon)", f"{row.title} (web novel)", row.title]
    alt = getattr(row, "alt_title", None)
    if isinstance(alt, str) and alt != row.title:
        out.append(alt)   # romanised Korean title, sometimes used as the page name
    return out


def resolve_wikipedia(stories: pd.DataFrame) -> pd.DataFrame:
    """Adds wiki_article and wiki_adapted columns (None / False when no page is found)."""
    stories = stories.copy()
    variants = {r.story_id: _variants(r) for r in stories.itertuples()}
    # 1. exact title variants, 50 per request
    info = wikipedia.page_info(sorted({t for v in variants.values() for t in v}))
    found = {}
    for r in stories.itertuples():
        for t in variants[r.story_id]:
            if _valid(info.get(t), r):
                found[r.story_id] = info[t]
                break
    # 2. fallback: one full-text search per story not found by exact title
    missing = stories[~stories["story_id"].isin(found)]
    print(f"   exact titles: {len(found)} found, searching {len(missing)} more", flush=True)
    for r in missing.itertuples():
        hint = "novel" if r.format == "Book" else "manhwa OR webtoon"
        try:
            results = wikipedia.search_pages(f'"{r.title}" {hint}')
        except Exception as e:
            print(f"   search failed for {r.title}: {e}")
            continue
        for p in results:
            if _valid(p, r):
                found[r.story_id] = p
                break
    # 3. categories of the matched pages only: is an adaptation listed?
    cats = wikipedia.page_info(sorted({p["title"] for p in found.values()}), with_categories=True)
    stories["wiki_article"] = stories["story_id"].map(lambda s: found[s]["title"] if s in found else None)
    stories["wiki_description"] = stories["story_id"].map(
        lambda s: found[s]["description"] if s in found else None)
    stories["wiki_adapted"] = stories["wiki_article"].map(
        lambda a: any("adapted into" in c.lower() for c in cats.get(a, {}).get("categories", []))
        if isinstance(a, str) else False)
    return stories


def wikipedia_views(articles: list[str], start: str, end: str) -> pd.DataFrame:
    frames = []
    for a in articles:
        try:
            v = wikipedia.monthly_pageviews(a.replace(" ", "_"), start=start, end=end)
        except Exception as e:  # keep going if one article fails
            print(f"   pageviews failed for {a}: {e}")
            continue
        frames.append(v.assign(wiki_article=a))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["date", "value", "wiki_article"])


def wikipedia_metrics(views: pd.DataFrame, last_month: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for a, g in views.groupby("wiki_article"):
        g = g.sort_values("date").set_index("date")["value"]
        full = g.reindex(pd.date_range(end=last_month, periods=9, freq="MS"), fill_value=0)
        recent, past = full.iloc[-3:].mean(), full.iloc[:6].mean()
        rows.append({
            "wiki_article": a,
            "wiki_views_month": int(g.get(last_month, 0)),
            "wiki_momentum": (recent / past) if past > 0 else np.inf,
            "wiki_page_age_months": (last_month.to_period("M") - g.index.min().to_period("M")).n,
        })
    return pd.DataFrame(rows)


def _k(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return f"{n:.0f}"


def score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    pct = lambda col: df.groupby("format")[col].rank(pct=True)  # noqa: E731
    # 1. acceleration (accel_signal: webtoons = 90-day fan growth, books = 24 h z-score)
    growth_pct = pct("accel_signal")
    activity_pct = pct("activity_now")
    df["accel"] = np.where(growth_pct.notna(), 0.7 * growth_pct + 0.3 * activity_pct, activity_pct)
    df["accel"] = df.groupby("format")["accel"].rank(pct=True)
    # 2. spreading / 3. unawareness
    # awareness on an absolute log scale: 100 views/month = 0, 10k = 0.5, 1M = 1.
    # No page = fully unaware; any page = some awareness (factor 0.9).
    # => "unaware" (>= 0.5) means: no English page, or fewer than ~6,000 views a month.
    has_page = df["wiki_views_month"].notna()
    awareness = ((np.log10(df["wiki_views_month"].clip(lower=1)) - 2) / 4).clip(0, 1)
    df["unaware"] = np.where(has_page, 0.9 * (1 - awareness), 1.0)
    df["spreading"] = np.where(
        has_page & ((df["wiki_momentum"] >= 1.25) | (df["wiki_page_age_months"] <= 12)), 1.0, 0.0)
    df["score"] = (100 * (0.6 * df["accel"] + 0.25 * df["unaware"] + 0.15 * df["spreading"])).round()
    # status
    desc = df.get("wiki_description", pd.Series(index=df.index, dtype=object)).fillna("")
    titles = df["title"] if "title" in df else pd.Series("", index=df.index)
    live_action = pd.Series([is_screen_adaptation(d, t, f) for d, t, f
                             in zip(desc, titles, df["format"])], index=df.index)
    wiki_adapted = df["wiki_adapted"].fillna(False).astype(bool)
    adapted = df["adaptation"].notna() | wiki_adapted | live_action
    df["status"] = np.select(
        [adapted, (df["accel"] >= ACT_NOW) & (df["unaware"] >= 0.5), df["accel"] >= PREPARE],
        ["Already adapted", "Act now", "Prepare"], default="Watch")
    df["adaptation"] = np.where(
        df["adaptation"].notna(), df["adaptation"],
        np.where(live_action, "TV series or film (Wikipedia)",
                 np.where(wiki_adapted, "Adaptation listed on Wikipedia", None)))

    # plain-language signals
    def fan_signal(r):
        if r.format == "Webtoon":
            g = " · new, under 90 days" if pd.isna(r.growth_90d) else f", {r.growth_90d:+.1%} in 90 days"
            return f"{_k(r.fans_now)} fans{g}"
        return f"{r.last_24h:.0f} reader logs in 24 h (vs {r.previous_days_avg:.0f}/day)"

    def mainstream(r):
        if pd.isna(r.wiki_views_month):
            return "No Wikipedia page yet"
        arrow = " ↗" if r.spreading else ""
        return f"{_k(r.wiki_views_month)} views/month{arrow}"

    def why(r):
        top = max(1, round((1 - r.accel) * 100))
        if r.format == "Webtoon":
            if pd.isna(r.growth_90d):
                first = (f"New on AniList (less than 90 days of history), already {_k(r.fans_now)} "
                         f"fans (top {top}% of tracked webtoons)")
            else:
                first = (f"AniList fan base {r.growth_90d:+.1%} in 90 days, {_k(r.fans_now)} fans "
                         f"today (top {top}% of tracked webtoons)")
        else:
            first = (f"Open Library readers: {r.last_24h:.0f} logs in the last 24 h against "
                     f"{r.previous_days_avg:.0f} per day the week before (top {top}% of tracked books)")
        if pd.isna(r.wiki_views_month):
            second = "No English Wikipedia page yet: the mainstream has not caught on"
        else:
            trend = (f", up {r.wiki_momentum - 1:.0%} versus the 6 months before"
                     if np.isfinite(r.wiki_momentum) and r.wiki_momentum >= 1.25 else "")
            second = f"Wikipedia: {_k(r.wiki_views_month)} views last month{trend}"
        if isinstance(r.adaptation, str) and r.adaptation:
            third = f"Already adapted: {r.adaptation}"
        elif r.format == "Webtoon":
            third = "No anime adaptation listed on AniList (check live-action rights)"
        else:
            third = "No adaptation listed on Wikipedia: check rights with the publisher"
        return " | ".join([first, second, third])

    df["fan_signal"] = df.apply(fan_signal, axis=1)
    df["mainstream"] = df.apply(mainstream, axis=1)
    df["why"] = df.apply(why, axis=1)
    df["status_rank"] = df["status"].map({s: i for i, s in enumerate(STATUS_ORDER)})
    return df.sort_values(["status_rank", "score"], ascending=[True, False])
