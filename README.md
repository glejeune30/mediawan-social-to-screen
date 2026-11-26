# From Social to Screen: an early-warning radar for adaptable stories

Business Deep Dive **Mediawan × Albert School** (23 November - 11 December 2026).
**Team 21:** Christine Durand, Fiona Loison, Gabin Dupre Duval, Gabriel Lejeune.

> **The decision we inform:** which book or webtoon should Mediawan's development teams look at,
> and option, this quarter, before its rights become expensive?

The radar follows stories (books, webtoons) across online communities and public data, and gives
each one a weekly emergence score and a status: **Watch**, **Prepare** or **Act now**.

## Where we are (26 November)

- Framing, benchmark, sources and method written (`docs/`).
- **Proof of concept**: with free Google Trends data and one rule fixed in advance, the radar would
  have flagged **3 of 4** recent adaptations before the deal was announced:

| Story | Radar alert | Deal announced | Warning |
|---|---|---|---|
| Solo Leveling | Dec 2018 | Jul 2022 (anime, Crunchyroll / A-1 Pictures) | 42 months |
| A Good Girl's Guide to Murder | Apr 2020 | Sep 2022 (BBC Three) | 28 months |
| Fourth Wing | Jun 2023 | Oct 2023 (Amazon MGM Studios) | 3.5 months |
| Heartstopper | not flagged (slow, steady growth) | Jan 2021 (Netflix) | missed |

- On the Grill 1 deck, speaker script and Q&A prep (`presentation/`).
- Prototype v0 (Streamlit) on the backtest snapshot (`app/`).

## Repository map

```
README.md
docs/
  01_framing.md            problem, decision, axis, scope, success criteria
  02_benchmark.md          existing trend tools and what they miss
  03_sources.md            sources, access, history, rules (ToS, no personal data)
  04_method.md             indicators, alert rule, score, backtest protocol, limits
  05_roadmap.md            plan to 13 December, roles
  scoping_note_draft.md    draft of the 2-4 page deliverable
  feedback_log.md          jury feedback, round by round
presentation/
  OTG1_deck.pptx           On the Grill 1 deck (7 slides, speaker notes included)
  OTG1_deck.pdf            same, as PDF
  OTG1_speaker_script.md   5-minute script with timings (+ French version)
  OTG1_jury_QA.md          expected questions, answers, questions for the jury
  build_deck.py            regenerates the deck from the data
src/radar/
  sources/                 wikipedia, google_trends, youtube, reddit, nyt_bestsellers
  indicators.py            momentum, alerts, emergence score, status
  config.py                paths and API keys (read from .env)
scripts/run_poc.py         collects data and runs the backtest
app/streamlit_app.py       prototype (filters, backtest table, curves, refresh button)
data/
  seeds/backtest_titles.csv   adapted titles, deal dates and source links
  raw/, processed/            data snapshot used by the deck and the app
tests/test_smoke.py        indicator tests + headless run of the app
```

## Run it

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_poc.py --offline     # recompute from the saved snapshot (no internet needed)
python scripts/run_poc.py               # refetch Google Trends + Wikipedia (about 3 minutes)
streamlit run app/streamlit_app.py      # open the prototype
python presentation/build_deck.py       # rebuild the deck with the latest numbers
python tests/test_smoke.py              # checks
```

Keep the virtual environment outside OneDrive if the folder is synced, or exclude `.venv`.

For YouTube, Reddit and NYT: copy `.env.example` to `.env` and add your own keys (never commit `.env`).

## Rules we follow

Public data only, official APIs where possible, terms of use respected, aggregate counts only
(no usernames, no private individuals). The case brief belongs to Mediawan and is not in this
repository; any public post about the case needs Mediawan's approval first.

## Key dates

| Date | Milestone |
|---|---|
| Fri 27 Nov, 13:00 | On the Grill 1 (5 min + 7 min Q&A), 30 % |
| Fri 4 Dec, 11:00 | On the Grill 2: prototype demo + use of feedback |
| Thu 10 Dec, 18:00 | Final deliverables on Inside |
| Fri 11 Dec | Final at Mediawan (best teams) |
| Sun 13 Dec, 23:59 | Peer review, 20 % |

---

## En bref (français)

- **Pour vendredi** : le diapo `presentation/OTG1_deck.pptx` (notes de l'orateur incluses), le texte
  à dire `presentation/OTG1_speaker_script.md` (anglais + traduction française), et la préparation
  des questions du jury `presentation/OTG1_jury_QA.md`.
- **Pour la suite** : le plan est dans `docs/05_roadmap.md`, la note de cadrage commencée dans
  `docs/scoping_note_draft.md`.
- **Partie technique** : `src/`, `scripts/`, `app/`, à ne pas montrer dans la présentation.
