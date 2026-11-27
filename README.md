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

- **False-alarm test** on 16 popular stories with no adaptation listed: the same rule fired for
  **11 of the 12** truly never adapted (precision 29 %), and a trade-press check showed that 4
  "controls" had in fact been optioned (The Midnight Library; Netflix's Twisted series deal,
  flagged about three years earlier). Acceleration alone is a first filter, not a decision
  (`docs/04_method.md`, section 6).
- On the Grill 1 deck, speaker script and Q&A prep (`presentation/`).
- **Story Radar interface** (`web/`), running on live public data without API keys.

## The prototype: Story Radar

![Story Radar: this week's radar](presentation/assets/web_radar.png)

| Watchlist | Story page | Settings and extensions |
|---|---|---|
| ![Watchlist](presentation/assets/web_list.png) | ![Story page](presentation/assets/web_story.png) | ![Settings](presentation/assets/web_settings.png) |

A web interface in plain HTML, CSS and JavaScript (`web/`, no framework, no build step), served
by a small Python server (`server.py`, standard library only). In French, for the team.

- **Radar**: this week's key numbers, the polar radar (books on the left, webtoons on the right,
  the closer to the centre the higher the score), the strongest signals, and a map of community
  acceleration against mainstream awareness.
- **Liste**: every story with its cover, status, score and reason, filterable by keyword, format,
  status and genre, as cards or as a table.
- **Story page** (opens on the side): what to do, why, where the score comes from, the community
  curve, the Wikipedia curve, links to check the rights.
- **Tests**: the backtest on four past adaptations and the false-alarm test.
- **Méthode**: the three questions, the formula and the status rules with the current values,
  the sources and the limits.
- **Réglages**: every rule of the radar is a setting (weights, thresholds, scope), with three
  presets and a live view of the effect. Settings are kept in the browser and can be exported.
- **Extensions**: one idea = one file in `web/js/extensions/` (extra points, hidden stories). It
  shows up in the settings by itself. Three examples are included. How-to: `web/README.md`.

The browser recomputes the scores itself, so every setting changes the result at once. With the
reference settings it gives exactly the Python results (same scores and statuses for the 105
stories). Live sources: **AniList** (webtoon fans), **Open Library** (book readers),
**Wikipedia** (mainstream gauge). Scoring rules: `docs/04_method.md`, section 4b.

The first prototype in Streamlit (`app/streamlit_app.py`) is kept for reference.

**To send it by email** (no Python needed on the other side; first prototype's look):
- `exports/story_radar.html`: the whole interface in one file (5 MB), interactive (filters, radar
  map, watchlist with reasons, backtest, false alarms). Opens in any browser.
- `exports/story_radar_screenshots.pdf`: 4 screenshots (1 MB), for mail systems that block HTML.
- Rebuild them with `python scripts/export_static.py` and `python scripts/export_screenshots_pdf.py`.

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
  comment_ca_marche_FR.pdf how we collect the data and compute everything, in French (+ .md)
  feedback_log.md          jury feedback, round by round
presentation/
  OTG1_deck.pptx           On the Grill 1 deck (7 slides + 1 backup, speaker notes included)
  OTG1_deck_FR.pptx/.pdf   same deck in French (build_deck_fr.py), notes from the French script
  OTG1_speaker_script_FR.* French script split between the 4 speakers (md + pdf)
  fiche_Gabriel_FR.*       Gabriel's part explained, with expected questions (md + pdf)
  assets/prototype.png     screenshot of the prototype (used in the backup slide)
  OTG1_deck.pdf            same, as PDF
  OTG1_speaker_script.md   5-minute script split between the 4 speakers (+ French version)
  OTG1_speaker_script.pdf  same, as PDF (build_script_pdf.py rebuilds it)
  OTG1_jury_QA.md          expected questions, answers, questions for the jury
  build_deck.py            regenerates the deck from the data
src/radar/
  sources/                 anilist, openlibrary, wikipedia, google_trends, youtube, reddit, nyt_bestsellers
  watchlist.py             live watchlist: Wikipedia matching, score, status, reasons
  indicators.py            momentum, alerts (backtest)
  config.py                paths and API keys (read from .env)
scripts/run_watchlist.py   builds this week's watchlist from live public data (+ web/data/radar.json)
scripts/export_web_data.py writes web/data/radar.json, the data of the interface
scripts/run_poc.py         collects data and runs the backtest
scripts/run_control_test.py  false-alarm test on stories never adapted
server.py                  serves the interface on http://localhost:8600, runs the data refresh
web/                       Story Radar interface (HTML, CSS, JS); how to extend it: web/README.md
  js/extensions/           one idea per file, switched on in the settings
app/streamlit_app.py       first prototype, in Streamlit (kept for reference)
.streamlit/config.toml     its theme
data/
  seeds/backtest_titles.csv   adapted titles, deal dates and source links
  raw/                        collected data (backtest series, watchlist signals and history)
  processed/                  watchlist, backtest results and series used by the app and the deck
tests/test_smoke.py        indicator tests + headless run of the app
```

## Run it

**Windows, simplest:** double-click `lancer_app.bat`. The first time, it creates a Python
environment in `%USERPROFILE%\.mediawan-radar` (about 3 minutes), then it opens the interface at
http://localhost:8600. Close its window to stop it.

By hand:

```powershell
python server.py                        # open http://localhost:8600 (plain Python is enough)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt         # needed to collect data, rebuild the deck, run the tests
python scripts/run_watchlist.py         # refresh the live watchlist and the interface (about 10 minutes)
python scripts/run_poc.py --offline     # recompute the backtest from the saved snapshot
python scripts/run_poc.py               # refetch Google Trends + Wikipedia for the backtest
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
- **Le texte de l'oral en PDF** : `presentation/OTG1_speaker_script.pdf` (réparti entre les quatre
  orateurs, avec la version française).
- **L'interface** (Story Radar) : double-cliquer sur `lancer_app.bat` (Windows), ou
  `python server.py`, puis ouvrir http://localhost:8600. Elle tourne sur de vraies données
  publiques de cette semaine (AniList, Open Library, Wikipedia). Tous les réglages du radar se
  changent dans la page Réglages, et chaque nouvelle idée peut s'y brancher comme extension :
  le mode d'emploi est dans `web/README.md`.
- **Pour la suite** : le plan est dans `docs/05_roadmap.md`, la note de cadrage commencée dans
  `docs/scoping_note_draft.md`.
- **Partie technique** : `src/`, `scripts/`, `app/`, à ne pas montrer dans la présentation.
