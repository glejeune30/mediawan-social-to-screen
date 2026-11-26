# 4. Method: how the radar decides that a story is emerging

## Pipeline

```
collect (APIs, weekly)  ->  match titles across sources  ->  monthly/weekly series per title
      ->  indicators (momentum, breadth, awareness gap)  ->  emergence score  ->  status
      ->  watchlist (Streamlit app)            and          backtest against past deals
```

## 1. Which titles do we track?

- **Seed list** from public rankings (Webtoon, Wattpad, bestseller lists) and award lists.
- **Discovery**: titles cited in Reddit posts and YouTube video titles. Week 2: extract them with
  a named-entity model or an LLM prompt, then match them to a canonical title (fuzzy matching on
  title + author). Matching the same story across sources is the hardest data-cleaning step.

## 2. Indicators (per title, per source)

| Plain-language question | Indicator | Definition |
|---|---|---|
| Is the buzz accelerating? | **Momentum** | mean of the last 3 months ÷ mean of the 6 months before |
| Is it real, not noise? | **Level floor** | the 3-month mean must exceed a minimum (e.g. 1,000 Wikipedia views/month, 2 points of Google Trends, 5 videos/month) |
| Is it spreading? | **Breadth** | share of sources on which the title is accelerating |
| Is the mainstream still unaware? | **Awareness gap** | niche momentum (YouTube, Reddit, rankings) minus mainstream momentum (Google Trends, Wikipedia) |

All indicators only use data available at each date (no look-ahead).

## 3. Alert rule (fixed before looking at results)

A source raises an **alert** for a title when momentum ≥ 2 **and** the level is above its floor,
**two months in a row**. The radar's alert date is the earliest alert across sources.

Two guards against cheating ourselves:
- a monthly point only counts once the month is over (lead time is measured from the end of the
  alert month);
- months before the title was first published are ignored (searches for a homonym).

In the proof of concept (26 Nov), the rule is applied to **Google Trends only**; Wikipedia is used
as the mainstream marker (date of the first page). Results: `data/processed/backtest_results.csv`.

## 4. Emergence score (live watchlist)

`score = 50 × strength + 30 × breadth + 20 × awareness gap` (0-100)

- strength = log2(momentum) capped at ×8, scaled to 0-1
- **Watch** < 40 ≤ **Prepare** < 70 ≤ **Act now**

Weights are a starting point; we will calibrate them on the backtest and the control group.

## 4b. Live watchlist v0 (prototype, sources without API keys)

Built by `scripts/run_watchlist.py`, logic in `src/radar/watchlist.py`.

| Question | Webtoons | Books |
|---|---|---|
| Accelerating? | AniList fans today vs 90 days ago (70 %) + AniList activity now (30 %) | Open Library reader logs, last 24 h vs previous week (z-score, 70 %) + volume in the last 24 h (30 %) |
| Spreading? | Wikipedia page less than 12 months old, or views +25 % vs the previous 6 months | same |
| Mainstream unaware? | No English Wikipedia page, or fewer than about 6,000 views a month (log scale: 100 views = unknown, 1M = mainstream) | same |

- Acceleration is ranked **within each format** (books are compared with books, webtoons with webtoons).
- Score = 60 % acceleration + 25 % unawareness + 15 % spreading.
- Status rules: **Already adapted** (anime relation on AniList, a Wikipedia "adapted into"
  category, or a TV series / film page under the story's own title) › **Act now** (acceleration
  in the top 10 % of its format and mainstream unaware) › **Prepare** (top 40 %) › **Watch**.
- Wikipedia pages are matched by exact title variants ("Title (novel)", "Title (manhwa)"…), then
  by search. A page is accepted only if its title matches (or, for books, it names the same
  author), its short description says it is a novel / manhwa / webtoon (or its TV / film
  adaptation), and, for books with the same title, the year matches.
- Cleaning: books with no reader activity in the last 8 days, titles outside the Latin alphabet
  and books by Open Library's own team are left out.

## 5. Backtest protocol

1. **Positive set**: titles adapted recently, with a public announcement date
   (`data/seeds/backtest_titles.csv`).
2. **Control set** (done 26 Nov, see section 6): titles that buzzed in the same communities but
   were *not* adapted.
3. For each title, compute the first alert before the announcement. Report:
   - **hit rate**: share of adapted titles flagged before the deal;
   - **lead time**: months between alert and deal (median);
   - **false-alarm rate**: share of control titles that were flagged.
4. Google Trends is queried with a window ending at the announcement date, so its 0-100 scale
   only uses information that existed at the time.

## 6. Results of the false-alarm test (26 Nov, `scripts/run_control_test.py`)

Control group chosen *before* looking at any curve: the 8 webtoons from 2018-2022 with the most
AniList fans and the 8 most wanted books from 2019-2022 on Open Library, all with no adaptation
listed on AniList or Wikipedia (titles whose name is ambiguous on Wikipedia left out). Same rule,
window from 12 months before to 46 months after publication (46 = median publication-to-deal
time of the adapted titles).

| | Result |
|---|---|
| Adapted titles flagged before the deal | **3 / 4** |
| Never-adapted titles that still raised an alert (false alarms) | **11 / 12** |
| Of those false alarms, in the first 6 months after publication | 5 |
| "Controls" that a trade-press check showed were in fact optioned | **4** (The Midnight Library, optioned in 2020; Netflix's Twisted series deal, Jan 2025) |
| Twisted series: alert before Netflix's deal | ~34 months before (2 of the 3 books) |
| Precision (alerts followed by a deal / all alerts) | **29 %** |

**Reading:** acceleration in Google searches catches the hits but fires for almost every popular
story. It is a necessary first filter, not a decision rule. Consequences for the radar:
1. rank stories against each other (the live watchlist only flags the top 10 % of each format);
2. require the mainstream gap and, with YouTube and Reddit, spreading across communities;
3. check rights in the trade press: our automatic check (AniList, Wikipedia categories) missed
   4 deals out of 16 titles.

Sources of the checks: `data/seeds/control_checks.csv`. Per-title results:
`data/processed/control_results.csv`.

## Known limits

- **Survivorship bias**: we start from known successes. The control set is there to correct it.
- **Launch effect**: every new book accelerates at launch; breadth and the awareness gap are meant
  to separate real phenomena from ordinary launches.
- **Announcement ≠ option date**: rights are often optioned months before the public announcement
  (Heartstopper was optioned about 18 months before Netflix's order), so the real window is shorter
  than the measured lead time.
- **Platform bias**: public APIs over-represent English-speaking communities.
- **Google Trends** is relative and sampled; values can change slightly between two queries.
