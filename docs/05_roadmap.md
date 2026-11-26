# 5. Roadmap and team organisation

## Key dates (from the brief)

| Date | Milestone | Weight |
|---|---|---|
| Mon 23 Nov | Kick-off | |
| **Fri 27 Nov, 13:00** | **On the Grill 1**: 5 min pitch + 7 min Q&A | 30 % |
| **Fri 4 Dec, 11:00** | **On the Grill 2**: prototype demo + how we used the feedback | 50 % with final deliverables |
| **Thu 10 Dec, 18:00** | Final deliverables uploaded on Inside (prototype + 2-4 page scoping note) | |
| Fri 11 Dec, 11:00 | Final at Mediawan (best teams) | |
| **Sun 13 Dec, 23:59** | Peer review | 20 % |

## Plan

| When | What | Done when |
|---|---|---|
| Thu 26 Nov | Framing, benchmark, sources, proof of concept on 4 deals, OTG1 deck and script | Deck rehearsed in 5 min |
| Thu 26 Nov | ✅ Prototype v0 "Story Radar" on live public data (AniList, Open Library, Wikipedia) | Done: watchlist, radar map, story pages, backtest |
| Fri 27 Nov | **OTG1**, write down every piece of jury feedback in `docs/feedback_log.md` | Feedback logged |
| Sat 28 Nov - Tue 1 Dec | API keys (YouTube, Reddit, NYT), YouTube + Reddit collection, title matching, control set of ~10 titles | Data for 4 sources in `data/processed` |
| Tue 1 - Wed 2 Dec | Indicators on all sources, emergence score, backtest with false-alarm rate | Backtest table with hit rate, lead time, false alarms |
| Wed 2 - Thu 3 Dec | Prototype v1 (live watchlist + backtest view), OTG2 deck with a "what we changed" slide | Demo runs end to end |
| **Fri 4 Dec** | **OTG2** | Feedback logged |
| Sat 5 - Tue 8 Dec | Calibrate weights, extend backtest, current top 10 with recommendations by impact × feasibility | Watchlist ready to show |
| Wed 9 Dec | Scoping note (2-4 pages, English) final, repository cleaned | Note proofread by two people |
| **Thu 10 Dec, 18:00** | Upload on Inside (aim for Wed evening) | |
| Fri 11 Dec | Final rehearsal and final | |
| Sun 13 Dec | Peer review | |

## Roles (adapt to team size)

| Role | Owns |
|---|---|
| Data engineer | API keys, collectors, storage, refresh button |
| Data scientist | Title matching, indicators, score, backtest, control set |
| Product / front | Streamlit app, demo script |
| Business lead | Benchmark, scoping note, decks, speaker scripts, jury questions |
