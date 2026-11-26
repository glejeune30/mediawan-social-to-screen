# 1. Framing: problem, decision, scope

## The business problem

Stories now break in online communities (BookTok, BookTube, Reddit, Webtoon, Wattpad) months or
years before they reach the mainstream. By the time a title tops the bestseller charts or trends on
Google, the screen rights are usually optioned or expensive.

Three recent adaptations show how short the window can be:

| Story | Born on | Deal announced | What it tells us |
|---|---|---|---|
| **Heartstopper** | Webcomic on Tumblr and Tapas (2016) | Netflix UK orders the series, 20 Jan 2021 | No English Wikipedia page about it existed when Netflix ordered it (the first one, about the TV series, was created a week later). The mainstream gauge was blind; the fandom was not. |
| **Fourth Wing** | Romantasy novel, May 2023, BookTok | Amazon MGM Studios develops a series, Oct 2023 | About 5 months between publication and the deal. |
| **Solo Leveling** | Korean webnovel (2016), webtoon (2018) | Anime announced at Anime Expo, 3 Jul 2022 | Years of growing global fandom before the deal. |
| **A Good Girl's Guide to Murder** | YA thriller (2019), BookTok | BBC Three commissions a series, Sept 2022 | Community buzz in 2020-2021, deal in 2022. |

Sources: see `data/seeds/backtest_titles.csv` (one source link per deal).

## The decision our radar informs

> **"Which book or webtoon should Mediawan's development and acquisition teams look at, and
> option, this quarter, before its rights become expensive?"**

- **Users:** development executives and acquisition teams of Mediawan's production labels
  (fiction and animation).
- **Rhythm:** a weekly watchlist.
- **Output per story:** an emergence score and one of three statuses:
  - **Watch**: early buzz, keep an eye on it.
  - **Prepare**: accelerating and spreading; read it, check who holds the rights.
  - **Act now**: strong, broad acceleration while the mainstream is still unaware; contact the
    rights holder.

## Axis and scope

- **Axis:** *Content trends* from the brief (emerging intellectual properties), with *consumption
  trends* as context (what audiences start to read).
- **Scope (v1):** books and webtoons/webcomics with screen potential: YA, romantasy, fantasy,
  thriller, romance, manhwa. English-speaking communities first, because they are the largest
  public sources; origin of a title (Korea, UK, US, France) is recorded but not filtered.
- **Out of scope (v1):** talent (possible extension: the authors behind the stories), music, games.

## How we will judge our own radar

1. **Earliness:** how many months before the deal announcement the radar raised an alert.
2. **Reliability:** how many alerts were false alarms, tested on a control group of titles that
   buzzed but were not adapted.
3. **Usefulness:** can a development executive act on the watchlist without a data analyst?
