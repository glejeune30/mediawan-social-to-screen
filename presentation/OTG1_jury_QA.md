# On the Grill 1: Q&A preparation (7 minutes)

Rule of thumb: answer in two sentences, then stop. If we don't know, say what we will check
before On the Grill 2.

## Questions we expect, and our answers

**"Why books and webtoons and not talent or formats?"**
Because the decision is concrete and expensive: an option on a story. Mediawan produces fiction
and animation, both adapt books and webtoons, and the rights window closes fast. Talent is a
natural extension: the authors behind the stories we flag.

**"TikTok is where BookTok happens. Why don't you use it?"**
TikTok's research API is only open to approved academic researchers, so it is not realistic in
three weeks. The same communities post on YouTube (BookTube, Shorts) and discuss on Reddit, which
have official APIs. We use TikTok Creative Center by hand for context.

**"Isn't your backtest biased? You picked titles that you already know became hits."**
We tested that. We took 16 popular stories with no adaptation listed, chosen before looking at
their curves. The same rule fired for 11 of the 12 that were truly never adapted: on its own,
search acceleration is not selective (precision 29 %). That is why the radar ranks stories
against each other and adds the mainstream gap and spreading. And 4 of the 16 had in fact been
optioned, including Netflix's Twisted series, which the rule flagged about three years before.

**"So how reliable is your radar?"**
Today: it catches 3 of 4 hits early, but alone it would raise too many alerts. Its value is to
shortlist: from thousands of stories to about ten a week that a development executive reads,
then checks the rights for. We will measure the combined rule on the same control group before
On the Grill 2.

**"Every new book grows at launch. How do you avoid flagging all of them?"**
Acceleration alone is not enough. A title also has to spread across several communities, and the
score rewards titles that grow in niche communities while the mainstream is still unaware.

**"How early is early enough?"**
That is one of our questions for you. Our first test gives the number of months between the
radar's alert and the public deal; we would like to know how much time your teams need to read,
assess and option a title.

**"What does the user actually see?"** → show the backup slide 8 (prototype screenshot).
A weekly watchlist, already running on live public data (AniList for webtoon fans, Open Library
for book readers, Wikipedia for the mainstream): each story with a status (Act now, Prepare,
Watch), a score from 0 to 100 and the reasons, a radar map, and a page per story with its curves.
Filters by keyword, format, genre and status.

**"Why AniList and Open Library?"**
They are the two big public communities where fans and readers log what they follow, with free
APIs and no key. AniList shows how fast a webtoon's fan base grows and whether an anime is already
announced; Open Library shows which recent books readers are suddenly adding. Both are biased
samples (AniList skews towards action and fantasy, Open Library is small), which is why YouTube
and Reddit come next.

**"Is the prototype using real data?"**
Yes: a snapshot of public data collected this week, with a refresh button. YouTube and Reddit are
coded and will be plugged in once we have the free API keys.

**"Is this legal and ethical?"**
Official APIs and public rankings only, respecting their terms. We store counts per title, never
usernames or private individuals.

**"What if a title is already optioned?"**
The radar does not know rights status. Prepare means "check who holds the rights"; a later version
could add a rights-check step, for example publisher catalogues and trade-press announcements.

**"How would Mediawan keep it running?"**
The prototype runs on a data snapshot with a refresh button; collection is scripted, so it can be
scheduled weekly at almost no cost (free API quotas).

## Questions we ask the jury

1. Which genres and formats matter most for Mediawan's labels right now?
2. How much warning is useful to your teams: 6 months? 18 months?
3. Could you share one or two past deals, won or lost, that we could test the radar against?
4. Do your teams already use a trend tool? What frustrates them about it?
