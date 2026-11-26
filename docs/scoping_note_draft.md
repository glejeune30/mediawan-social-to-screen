# From Social to Screen: scoping note (draft v0.1, 26 November 2026)

*Business Deep Dive Mediawan × Albert School. Final version due Thursday 10 December, 18:00
(2 to 4 pages). This draft is written after the first proof of concept and will be updated after
each On the Grill.*

## 1. The decision our radar informs

Mediawan's labels adapt books and webtoons for fiction and animation. Stories now gain their
audience in online communities (BookTok, BookTube, Reddit, Webtoon, Wattpad) long before they
reach bestseller lists or general search. By the time a story is mainstream, its screen rights are
usually optioned or expensive. Three recent deals show how short the window is: Amazon MGM Studios
moved on *Fourth Wing* about five months after the novel came out; Netflix ordered *Heartstopper*
when no English Wikipedia page existed about it yet; *Solo Leveling* had four years of global fandom
before its anime was announced.

Our radar informs one decision:

> **Which book or webtoon should Mediawan's development and acquisition teams look at, and option,
> this quarter, before its rights become expensive?**

Each week, every tracked story receives an emergence score (0-100) and a status: **Watch** (early
buzz), **Prepare** (accelerating and spreading: read it, check who holds the rights) or **Act now**
(strong, broad growth while the mainstream is still unaware: contact the rights holder).

## 2. Axis and scope

We chose the *content trends* axis of the brief, applied to emerging intellectual properties, with
*consumption trends* as context. Version 1 covers books and webtoons/webcomics with screen potential
(YA, romantasy, fantasy, thriller, romance, manhwa), in English-speaking communities, which are the
largest public sources. The country of origin is recorded but not filtered. Talent (the authors
behind flagged stories) is the natural extension.

## 3. Sources and why we chose them

We separate **early signals**, where stories are born, from a **mainstream gauge**, which tells us
who already knows.

| Role | Source | Why |
|---|---|---|
| Early signal (live) | AniList API | Webtoon fans list the series they follow; daily snapshots show how fast a fan base grows; adaptations are listed |
| Early signal (live) | Open Library API | Readers log what they want to read or are reading; recent activity versus the previous week shows acceleration |
| Early signal | YouTube Data API | Official and free; BookTube and webtoon reviewers react early; history can be rebuilt by publication date |
| Early signal | Reddit API | Fan communities recommend titles first; official API; used for the live radar (limited history) |
| Early signal | Webtoon and Wattpad public rankings | New entries and fast climbers; snapshots within the terms of use |
| Mainstream gauge | Google Trends | Long history (2004), global; shows when the general public starts searching |
| Mainstream gauge | Wikipedia pageviews | Official API, history since 2015; the creation of a page marks mainstream recognition |

TikTok and Instagram are not used directly: TikTok's research API is limited to approved academic
researchers and Instagram offers no public search API. The same communities are visible on YouTube
and Reddit. We store only aggregate counts per title; no usernames and no private individuals.

## 4. Method

1. **Track titles**: seed list from rankings, plus titles discovered in Reddit posts and YouTube
   video titles, matched across sources to one canonical story.
2. **Measure, per title and source**: momentum (last 3 months versus the 6 months before), a
   minimum level to filter noise, breadth (on how many sources it accelerates) and the awareness
   gap (niche momentum minus mainstream momentum). Every indicator only uses data available at
   the time.
3. **Score**: 50 % strength of acceleration, 30 % breadth, 20 % awareness gap; thresholds give the
   three statuses. Weights will be calibrated on the backtest.
4. **Backtest**: on adapted titles (positive set) and on titles that buzzed but were never adapted
   (control set), we measure hit rate, lead time before the public deal, and false-alarm rate.

## 5. First results (proof of concept, 26 November)

With free search data only (Google Trends) and one rule fixed in advance (searches over the last 3
months at least double the previous 6 months, two months in a row), the radar would have raised an
alert before the deal for **3 of 4** recent adaptations:

| Story | Radar alert | First Wikipedia page | Deal announced | Warning |
|---|---|---|---|---|
| Solo Leveling | Dec 2018 | Aug 2019 | 3 Jul 2022 (anime) | 42 months |
| A Good Girl's Guide to Murder | Apr 2020 | Sep 2021 | 5 Sep 2022 (BBC Three) | 28 months |
| Fourth Wing | Jun 2023 | Jun 2023 | Oct 2023 (Amazon MGM) | 3.5 months |
| Heartstopper | not flagged | Jan 2021 (a week after the deal) | 20 Jan 2021 (Netflix) | missed |

Lead time is counted from the end of the alert month, when the data is actually available.
*Heartstopper* was missed: its searches grew tenfold between 2018 and 2020, but never doubled
within a few months. This calls for a slow-growth indicator and for the community sources.

**False alarms.** We applied the same rule to 16 popular stories with no adaptation listed,
chosen before looking at their curves. A trade-press check showed that 4 had in fact been
optioned (*The Midnight Library* in 2020; Netflix's deal for the *Twisted* series in January 2025,
which the rule had flagged about three years earlier). On the 12 truly never-adapted stories, the
rule fired 11 times: precision is 29 %. Search acceleration is therefore a first filter, not a
decision: the radar ranks stories against each other, adds the mainstream gap and spreading, and
leaves the rights check to a human, in the trade press.

## 5b. Prototype (26 November)

*Story Radar* already runs on live public data without API keys: webtoons trending among AniList
fans and recent fiction trending among Open Library readers, each matched to its English Wikipedia
page. Every story gets a status (Act now, Prepare, Watch, Already adapted), a score and the
reasons, on a radar map and a filterable watchlist, with one page per story.

## 6. Limits

- **Selectivity**: on its own, the acceleration rule raised an alert for 11 of 12 never-adapted
  popular stories (see 5). The score has to combine it with the other questions.
- **Rights status**: the automatic check missed 4 deals in 16 titles; rights must be checked in
  the trade press before any contact.
- **Launch effect**: every new book accelerates at launch; breadth and the awareness gap should
  separate phenomena from ordinary launches.
- **Announcement versus option date**: rights are often optioned months before the public
  announcement, so the real window is shorter than the measured lead time.
- **Coverage**: public APIs over-represent English-speaking communities; TikTok is seen indirectly.
- **Ambiguous names**: a title that is also a common word (for example *Heartstopper*) mixes
  unrelated searches; we will use Google Trends topics and title + author queries.
- **Rights status**: the radar does not know whether a title is already optioned; *Prepare* means
  checking it.

## 7. Next steps

Before On the Grill 2 (4 December): YouTube and Reddit collection, a combined rule that cuts
false alarms (tested on the same control group), prototype v1 (weekly watchlist, filters by
keyword and genre, refresh button). Before the
final deliverables: calibrated score, current top 10 with recommendations prioritised by impact
and feasibility, and this note finalised.
