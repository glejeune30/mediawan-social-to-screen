"""False-alarm test: does the backtest rule also fire for stories that buzzed but were never
adapted? About 10 minutes (Google Trends and Wikipedia limit the request rate).

Run:  python scripts/run_control_test.py            select controls + fetch + compute
      python scripts/run_control_test.py --offline  recompute from the saved data

Control group (selection rule fixed before looking at any Google Trends data):
  - Webtoons: series that started 2018-2022 (same era as the adapted titles), collected this week
    from AniList, with no adaptation listed (no anime on AniList, no "adapted into" category and no
    TV / film page on Wikipedia): the 8 with the most AniList fans.
  - Books: fiction first published 2019-2022 in our genres, the most wanted on Open Library, with
    no adaptation listed on Wikipedia: the top 8.
  - Titles whose exact name is a Wikipedia disambiguation page or another topic are left out
    (their Google searches would mix several meanings).
Window: from 12 months before publication to 46 months after it (46 = median time between
publication and the deal for the four adapted titles), capped at the last complete month.
Same rule as the backtest: an alert = Google searches over 3 months at least double the 6 months
before, two months in a row, after publication. Every alert here is a false alarm.

Outputs:
  data/seeds/control_titles.csv          the selected control titles and why
  data/raw/control_gt.csv                Google Trends series
  data/processed/control_results.csv     one line per title: alert or not
  data/processed/backtest_summary.json   hit rate, false-alarm rate, precision
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radar.config import SEEDS, RAW, PROCESSED  # noqa: E402
from radar.indicators import source_alerts, first_alert, known_at  # noqa: E402
from radar.sources import google_trends, openlibrary, wikipedia, anilist  # noqa: E402
from radar.watchlist import _valid, resolve_wikipedia, is_screen_adaptation  # noqa: E402

N_PER_FORMAT = 8
HORIZON_MONTHS = 46


def _ambiguous(stories: pd.DataFrame) -> set[str]:
    """Titles whose exact name on Wikipedia is a disambiguation page or another topic."""
    info = wikipedia.page_info(sorted(set(stories["title"])))
    out = set()
    for r in stories.itertuples():
        p = info.get(r.title)
        if p and (p["disambiguation"] or not _valid(p, r)):
            out.add(r.story_id)
    return out


def select_controls() -> pd.DataFrame:
    raw = pd.read_csv(RAW / "watchlist_raw.csv").drop_duplicates("story_id")

    # --- webtoons from this week's AniList collection
    web = raw[(raw["format"] == "Webtoon") & raw["year"].between(2018, 2022)].copy()
    desc = web["wiki_description"].fillna("")
    adapted = (web["adaptation"].notna() | web["wiki_adapted"].fillna(False).astype(bool)
               | pd.Series([is_screen_adaptation(d, t, "Webtoon") for d, t in
                            zip(desc, web["title"])], index=web.index))
    web = web[~adapted & ~web["title"].str.contains(r"[^\x00-\x7F’']", regex=True)]
    web = web[~web["story_id"].isin(_ambiguous(web))]
    web = web.sort_values("fans_now", ascending=False).head(N_PER_FORMAT)
    # exact start month from AniList
    ids = web["story_id"].str.replace("al-", "").astype(int).tolist()
    q = """query ($ids: [Int]) { Page(perPage: 50) { media(id_in: $ids) {
             id startDate { year month } } } }"""
    starts = {m["id"]: m["startDate"] for m in anilist._post(q, {"ids": ids})["Page"]["media"]}
    web["first_published"] = [
        f"{starts[i]['year']}-{(starts[i]['month'] or 1):02d}-01" for i in ids]
    web["selection"] = "AniList fans (top 8 started 2018-2022), no adaptation listed"
    web["popularity"] = web["fans_now"].map(lambda v: f"{v:,.0f} AniList fans")

    # --- books: most wanted 2019-2022 on Open Library, no adaptation listed on Wikipedia
    books = openlibrary.popular_books(2019, 2022)
    books["format"] = "Book"
    books["story_id"] = "ol-" + books["source_id"].str.replace("/works/", "", regex=False)
    books = books.sort_values("want_to_read", ascending=False).head(3 * N_PER_FORMAT)
    books = resolve_wikipedia(books)
    desc = books["wiki_description"].fillna("")
    adapted = books["wiki_adapted"] | pd.Series(
        [is_screen_adaptation(d, t, "Book") for d, t in zip(desc, books["title"])],
        index=books.index)
    books = books[~adapted]
    books = books[~books["story_id"].isin(_ambiguous(books))]
    books = books.head(N_PER_FORMAT).copy()
    books["first_published"] = books["year"].astype(int).astype(str) + "-01-01"
    books["selection"] = "Open Library most wanted (2019-2022), no adaptation listed on Wikipedia"
    books["popularity"] = books["want_to_read"].map(lambda v: f"{v:,.0f} want to read")

    cols = ["title", "format", "author", "first_published", "popularity", "selection",
            "source_url"]
    ctrl = pd.concat([web[cols], books[cols]], ignore_index=True)
    ctrl["gt_keyword"] = ctrl["title"].str.lower().str.replace("’", "'")
    ctrl.to_csv(SEEDS / "control_titles.csv", index=False)
    print(ctrl[["format", "title", "first_published", "popularity"]].to_string(index=False))
    return ctrl


def window(first_published: str, last_month: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    pub = pd.Timestamp(first_published)
    start = max(pub - pd.DateOffset(months=12), pd.Timestamp("2015-07-01"))
    end = min(pub + pd.DateOffset(months=HORIZON_MONTHS), last_month + pd.offsets.MonthEnd(0))
    return start, end


def fetch(ctrl: pd.DataFrame, last_month: pd.Timestamp) -> pd.DataFrame:
    frames = []
    for r in ctrl.itertuples():
        start, end = window(r.first_published, last_month)
        print(f"== {r.title} ({start.date()} → {end.date()})", flush=True)
        gt = google_trends.interest_over_time(r.gt_keyword, start.strftime("%Y-%m-%d"),
                                              end.strftime("%Y-%m-%d"))
        frames.append(gt.assign(title=r.title))
        time.sleep(15)
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(RAW / "control_gt.csv", index=False)
    return raw


def compute(ctrl: pd.DataFrame, raw: pd.DataFrame, last_month: pd.Timestamp) -> pd.DataFrame:
    raw["date"] = pd.to_datetime(raw["date"])
    rows = []
    for r in ctrl.itertuples():
        start, end = window(r.first_published, last_month)
        s = raw[raw["title"] == r.title][["date", "value"]]
        alert = None
        if not s.empty and s["value"].sum() > 0:
            a = source_alerts(s, "google_trends")
            alert = first_alert(a, before=end, after=r.first_published)
        pub = pd.Timestamp(r.first_published)
        rows.append({
            "title": r.title, "format": r.format, "first_published": pub.date(),
            "window_end": end.date(), "has_data": not s.empty and s["value"].sum() > 0,
            "radar_alert": alert.date() if alert is not None else None,
            "months_after_publication": (round((known_at(alert) - pub).days / 30.44, 1)
                                         if alert is not None else None),
            "false_alarm": alert is not None,
            "popularity": r.popularity,
        })
    res = pd.DataFrame(rows)

    # Manual check of each control in the trade press (data/seeds/control_checks.csv): a few
    # "never adapted" titles turned out to have been optioned. They leave the control group.
    checks_path = SEEDS / "control_checks.csv"
    checks = pd.read_csv(checks_path) if checks_path.exists() else pd.DataFrame(
        columns=["title", "adaptation_found", "deal_date", "deal", "source_url"])
    res = res.merge(checks, on="title", how="left")
    res["adaptation_found"] = res["adaptation_found"].fillna(False).astype(bool)
    deal = pd.to_datetime(res["deal_date"])
    alert = pd.to_datetime(res["radar_alert"])
    known = alert + pd.offsets.MonthBegin(1)
    res["lead_months"] = ((deal - known).dt.days / 30.44).round(1)
    res["verdict"] = "No alert"
    res.loc[res["radar_alert"].notna(), "verdict"] = "False alarm"
    adapted = res["adaptation_found"]
    res.loc[adapted, "verdict"] = "Adapted after all: missed"
    res.loc[adapted & alert.notna(), "verdict"] = "Adapted after all: alert around the deal"
    res.loc[adapted & alert.notna() & (res["lead_months"] > 0),
            "verdict"] = "Adapted after all: alert before the deal"
    res.to_csv(PROCESSED / "control_results.csv", index=False)

    bt = pd.read_csv(PROCESSED / "backtest_results.csv")
    usable = res[res["has_data"]]
    controls = usable[~usable["adaptation_found"]]
    extra = usable[usable["adaptation_found"]]
    hits0, n_pos = int(bt["lead_months"].notna().sum()), len(bt)
    hits_extra = int((extra["verdict"] == "Adapted after all: alert before the deal").sum())
    around = int((extra["verdict"] == "Adapted after all: alert around the deal").sum())
    fa, n_ctrl = int(controls["false_alarm"].sum()), len(controls)
    hits = hits0 + hits_extra
    summary = {
        "adapted_flagged": hits0, "adapted_total": n_pos,
        "controls_flagged": fa, "controls_total": n_ctrl,
        "controls_found_adapted": int(len(extra)),
        "controls_found_adapted_titles": extra["title"].tolist(),
        "extra_hits_before_deal": hits_extra,
        "hit_rate": round(hits0 / n_pos, 2),
        "false_alarm_rate": round(fa / n_ctrl, 2) if n_ctrl else None,
        "precision": round(hits / (hits + around + fa), 2) if hits + around + fa else None,
        "false_alarms_within_6_months_of_publication": int(
            (controls["months_after_publication"] <= 6).sum()),
        "horizon_months": HORIZON_MONTHS,
    }
    (PROCESSED / "backtest_summary.json").write_text(json.dumps(summary, indent=2),
                                                    encoding="utf-8")
    print(res.to_string(index=False))
    print(json.dumps(summary, indent=2))
    return res


if __name__ == "__main__":
    last_month = (pd.Timestamp.today().to_period("M") - 1).start_time
    if "--offline" in sys.argv:
        ctrl = pd.read_csv(SEEDS / "control_titles.csv")
        raw = pd.read_csv(RAW / "control_gt.csv")
    else:
        ctrl = select_controls()
        raw = fetch(ctrl, last_month)
    compute(ctrl, raw, last_month)
