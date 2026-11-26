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

## 5. Backtest protocol

1. **Positive set**: titles adapted recently, with a public announcement date
   (`data/seeds/backtest_titles.csv`).
2. **Control set** (week 2): titles that buzzed in the same communities but were *not* adapted.
3. For each title, compute the first alert before the announcement. Report:
   - **hit rate**: share of adapted titles flagged before the deal;
   - **lead time**: months between alert and deal (median);
   - **false-alarm rate**: share of control titles that were flagged.
4. Google Trends is queried with a window ending at the announcement date, so its 0-100 scale
   only uses information that existed at the time.

## Known limits

- **Survivorship bias**: we start from known successes. The control set is there to correct it.
- **Launch effect**: every new book accelerates at launch; breadth and the awareness gap are meant
  to separate real phenomena from ordinary launches.
- **Announcement ≠ option date**: rights are often optioned months before the public announcement
  (Heartstopper was optioned about 18 months before Netflix's order), so the real window is shorter
  than the measured lead time.
- **Platform bias**: public APIs over-represent English-speaking communities.
- **Google Trends** is relative and sampled; values can change slightly between two queries.
