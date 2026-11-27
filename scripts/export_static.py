"""Exports the Story Radar interface as ONE self-contained HTML file that can be sent by email.

Run:  python scripts/export_static.py
Output: exports/story_radar.html  (opens in any browser, no Python needed; works offline except
        the cover images, which load from AniList / Open Library when online)

It shows the data snapshot in data/processed: watchlist with filters, top signals, radar map,
backtest, false-alarm test and method.
"""
from __future__ import annotations

import html
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "exports" / "story_radar.html"

INK, PLUM, LILAC, CORAL, MUTED, GRID, SOFT = ("#1F1A2E", "#5B3F8C", "#F1EEF7", "#FF5A4E",
                                              "#6B6680", "#E4E0EC", "#CFC8E0")
STATUS = {"Act now": (CORAL, "#fff"), "Prepare": (PLUM, "#fff"), "Watch": ("#DCD6EA", INK),
          "Already adapted": ("#ECEAF1", MUTED)}
TEAM = "Team 21 · Christine Durand, Fiona Loison, Gabin Dupre Duval, Gabriel Lejeune"


def esc(x) -> str:
    return html.escape("" if pd.isna(x) else str(x))


def style(fig, height):
    fig.update_layout(height=height, paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family="Arial, Helvetica, sans-serif", color=INK, size=13),
                      margin=dict(l=10, r=10, t=50, b=10),
                      hoverlabel=dict(bgcolor="white", font_color=INK, bordercolor=GRID),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                  font=dict(color=MUTED)))
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED), zeroline=False,
                     automargin=True, title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED), zeroline=False,
                     automargin=True, title_font=dict(color=MUTED), title_standoff=12)
    return fig


def radar_map(wl: pd.DataFrame) -> go.Figure:
    m = wl[wl["status"] != "Already adapted"].copy()
    jitter = m["story_id"].map(lambda s: (zlib.crc32(s.encode()) % 1000) / 1000)
    views = m["wiki_views_month"].clip(lower=1)
    on_log = 32 + 68 * ((np.log10(views) - 2) / 4).clip(0, 1)
    m["x"] = np.where(m["wiki_article"].isna(), 2 + 21 * jitter, on_log)
    m["y"] = 100 * m["accel"]
    thr = 32 + 68 * ((np.log10(6000) - 2) / 4)
    size = m.groupby("format")["score"].rank(pct=True).fillna(0.5)
    fig = go.Figure()
    fig.add_vrect(x0=-2, x1=26, fillcolor="rgba(91,63,140,.05)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=-2, x1=thr, y0=90, y1=101, fillcolor="rgba(255,90,78,.10)",
                  line=dict(width=0), layer="below")
    fig.add_annotation(x=thr - 1, y=100.5, text="ACT NOW ZONE", showarrow=False, xanchor="right",
                       yanchor="top", font=dict(size=11, color=CORAL))
    fig.add_annotation(x=12, y=-5, text="no Wikipedia page", showarrow=False,
                       font=dict(size=11, color=MUTED))
    for s in ["Act now", "Prepare", "Watch"]:
        g = m[m["status"] == s]
        fig.add_trace(go.Scatter(
            x=g["x"], y=g["y"], mode="markers", name=s,
            marker=dict(size=9 + 14 * size[g.index], color=STATUS[s][0],
                        line=dict(width=1.5, color="white"), opacity=0.9),
            customdata=np.stack([g["title"], g["format"], g["fan_signal"], g["mainstream"],
                                 g["score"]], axis=-1),
            hovertemplate=("<b>%{customdata[0]}</b> · %{customdata[1]}<br>%{customdata[2]}"
                           "<br>Wikipedia: %{customdata[3]}<br>Score %{customdata[4]:.0f}/100"
                           f"<extra>{s}</extra>")))
    style(fig, 480)
    fig.update_xaxes(range=[-2, 102], title="Mainstream awareness: Wikipedia views per month →",
                     tickvals=[12, 32, 49, 66, 83, 100],
                     ticktext=["no page", "100", "1k", "10k", "100k", "1M"])
    fig.update_yaxes(range=[-9, 103], title="Acceleration in its community (percentile) →")
    return fig


def backtest_timeline(bt: pd.DataFrame) -> go.Figure:
    rows = bt.iloc[::-1].reset_index(drop=True)
    fig = go.Figure()
    for _, r in rows.iterrows():
        if pd.notna(r.radar_alert):
            fig.add_trace(go.Scatter(x=[r.radar_alert, r.announcement_date], y=[r.title] * 2,
                                     mode="lines", line=dict(color=CORAL, width=6),
                                     hoverinfo="skip", showlegend=False))
        lead = (f"{r.lead_months:.0f} months early" if pd.notna(r.lead_months) and r.lead_months >= 10
                else f"{r.lead_months:.1f} months early" if pd.notna(r.lead_months)
                else "missed: slow burner")
        fig.add_annotation(x=pd.Timestamp("2024-03-01"), y=r.title, text=f"<b>{lead}</b>",
                           showarrow=False, xanchor="left",
                           font=dict(color=CORAL if pd.notna(r.lead_months) else MUTED, size=13))
    fig.add_trace(go.Scatter(x=rows["radar_alert"], y=rows["title"], mode="markers",
                             name="Radar alert", marker=dict(size=15, color=CORAL)))
    fig.add_trace(go.Scatter(x=rows["first_wikipedia_page"], y=rows["title"], mode="markers",
                             name="First Wikipedia page",
                             marker=dict(size=15, color="white", line=dict(color=PLUM, width=3))))
    fig.add_trace(go.Scatter(x=rows["announcement_date"], y=rows["title"], mode="markers",
                             name="Adaptation deal announced", marker=dict(size=15, color=INK)))
    style(fig, 380)
    fig.update_xaxes(range=[pd.Timestamp("2018-01-01"), pd.Timestamp("2025-06-01")],
                     dtick="M12", tickformat="%Y")
    fig.update_yaxes(showgrid=False)
    fig.update_layout(margin=dict(l=230, t=50))
    return fig


def main() -> None:
    wl = pd.read_csv(P / "watchlist.csv")
    meta = json.loads((P / "watchlist_meta.json").read_text(encoding="utf-8"))
    bt = pd.read_csv(P / "backtest_results.csv",
                     parse_dates=["announcement_date", "radar_alert", "first_wikipedia_page"])
    ctrl = pd.read_csv(P / "control_results.csv")
    summ = json.loads((P / "backtest_summary.json").read_text(encoding="utf-8"))

    order = {s: i for i, s in enumerate(STATUS)}
    wl["rank"] = wl["status"].map(order)
    wl = wl.sort_values(["rank", "score"], ascending=[True, False])
    stories = []
    for r in wl.itertuples():
        wiki = (f"https://en.wikipedia.org/wiki/{r.wiki_article.replace(' ', '_')}"
                if isinstance(r.wiki_article, str) else "")
        stories.append({
            "title": r.title, "author": "" if pd.isna(r.author) else r.author,
            "format": r.format, "year": None if pd.isna(r.year) else int(r.year),
            "genres": "" if pd.isna(r.genres) else r.genres, "status": r.status,
            "score": int(r.score), "fan": r.fan_signal, "main": r.mainstream,
            "adapt": r.adaptation if isinstance(r.adaptation, str) else "None listed",
            "why": r.why.split(" | "), "cover": r.cover_url if isinstance(r.cover_url, str) else "",
            "src": r.source_url, "wiki": wiki,
        })

    map_html = radar_map(wl).to_html(full_html=False, include_plotlyjs=True,
                                     config={"displayModeBar": False, "responsive": True})
    bt_html = backtest_timeline(bt).to_html(full_html=False, include_plotlyjs=False,
                                            config={"displayModeBar": False, "responsive": True})

    flagged = bt[bt["lead_months"].notna()]
    counts = wl["status"].value_counts()
    snap = pd.Timestamp(meta["snapshot"]).strftime("%d %B %Y")

    ctrl_rows = "".join(
        f"<tr><td>{esc(r.title)}</td><td>{esc(r.format)}</td><td>{esc(r.popularity)}</td>"
        f"<td>{esc(r.radar_alert) if pd.notna(r.radar_alert) else 'no alert'}</td>"
        f"<td>{esc(r.verdict)}</td>"
        f"<td>{esc(r.deal) if isinstance(r.deal, str) else ''}</td></tr>"
        for r in ctrl.itertuples())

    page = TEMPLATE
    for k, v in {
        "__SNAP__": snap, "__N__": str(len(wl)), "__BOOKS__": str(meta.get("books", "")),
        "__WEBTOONS__": str(meta.get("webtoons", "")),
        "__ACT__": str(counts.get("Act now", 0)), "__PREP__": str(counts.get("Prepare", 0)),
        "__FLAG__": f"{len(flagged)} / {len(bt)}",
        "__MEDIAN__": f"{flagged['lead_months'].median():.0f} months",
        "__CTRL_FLAG__": f"{summ['controls_flagged']} / {summ['controls_total']}",
        "__PREC__": f"{summ['precision']:.0%}", "__FOUND__": str(summ["controls_found_adapted"]),
        "__CTRL_ROWS__": ctrl_rows, "__MAP__": map_html, "__BT__": bt_html, "__TEAM__": TEAM,
        "__DATA__": json.dumps(stories, ensure_ascii=False).replace("</", "<\\/"),
        "__STATUS__": json.dumps(STATUS),
    }.items():
        page = page.replace(k, v)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"saved {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Story Radar · From Social to Screen · Team 21</title>
<style>
:root { --ink:#1F1A2E; --plum:#5B3F8C; --lilac:#F1EEF7; --coral:#FF5A4E; --muted:#6B6680;
        --grid:#E4E0EC; --soft:#CFC8E0; }
* { box-sizing: border-box; }
body { margin:0; font-family:"Segoe UI", Calibri, Arial, sans-serif; color:var(--ink);
       background:#fff; font-size:15px; line-height:1.5; }
.wrap { max-width:1280px; margin:0 auto; padding:22px 24px 40px; }
.hero { background:var(--ink); color:#fff; border-radius:18px; padding:26px 30px 24px;
        display:flex; justify-content:space-between; align-items:flex-end; gap:24px;
        position:relative; overflow:hidden; flex-wrap:wrap; }
.hero .rings { position:absolute; right:-70px; top:-90px; width:280px; height:280px;
        border-radius:50%; border:1.5px solid rgba(155,125,210,.45);
        box-shadow:0 0 0 42px rgba(155,125,210,.07), 0 0 0 84px rgba(155,125,210,.045); }
.hero .ping { position:absolute; right:150px; top:34px; width:12px; height:12px; border-radius:50%;
        background:var(--coral); box-shadow:0 0 0 7px rgba(255,90,78,.25); }
.k { color:var(--coral); font-weight:700; letter-spacing:.08em; font-size:12px;
     text-transform:uppercase; }
.hero .t { font-family:Cambria, Georgia, serif; font-size:40px; font-weight:700; line-height:1.1;
        margin:6px 0 8px; }
.hero .s { color:var(--soft); font-size:16px; max-width:620px; }
.hero .meta { text-align:right; color:var(--soft); font-size:13px; line-height:1.6;
        position:relative; z-index:1; }
.hero .meta b { color:#fff; }
nav { display:flex; gap:22px; border-bottom:1px solid var(--grid); margin:18px 0 6px;
      flex-wrap:wrap; }
nav a { color:var(--ink); text-decoration:none; font-weight:600; padding:8px 0; }
nav a:hover { color:var(--coral); }
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px,1fr)); gap:12px;
        margin-top:14px; }
.kpi { background:var(--lilac); border-radius:14px; padding:14px 18px; }
.kpi .v { font-size:28px; font-weight:700; line-height:1.15; }
.kpi .l { color:var(--muted); font-size:13px; }
h2 { font-family:Cambria, Georgia, serif; font-size:24px; margin:30px 0 2px; }
.cap { color:var(--muted); font-size:14px; margin-bottom:12px; }
.filters { display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin:12px 0 16px; }
.filters input[type=text] { padding:9px 12px; border:1px solid var(--grid); border-radius:10px;
        background:var(--lilac); min-width:220px; font-size:14px; }
.seg button, .pill { border:1px solid var(--grid); background:#fff; padding:7px 13px;
        font-size:14px; cursor:pointer; color:var(--ink); }
.seg button:first-child { border-radius:10px 0 0 10px; }
.seg button:last-child { border-radius:0 10px 10px 0; }
.seg button.on { border-color:var(--coral); color:var(--coral); font-weight:700; }
.pill { border-radius:999px; }
.pill.on { border-color:var(--coral); background:rgba(255,90,78,.08); color:var(--coral);
        font-weight:700; }
.chip { display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px;
        font-weight:700; white-space:nowrap; }
.cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(380px,1fr)); gap:12px; }
.card { border:1px solid var(--grid); border-radius:14px; padding:14px; display:flex; gap:14px; }
.card img, .card .ph { width:78px; height:114px; object-fit:cover; border-radius:8px;
        flex-shrink:0; background:var(--lilac); }
.card .tt { font-weight:700; font-size:16px; margin:6px 0 2px; }
.card .by { color:var(--muted); font-size:12.5px; margin-bottom:6px; }
.card .sig { font-size:13px; }
.card .sig span { color:var(--muted); }
.card .sc { float:right; font-weight:700; font-size:13px; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th { text-align:left; background:var(--lilac); padding:9px 10px; font-weight:600;
     position:sticky; top:0; }
td { padding:8px 10px; border-bottom:1px solid var(--grid); vertical-align:middle; }
tr.row { cursor:pointer; }
tr.row:hover td { background:#FAF9FC; }
td.cv img { width:40px; height:58px; object-fit:cover; border-radius:5px; display:block; }
.bar { background:#EEEAF5; border-radius:6px; height:8px; width:90px; display:inline-block;
       vertical-align:middle; margin-right:6px; overflow:hidden; }
.bar i { display:block; height:100%; background:var(--coral); }
tr.det td { background:#FAF9FC; font-size:13.5px; color:var(--ink); }
tr.det ul { margin:4px 0 4px 18px; padding:0; }
.tablewrap { max-height:640px; overflow:auto; border:1px solid var(--grid); border-radius:12px; }
.box { background:var(--lilac); border-radius:14px; padding:16px 18px; }
.grid3 { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px,1fr)); gap:12px; }
.n { display:inline-flex; width:30px; height:30px; border-radius:50%; background:var(--coral);
     color:#fff; font-weight:700; align-items:center; justify-content:center; margin-bottom:8px;
     box-shadow:0 0 0 5px rgba(255,90,78,.18); }
.foot { color:var(--muted); font-size:12.5px; margin-top:34px; border-top:1px solid var(--grid);
        padding-top:12px; }
a { color:var(--plum); }
td a { white-space:nowrap; }
@media print { nav, .filters { display:none; } .tablewrap { max-height:none; overflow:visible; } }
</style></head>
<body><div class="wrap">

<div class="hero"><div class="rings"></div><div class="ping"></div>
  <div><div class="k">From Social to Screen · Mediawan × Albert School · Team 21</div>
  <div class="t">Story Radar</div>
  <div class="s">Which book or webtoon should Mediawan's development teams look at, and option,
  before its rights become expensive?</div></div>
  <div class="meta">Data snapshot <b>__SNAP__</b><br><b>__N__</b> stories tracked<br>
  AniList · Open Library · Wikipedia</div>
</div>

<div class="kpis">
  <div class="kpi"><div class="v" style="color:var(--coral)">__ACT__</div><div class="l">stories to act on now</div></div>
  <div class="kpi"><div class="v" style="color:var(--plum)">__PREP__</div><div class="l">stories to prepare</div></div>
  <div class="kpi"><div class="v">__N__</div><div class="l">__BOOKS__ books · __WEBTOONS__ webtoons tracked</div></div>
  <div class="kpi"><div class="v">__FLAG__</div><div class="l">past adaptations flagged before the deal</div></div>
  <div class="kpi"><div class="v">__MEDIAN__</div><div class="l">median warning in the backtest</div></div>
</div>

<nav><a href="#radar">📡 This week's radar</a><a href="#map">🗺 Radar map</a>
<a href="#list">📋 Watchlist</a><a href="#backtest">⏱ Backtest</a><a href="#how">🧭 How it works</a></nav>

<h2 id="radar">Top signals this week</h2>
<div class="cap">The highest-scoring stories after your filters, with the reasons behind their status.</div>
<div class="filters">
  <input id="q" type="text" placeholder="Search a title or author">
  <div class="seg" id="fmt"><button data-v="All" class="on">All</button><button data-v="Book">Books</button><button data-v="Webtoon">Webtoons</button></div>
  <div id="st"><button class="pill on" data-v="Act now">Act now</button> <button class="pill on" data-v="Prepare">Prepare</button> <button class="pill on" data-v="Watch">Watch</button> <button class="pill" data-v="Already adapted">Already adapted</button></div>
</div>
<div class="cards" id="cards"></div>

<h2 id="map">Radar map</h2>
<div class="cap">Up: the story accelerates faster than others of its format. Left: the mainstream has not
noticed it yet. The shaded corner is where the <b>Act now</b> rule applies. Hover a dot to see the story.</div>
__MAP__

<h2 id="list">Watchlist</h2>
<div class="cap"><span id="count"></span> · sorted by status, then score · click a row to see why</div>
<div class="tablewrap"><table><thead><tr><th></th><th>Story</th><th>Status</th><th>Score</th>
<th>Community signal</th><th>Mainstream</th><th>Adaptation</th><th>Format</th><th>Source</th></tr></thead>
<tbody id="rows"></tbody></table></div>

<h2 id="backtest">Backtest: would the radar have seen them coming?</h2>
<div class="cap">Four recent adaptations. One rule, fixed in advance and the same for every title: Google
searches over 3 months at least double the 6 months before, two months in a row.</div>
__BT__
<h2>And the false alarms?</h2>
<div class="cap">The same rule on 16 popular stories with no adaptation listed, chosen before looking at
their curves. A trade-press check showed that __FOUND__ of them had in fact been optioned.</div>
<div class="kpis">
  <div class="kpi"><div class="v">__CTRL_FLAG__</div><div class="l">never-adapted stories that still raised an alert: false alarms</div></div>
  <div class="kpi"><div class="v">__PREC__</div><div class="l">of all alerts were followed by a deal (precision)</div></div>
  <div class="kpi"><div class="v">__FOUND__</div><div class="l">stories we thought free were already optioned: rights need a manual check</div></div>
</div>
<p><b>What it means:</b> search acceleration catches the hits, but it also fires for almost every popular
story. It is a first filter, not a decision: the radar only flags the top 10 % of each format, adds the
mainstream gap, and will add spreading across communities (YouTube, Reddit). Bonus: for the Twisted
series, the rule fired about three years before Netflix bought it.</p>
<div class="tablewrap" style="max-height:none"><table><thead><tr><th>Story</th><th>Format</th>
<th>Popularity</th><th>Radar alert</th><th>Verdict</th><th>Deal found</th></tr></thead>
<tbody>__CTRL_ROWS__</tbody></table></div>

<h2 id="how">How it works</h2>
<div class="grid3">
  <div class="box"><div class="n">1</div><div><b>Is the buzz accelerating?</b></div>
  <div>Webtoons: growth of AniList fans over 90 days. Books: Open Library reader activity in the last
  24 hours versus the previous week. Ranked within each format.</div></div>
  <div class="box"><div class="n">2</div><div><b>Is it spreading?</b></div>
  <div>Its Wikipedia page is new or its views are growing. YouTube and Reddit will add more
  communities.</div></div>
  <div class="box"><div class="n">3</div><div><b>Is the mainstream still unaware?</b></div>
  <div>No English Wikipedia page, or fewer than about 6,000 views a month.</div></div>
</div>
<p style="margin-top:14px"><span class="chip" style="background:var(--coral);color:#fff">Act now</span>
acceleration in the top 10 % of its format and the mainstream still unaware ·
<span class="chip" style="background:var(--plum);color:#fff">Prepare</span> top 40 % ·
<span class="chip" style="background:#DCD6EA">Watch</span> the rest ·
<span class="chip" style="background:#ECEAF1;color:var(--muted)">Already adapted</span> an adaptation is
listed on AniList or Wikipedia.</p>
<p>Public data only, official APIs, aggregate counts, no personal data. Statuses are relative: every week,
the top of the list is the strongest signal of that week. Rights are not checked automatically.</p>

<div class="foot">__TEAM__ · Business Deep Dive Mediawan × Albert School · Static export of the Story Radar
prototype, data snapshot __SNAP__.</div>
</div>

<script>
const DATA = __DATA__;
const STATUS = __STATUS__;
const state = { q: "", fmt: "All", st: new Set(["Act now", "Prepare", "Watch"]) };
const e = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const chip = s => `<span class="chip" style="background:${STATUS[s][0]};color:${STATUS[s][1]}">${e(s)}</span>`;
function visible() {
  const q = state.q.toLowerCase();
  return DATA.filter(d => (state.fmt === "All" || d.format === state.fmt) && state.st.has(d.status)
    && (!q || d.title.toLowerCase().includes(q) || d.author.toLowerCase().includes(q)));
}
function render() {
  const v = visible();
  const top = v.filter(d => d.status !== "Already adapted").slice(0, 6);
  document.getElementById("cards").innerHTML = top.length ? top.map(d => `
    <div class="card">${d.cover ? `<img src="${e(d.cover)}" alt="">` : `<div class="ph"></div>`}
    <div style="flex:1;min-width:0">${chip(d.status)} <span class="sc">${d.score}/100</span>
    <div class="tt">${e(d.title)}</div>
    <div class="by">${e(d.author || "Unknown author")} · ${e(d.format)}${d.year ? " · " + d.year : ""}</div>
    <div class="sig">${e(d.why[0])}<br><span>${e(d.why[1])}</span></div></div></div>`).join("")
    : "<p class='cap'>No story matches these filters.</p>";
  document.getElementById("count").textContent = v.length + " stories";
  document.getElementById("rows").innerHTML = v.map((d, i) => `
    <tr class="row" data-i="${i}"><td class="cv">${d.cover ? `<img src="${e(d.cover)}" alt="" loading="lazy">` : ""}</td>
    <td><b>${e(d.title)}</b><br><span style="color:var(--muted);font-size:12.5px">${e(d.author)}</span></td>
    <td>${chip(d.status)}</td><td><span class="bar"><i style="width:${d.score}%"></i></span>${d.score}</td>
    <td>${e(d.fan)}</td><td>${e(d.main)}</td><td>${e(d.adapt)}</td><td>${e(d.format)}</td>
    <td><a href="${e(d.src)}" target="_blank" rel="noopener">Open ↗</a></td></tr>
    <tr class="det" id="det${i}" style="display:none"><td></td><td colspan="8"><b>Why this status</b>
    <ul>${d.why.map(w => `<li>${e(w)}</li>`).join("")}</ul>${d.genres ? "Genres: " + e(d.genres) + " · " : ""}
    ${d.wiki ? `<a href="${e(d.wiki)}" target="_blank" rel="noopener">Wikipedia ↗</a>` : "No Wikipedia page"}</td></tr>`).join("");
  document.querySelectorAll("tr.row").forEach(r => r.onclick = ev => {
    if (ev.target.tagName === "A") return;
    const det = document.getElementById("det" + r.dataset.i);
    det.style.display = det.style.display === "none" ? "" : "none";
  });
}
document.getElementById("q").oninput = ev => { state.q = ev.target.value; render(); };
document.querySelectorAll("#fmt button").forEach(b => b.onclick = () => {
  document.querySelectorAll("#fmt button").forEach(x => x.classList.remove("on"));
  b.classList.add("on"); state.fmt = b.dataset.v; render(); });
document.querySelectorAll("#st button").forEach(b => b.onclick = () => {
  b.classList.toggle("on");
  b.classList.contains("on") ? state.st.add(b.dataset.v) : state.st.delete(b.dataset.v); render(); });
render();
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
