"""Story Radar: prototype of the From Social to Screen radar (Team 21).

Run from the repository root:  streamlit run app/streamlit_app.py
Data: data/processed (live watchlist snapshot + backtest). The "Refresh live data" button in the
"How it works" tab rebuilds the watchlist (scripts/run_watchlist.py, about 4 minutes).
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SEEDS = ROOT / "data" / "seeds"

INK, PLUM, LILAC, CORAL = "#1F1A2E", "#5B3F8C", "#F1EEF7", "#FF5A4E"
MUTED, GRID, SOFT = "#6B6680", "#E4E0EC", "#CFC8E0"
STATUS = {
    "Act now": {"bg": CORAL, "fg": "#FFFFFF", "dot": "🔴",
                "help": "Strong growth while the mainstream is still unaware: contact the rights holder."},
    "Prepare": {"bg": PLUM, "fg": "#FFFFFF", "dot": "🟣",
                "help": "Accelerating in its community: read it and check who holds the rights."},
    "Watch": {"bg": "#DCD6EA", "fg": INK, "dot": "⚪",
              "help": "Early or modest buzz: keep it on the list."},
    "Already adapted": {"bg": "#ECEAF1", "fg": MUTED, "dot": "⚫",
                        "help": "An adaptation is already listed: the rights are probably gone."},
}
STATUS_ORDER = list(STATUS)
TEAM = "Team 21 · Christine Durand, Fiona Loison, Gabin Dupre Duval, Gabriel Lejeune"

st.set_page_config(page_title="Story Radar · From Social to Screen", page_icon="📡",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
.block-container {{padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px;}}
.sr-hero {{background:{INK}; border-radius:18px; padding:26px 30px 24px; color:#fff;
  display:flex; justify-content:space-between; gap:24px; align-items:flex-end;
  position:relative; overflow:hidden; margin-bottom:14px;}}
.sr-hero .rings {{position:absolute; right:-70px; top:-90px; width:280px; height:280px;
  border-radius:50%; border:1.5px solid rgba(155,125,210,.45);
  box-shadow:0 0 0 42px rgba(155,125,210,.07), 0 0 0 84px rgba(155,125,210,.045);}}
.sr-hero .ping {{position:absolute; right:150px; top:34px; width:12px; height:12px;
  border-radius:50%; background:{CORAL}; box-shadow:0 0 0 7px rgba(255,90,78,.25);}}
.sr-hero .k {{color:{CORAL}; font-weight:700; letter-spacing:.08em; font-size:.74rem;
  text-transform:uppercase;}}
.sr-hero .t {{font-family:"Source Serif 4","Source Serif Pro",Georgia,serif; font-size:2.5rem;
  font-weight:700; line-height:1.1; margin:6px 0 8px;}}
.sr-hero .s {{color:{SOFT}; font-size:1.02rem; max-width:620px; line-height:1.45;}}
.sr-hero .meta {{text-align:right; color:{SOFT}; font-size:.84rem; line-height:1.6;
  position:relative; z-index:1;}}
.sr-hero .meta b {{color:#fff;}}
.sr-kpi {{background:{LILAC}; border-radius:14px; padding:14px 18px; height:100%;}}
.sr-kpi .v {{font-size:1.85rem; font-weight:700; color:{INK}; line-height:1.15;}}
.sr-kpi .l {{color:{MUTED}; font-size:.84rem; margin-top:2px; line-height:1.35;}}
.sr-chip {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:.74rem;
  font-weight:700; letter-spacing:.02em; white-space:nowrap;}}
.sr-card {{border:1px solid {GRID}; border-radius:14px; padding:14px; display:flex; gap:14px;
  background:#fff; min-height:168px; margin-bottom:12px;}}
.sr-card img, .sr-card .ph {{width:78px; height:114px; object-fit:cover; border-radius:8px;
  flex-shrink:0; background:{LILAC};}}
.sr-card .tt {{font-weight:700; font-size:1.02rem; color:{INK}; line-height:1.25; margin:6px 0 2px;}}
.sr-card .by {{color:{MUTED}; font-size:.8rem; margin-bottom:6px;}}
.sr-card .sig {{font-size:.83rem; color:{INK}; line-height:1.45;}}
.sr-card .sig span {{color:{MUTED};}}
.sr-card .sc {{float:right; font-weight:700; color:{INK}; font-size:.85rem;}}
.sr-h {{font-family:"Source Serif 4","Source Serif Pro",Georgia,serif; font-size:1.35rem;
  font-weight:700; color:{INK}; margin:14px 0 2px;}}
.sr-cap {{color:{MUTED}; font-size:.88rem; margin-bottom:10px;}}
.sr-box {{background:{LILAC}; border-radius:14px; padding:16px 18px; height:100%;}}
.sr-box .n {{display:inline-flex; align-items:center; justify-content:center; width:30px;
  height:30px; border-radius:50%; background:{CORAL}; color:#fff; font-weight:700;
  margin-bottom:8px; box-shadow:0 0 0 5px rgba(255,90,78,.18);}}
.sr-box .q {{font-weight:700; color:{INK}; font-size:1.02rem; margin-bottom:4px;}}
.sr-box .d {{color:{INK}; font-size:.9rem; line-height:1.45;}}
.sr-box .d span {{color:{MUTED};}}
.sr-why li {{margin-bottom:6px; line-height:1.45;}}
.sr-foot {{color:{MUTED}; font-size:.8rem; margin-top:30px; border-top:1px solid {GRID};
  padding-top:12px;}}
div[data-testid="stTabs"] button p {{font-size:1rem; font-weight:600;}}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data
DATA_FILES = ["watchlist.csv", "watchlist_series.csv", "watchlist_meta.json",
              "backtest_results.csv", "poc_timeseries.csv"]


def data_stamp() -> tuple:
    """Modification times of the data files: the cache is rebuilt when a file changes."""
    return tuple((PROCESSED / f).stat().st_mtime if (PROCESSED / f).exists() else 0
                 for f in DATA_FILES)


@st.cache_data
def load(stamp: tuple):
    wl = pd.read_csv(PROCESSED / "watchlist.csv") if (PROCESSED / "watchlist.csv").exists() else None
    series = (pd.read_csv(PROCESSED / "watchlist_series.csv")
              if (PROCESSED / "watchlist_series.csv").exists() else None)
    meta = (json.loads((PROCESSED / "watchlist_meta.json").read_text(encoding="utf-8"))
            if (PROCESSED / "watchlist_meta.json").exists() else {})
    bt = pd.read_csv(PROCESSED / "backtest_results.csv",
                     parse_dates=["announcement_date", "radar_alert", "first_wikipedia_page"])
    ts = pd.read_csv(PROCESSED / "poc_timeseries.csv", parse_dates=["date"])
    if wl is not None:
        wl["adaptation"] = wl["adaptation"].fillna("None listed")
        wl["author"] = wl["author"].fillna("")
        wl["genres"] = wl["genres"].fillna("")
        wl["status_rank"] = wl["status"].map({s: i for i, s in enumerate(STATUS_ORDER)})
        wl = wl.sort_values(["status_rank", "score"], ascending=[True, False])
    return wl, series, meta, bt, ts


wl, series, meta, bt, ts = load(data_stamp())


def chip(status: str) -> str:
    s = STATUS[status]
    return f'<span class="sr-chip" style="background:{s["bg"]};color:{s["fg"]}">{status}</span>'


def esc(x) -> str:
    return html.escape("" if pd.isna(x) else str(x))


def style(fig: go.Figure, height: int = 380, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", color=INK, size=13),
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        title=dict(text=title, font=dict(size=15, color=INK), x=0, xanchor="left") if title else None,
        hoverlabel=dict(bgcolor="white", font_color=INK, bordercolor=GRID),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color=MUTED)),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED), zeroline=False)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED), zeroline=False)
    return fig


def fmt_months(v: float) -> str:
    return f"{v:.0f}" if v >= 10 else f"{v:.1f}"


# ---------------------------------------------------------------- header
n_stories = len(wl) if wl is not None else 0
snap = pd.Timestamp(meta["snapshot"]).strftime("%d %B %Y") if meta.get("snapshot") else "not built yet"
st.markdown(f"""
<div class="sr-hero">
  <div class="rings"></div><div class="ping"></div>
  <div>
    <div class="k">From Social to Screen · Mediawan × Albert School</div>
    <div class="t">Story Radar</div>
    <div class="s">Which book or webtoon should Mediawan's development teams look at, and option,
    before its rights become expensive?</div>
  </div>
  <div class="meta">Data snapshot <b>{snap}</b><br><b>{n_stories}</b> stories tracked<br>
  AniList · Open Library · Wikipedia</div>
</div>
""", unsafe_allow_html=True)

flagged = bt[bt["lead_months"].notna()]
counts = wl["status"].value_counts() if wl is not None else pd.Series(dtype=int)
k = st.columns(5)
kpis = [
    (f'<span style="color:{CORAL}">{counts.get("Act now", 0)}</span>', "stories to act on now"),
    (f'<span style="color:{PLUM}">{counts.get("Prepare", 0)}</span>', "stories to prepare"),
    (f"{n_stories}", f'{meta.get("books", 0)} books · {meta.get("webtoons", 0)} webtoons tracked'),
    (f"{len(flagged)} / {len(bt)}", "past adaptations flagged before the deal"),
    (f"{flagged['lead_months'].median():.0f} months", "median warning in the backtest"),
]
for col, (v, label) in zip(k, kpis):
    col.markdown(f'<div class="sr-kpi"><div class="v">{v}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)

st.write("")
tab_radar, tab_story, tab_bt, tab_how = st.tabs(
    ["📡  This week's radar", "📖  Story page", "⏱  Backtest", "🧭  How it works"])

# ================================================================ RADAR
with tab_radar:
    if wl is None:
        st.info("No watchlist yet. Run `python scripts/run_watchlist.py` (about 4 minutes).")
    else:
        f1, f2, f3, f4, f5 = st.columns([1.7, 2.2, 2.3, 1.8, 1.2], vertical_alignment="bottom")
        query = f1.text_input("Search", placeholder="Title or author")
        fmt = f2.segmented_control("Format", ["All", "Books", "Webtoons"], default="All")
        stat = f3.pills("Status", ["Act now", "Prepare", "Watch"], selection_mode="multi",
                        default=["Act now", "Prepare", "Watch"])
        all_genres = sorted({g.strip() for gs in wl["genres"] for g in gs.split(",") if g.strip()})
        genres = f4.multiselect("Genre", all_genres, placeholder="All genres")
        show_adapted = f5.toggle("Show adapted", value=False)

        d = wl.copy()
        if query:
            q = query.lower()
            d = d[d["title"].str.lower().str.contains(q, regex=False)
                  | d["author"].str.lower().str.contains(q, regex=False)]
        if fmt == "Books":
            d = d[d["format"] == "Book"]
        elif fmt == "Webtoons":
            d = d[d["format"] == "Webtoon"]
        keep = list(stat or []) + (["Already adapted"] if show_adapted else [])
        d = d[d["status"].isin(keep)]
        if genres:
            d = d[d["genres"].apply(lambda s: any(g in s for g in genres))]

        # ---- top signals
        st.markdown('<div class="sr-h">Top signals this week</div>'
                    '<div class="sr-cap">The highest-scoring stories after your filters, with the '
                    'reasons behind their status.</div>', unsafe_allow_html=True)
        top = d[d["status"] != "Already adapted"].head(6)
        if top.empty:
            st.caption("No story matches these filters.")
        cols = st.columns(2)
        for i, r in enumerate(top.itertuples()):
            reasons = r.why.split(" | ")
            img = (f'<img src="{esc(r.cover_url)}" alt="">' if isinstance(r.cover_url, str)
                   else '<div class="ph"></div>')
            cols[i % 2].markdown(f"""
<div class="sr-card">{img}<div style="flex:1;min-width:0">
  {chip(r.status)} <span class="sc">{r.score:.0f}/100</span>
  <div class="tt">{esc(r.title)}</div>
  <div class="by">{esc(r.author) or "Unknown author"} · {esc(r.format)}{f" · {int(r.year)}" if pd.notna(r.year) else ""}</div>
  <div class="sig">{esc(reasons[0])}<br><span>{esc(reasons[1])}</span></div>
</div></div>""", unsafe_allow_html=True)

        # ---- radar map
        st.markdown('<div class="sr-h">Radar map</div>'
                    '<div class="sr-cap">Up: the story accelerates faster than others of its format. '
                    'Left: the mainstream has not noticed it yet. The shaded corner is where the '
                    '<b>Act now</b> rule applies.</div>', unsafe_allow_html=True)
        m = d.copy()
        m["aware"] = 100 * (1 - m["unaware"])
        jitter = m["story_id"].map(lambda s: (zlib.crc32(s.encode()) % 1000) / 1000)
        m["x"] = np.where(m["wiki_article"].isna(), 1 + 7 * jitter, m["aware"])
        m["y"] = 100 * m["accel"]
        size_pct = m.groupby("format")["score"].rank(pct=True).fillna(0.5)
        fig = go.Figure()
        fig.add_shape(type="rect", x0=-2, x1=50, y0=90, y1=101, fillcolor="rgba(255,90,78,.10)",
                      line=dict(width=0), layer="below")
        fig.add_annotation(x=1, y=100, text="ACT NOW ZONE", showarrow=False, xanchor="left",
                           yanchor="top", font=dict(size=11, color=CORAL))
        fig.add_vrect(x0=-2, x1=9.5, fillcolor="rgba(91,63,140,.05)", line_width=0, layer="below")
        fig.add_annotation(x=4.5, y=-4, text="no Wikipedia page", showarrow=False,
                           font=dict(size=11, color=MUTED))
        for s in STATUS_ORDER:
            g = m[m["status"] == s]
            if g.empty:
                continue
            fig.add_trace(go.Scatter(
                x=g["x"], y=g["y"], mode="markers", name=s,
                marker=dict(size=9 + 14 * size_pct[g.index], color=STATUS[s]["bg"],
                            line=dict(width=1.5, color="white"), opacity=0.9),
                customdata=np.stack([g["title"], g["format"], g["fan_signal"], g["mainstream"],
                                     g["score"]], axis=-1),
                hovertemplate=("<b>%{customdata[0]}</b> · %{customdata[1]}<br>%{customdata[2]}"
                               "<br>Wikipedia: %{customdata[3]}<br>Score %{customdata[4]:.0f}/100"
                               f"<extra>{s}</extra>")))
        fig.update_layout(margin=dict(l=75, r=20, t=40, b=75))
        fig.update_xaxes(range=[-2, 102],
                         title="Mainstream awareness: Wikipedia views per month →",
                         tickvals=[4.5, 32.5, 55, 77.5, 100],
                         ticktext=["no page", "1k", "10k", "100k", "1M"])
        fig.update_yaxes(range=[-8, 103], title="Acceleration in its community (percentile) →")
        fig = style(fig, 480)
        fig.update_layout(margin=dict(l=75, r=20, t=40, b=75))
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})

        # ---- table
        st.markdown(f'<div class="sr-h">Watchlist</div><div class="sr-cap">{len(d)} stories · '
                    'sorted by status, then score · click a column header to sort</div>',
                    unsafe_allow_html=True)
        t = d.assign(Status=d["status"].map(lambda s: f'{STATUS[s]["dot"]} {s}'))
        st.dataframe(
            t[["cover_url", "title", "author", "format", "Status", "score", "fan_signal",
               "mainstream", "adaptation", "genres", "source_url"]],
            column_config={
                "cover_url": st.column_config.ImageColumn("", width="small"),
                "title": st.column_config.TextColumn("Story", width="medium"),
                "author": st.column_config.TextColumn("By"),
                "format": st.column_config.TextColumn("Format", width="small"),
                "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100,
                                                         format="%d", color="primary"),
                "fan_signal": st.column_config.TextColumn("Community signal", width="medium"),
                "mainstream": st.column_config.TextColumn("Mainstream"),
                "adaptation": st.column_config.TextColumn("Adaptation"),
                "genres": st.column_config.TextColumn("Genres"),
                "source_url": st.column_config.LinkColumn("Source", display_text="Open ↗"),
            },
            hide_index=True, width="stretch", height=560, row_height=64)

# ================================================================ STORY PAGE
with tab_story:
    if wl is None:
        st.info("No watchlist yet.")
    else:
        options = wl[wl["status"] != "Already adapted"]["story_id"].tolist() + \
            wl[wl["status"] == "Already adapted"]["story_id"].tolist()
        label = dict(zip(wl["story_id"], wl["title"] + "  ·  " + wl["status"] + "  ·  " +
                         wl["score"].map(lambda v: f"{v:.0f}/100")))
        sid = st.selectbox("Story", options, format_func=lambda s: label[s])
        r = wl[wl["story_id"] == sid].iloc[0]
        left, right = st.columns([1, 3.2], gap="large")
        with left:
            if isinstance(r.cover_url, str):
                st.image(r.cover_url, width="stretch")
        with right:
            st.markdown(f'{chip(r.status)}<div class="sr-h" style="font-size:2rem;margin-top:6px">'
                        f'{esc(r.title)}</div><div class="sr-cap">{esc(r.author) or "Unknown author"}'
                        f' · {esc(r.format)}{f" · first published {int(r.year)}" if pd.notna(r.year) else ""}'
                        f' · {esc(r.genres)}</div>', unsafe_allow_html=True)
            st.progress(int(r.score), text=f"Emergence score: {r.score:.0f}/100")
            st.markdown(f"**What to do:** {STATUS[r.status]['help']}")
            items = "".join(f"<li>{esc(x)}</li>" for x in r.why.split(" | "))
            st.markdown(f'<div class="sr-h" style="font-size:1.1rem">Why this status</div>'
                        f'<ul class="sr-why">{items}</ul>', unsafe_allow_html=True)
            links = [f"[{'AniList' if r.format == 'Webtoon' else 'Open Library'} page ↗]({r.source_url})"]
            if isinstance(r.wiki_article, str):
                links.append(f"[Wikipedia ↗](https://en.wikipedia.org/wiki/{r.wiki_article.replace(' ', '_')})")
            st.markdown("  ·  ".join(links))

        c1, c2 = st.columns(2, gap="large")
        s = series[series["story_id"] == sid] if series is not None else pd.DataFrame()
        with c1:
            if r.format == "Webtoon":
                f = s[s["kind"] == "fans"].copy()
                f["x"] = pd.to_datetime(f["x"])
                f = f.sort_values("x")
                fig = go.Figure(go.Scatter(x=f["x"], y=f["value"], mode="lines+markers",
                                           line=dict(color=CORAL, width=2.5),
                                           marker=dict(size=9, color=CORAL),
                                           hovertemplate="%{x|%d %b %Y}: %{y:,} fans<extra></extra>"))
                fig.update_yaxes(title="fans on AniList", tickformat=",")
                st.plotly_chart(style(fig, 330, "Community: fans who listed it on AniList"),
                                width="stretch", theme=None, config={"displayModeBar": False})
            else:
                f = s[s["kind"] == "reader_activity"]
                fig = go.Figure(go.Bar(x=f["x"], y=f["value"], marker_color=[SOFT, CORAL],
                                       text=f["value"].map(lambda v: f"{v:.0f}"),
                                       textposition="outside", width=0.5,
                                       hovertemplate="%{x}: %{y:.0f} logs<extra></extra>"))
                fig.update_yaxes(title="reading-log entries")
                st.plotly_chart(style(fig, 330, "Community: Open Library reader activity"),
                                width="stretch", theme=None, config={"displayModeBar": False})
        with c2:
            w = s[s["kind"] == "wikipedia_views"].copy()
            if w.empty:
                st.markdown(f'<div class="sr-box" style="margin-top:40px"><div class="q">'
                            'No English Wikipedia page yet</div><div class="d">The mainstream '
                            'has not caught on. Heartstopper had no page either when Netflix '
                            'ordered the series.</div></div>', unsafe_allow_html=True)
            else:
                w["x"] = pd.to_datetime(w["x"])
                fig = go.Figure(go.Bar(x=w["x"], y=w["value"], marker_color=PLUM,
                                       hovertemplate="%{x|%b %Y}: %{y:,} views<extra></extra>"))
                fig.update_yaxes(title="views per month", tickformat="~s")
                st.plotly_chart(style(fig, 330, "Mainstream: Wikipedia page views per month"),
                                width="stretch", theme=None, config={"displayModeBar": False})

# ================================================================ BACKTEST
with tab_bt:
    lo, hi = flagged["lead_months"].min(), flagged["lead_months"].max()
    b = st.columns(4)
    for col, (v, label) in zip(b, [
            (f"{len(flagged)} / {len(bt)}", "adaptations flagged before the deal was announced"),
            (f"{flagged['lead_months'].median():.0f} months", "median warning"),
            (f"{fmt_months(lo)} to {fmt_months(hi)}", "months of warning, range"),
            ("1 missed", "Heartstopper: slow, steady growth")]):
        col.markdown(f'<div class="sr-kpi"><div class="v">{v}</div><div class="l">{label}</div></div>',
                     unsafe_allow_html=True)
    st.markdown('<div class="sr-h">Would the radar have seen them coming?</div>'
                '<div class="sr-cap">Four recent adaptations. One rule, fixed in advance and the same '
                'for every title: Google searches over 3 months at least double the 6 months before, '
                'two months in a row. A month only counts once it is over.</div>',
                unsafe_allow_html=True)
    rows = bt.iloc[::-1].reset_index(drop=True)
    fig = go.Figure()
    for i, r in rows.iterrows():
        if pd.notna(r.radar_alert):
            fig.add_trace(go.Scatter(x=[r.radar_alert, r.announcement_date], y=[r.title] * 2,
                                     mode="lines", line=dict(color=CORAL, width=6),
                                     hoverinfo="skip", showlegend=False))
        lead = (f"{fmt_months(r.lead_months)} months early" if pd.notna(r.lead_months)
                else "missed: slow burner")
        fig.add_annotation(x=pd.Timestamp("2024-03-01"), y=r.title, text=f"<b>{lead}</b>",
                           showarrow=False, xanchor="left",
                           font=dict(color=CORAL if pd.notna(r.lead_months) else MUTED, size=13))
    fig.add_trace(go.Scatter(x=rows["radar_alert"], y=rows["title"], mode="markers",
                             name="Radar alert", marker=dict(size=15, color=CORAL),
                             hovertemplate="Radar alert: %{x|%b %Y}<extra>%{y}</extra>"))
    fig.add_trace(go.Scatter(x=rows["first_wikipedia_page"], y=rows["title"], mode="markers",
                             name="First Wikipedia page",
                             marker=dict(size=15, color="white", line=dict(color=PLUM, width=3)),
                             hovertemplate="First Wikipedia page: %{x|%d %b %Y}<extra>%{y}</extra>"))
    fig.add_trace(go.Scatter(x=rows["announcement_date"], y=rows["title"], mode="markers",
                             name="Adaptation deal announced", marker=dict(size=15, color=INK),
                             hovertemplate="Deal announced: %{x|%d %b %Y}<extra>%{y}</extra>"))
    fig.update_xaxes(range=[pd.Timestamp("2018-01-01"), pd.Timestamp("2025-06-01")],
                     showgrid=True, gridcolor=GRID, dtick="M12", tickformat="%Y")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(style(fig, 360), width="stretch", theme=None, config={"displayModeBar": False})

    with st.expander("See the search and Wikipedia curves for each title"):
        title = st.selectbox("Title", bt["title"].tolist(), key="bt_title")
        row = bt[bt["title"] == title].iloc[0]
        fig = go.Figure()
        for source, window, name, color in [("google_trends", "full", "Google searches", CORAL),
                                            ("wikipedia", "full", "Wikipedia page views", PLUM)]:
            sdf = ts[(ts.title == title) & (ts.source == source) & (ts.window == window)]
            if not sdf.empty:
                fig.add_trace(go.Scatter(x=sdf["date"], y=100 * sdf["value"] / sdf["value"].max(),
                                         name=name, mode="lines", line=dict(color=color, width=2)))
        fig.add_vline(x=row["announcement_date"], line_dash="dash", line_color=INK)
        fig.add_annotation(x=row["announcement_date"], y=104, text="deal", showarrow=False,
                           font=dict(color=INK, size=11))
        if pd.notna(row["radar_alert"]):
            fig.add_vline(x=row["radar_alert"], line_color=CORAL)
            fig.add_annotation(x=row["radar_alert"], y=104, text="alert", showarrow=False,
                               font=dict(color=CORAL, size=11))
        fig.update_yaxes(title="index (100 = peak)", range=[0, 110])
        st.plotly_chart(style(fig, 360), width="stretch", theme=None,
                        config={"displayModeBar": False})
    st.caption("Known successes only. Next step: titles that buzzed but were never adapted, to count "
               "false alarms. Lead time is measured to the public announcement; options are often "
               "signed earlier, so the real window is shorter.")

# ================================================================ HOW IT WORKS
with tab_how:
    st.markdown('<div class="sr-h">Three questions, asked every week for every story</div>',
                unsafe_allow_html=True)
    q = st.columns(3)
    boxes = [
        ("Is the buzz accelerating?",
         "Webtoons: growth of AniList fans over 90 days, plus activity now. "
         "Books: Open Library reader activity in the last 24 hours versus the previous week.",
         "Ranked within each format: 60 % of the score."),
        ("Is it spreading?",
         "Its Wikipedia page is new (less than a year) or its views grow by 25 % or more.",
         "15 % of the score. YouTube and Reddit will add more communities."),
        ("Is the mainstream still unaware?",
         "No English Wikipedia page, or fewer than about 6,000 views a month.",
         "25 % of the score."),
    ]
    for i, (col, (title, d1, d2)) in enumerate(zip(q, boxes)):
        col.markdown(f'<div class="sr-box"><div class="n">{i + 1}</div><div class="q">{title}</div>'
                     f'<div class="d">{d1}<br><span>{d2}</span></div></div>',
                     unsafe_allow_html=True)
    st.markdown('<div class="sr-h">Status rules</div>', unsafe_allow_html=True)
    st.markdown(
        f"{chip('Act now')} acceleration in the top 10 % of its format **and** the mainstream still "
        f"unaware &nbsp;&nbsp; {chip('Prepare')} acceleration in the top 40 % &nbsp;&nbsp; "
        f"{chip('Watch')} the rest &nbsp;&nbsp; {chip('Already adapted')} an adaptation is listed "
        "on AniList or Wikipedia", unsafe_allow_html=True)

    st.markdown('<div class="sr-h">Sources</div>', unsafe_allow_html=True)
    src = pd.DataFrame([
        ["AniList", "Webtoon fans (community)", "Public API, no key", "🟢 Live"],
        ["Open Library", "Book readers (community)", "Public API, no key", "🟢 Live"],
        ["Wikipedia", "Mainstream awareness", "Official API, no key", "🟢 Live"],
        ["Google Trends", "Mainstream searches (backtest)", "Unofficial client", "🟢 Live"],
        ["YouTube", "BookTube and webtoon reviewers", "Official API, free key", "🟡 Code ready, needs a key"],
        ["Reddit", "Fan communities", "Official API, free key", "🟡 Code ready, needs a key"],
        ["NYT Best Sellers", "Ground truth for books", "Official API, free key", "🟡 Code ready, needs a key"],
        ["Webtoon and Wattpad charts", "New entries, fast climbers", "Public rankings", "⚪ Planned"],
    ], columns=["Source", "What it tells us", "Access", "Status"])
    st.dataframe(src, hide_index=True, width="stretch")
    st.markdown("""
**Limits we know about**
- Each community source covers its own audience: AniList fans skew towards action and fantasy
  manhwa, Open Library readers are a small, English-speaking sample.
- AniList only lists anime adaptations: a live-action drama deal will not appear there.
- Scores are relative: every week, the top of the list is the strongest signal *this week*.
- Public data only, aggregate counts only, no personal data.
""")
    st.markdown('<div class="sr-h">Data</div>', unsafe_allow_html=True)
    st.caption(f"Snapshot: {snap}. Wikipedia views up to {meta.get('wikipedia_last_month', '?')}.")
    if st.button("Refresh live data (about 4 minutes)", type="primary"):
        with st.spinner("Collecting AniList, Open Library and Wikipedia data…"):
            res = subprocess.run([sys.executable, "-X", "utf8",
                                  str(ROOT / "scripts" / "run_watchlist.py")],
                                 capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Refresh failed. Last lines of the log:")
            st.code((res.stdout + res.stderr)[-1500:])

st.markdown(f'<div class="sr-foot">{TEAM} · Business Deep Dive Mediawan × Albert School · '
            'Public data only, aggregate counts, no personal data.</div>', unsafe_allow_html=True)
