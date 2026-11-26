"""Radar prototype (v0). Run:  streamlit run app/streamlit_app.py

Works on the data snapshot in data/processed. The "Refresh data" button reruns the
collection script (scripts/run_poc.py).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SEEDS = ROOT / "data" / "seeds"

st.set_page_config(page_title="From Social to Screen — IP Radar", layout="wide")


@st.cache_data
def load():
    ts = pd.read_csv(PROCESSED / "poc_timeseries.csv", parse_dates=["date"])
    res = pd.read_csv(PROCESSED / "backtest_results.csv",
                      parse_dates=["announcement_date", "radar_alert", "first_wikipedia_page"])
    seeds = pd.read_csv(SEEDS / "backtest_titles.csv")
    return ts, res, seeds


st.title("From Social to Screen — early-warning radar for adaptable IP")
st.caption("Prototype v0 · snapshot data · backtest on four recent adaptations")

if not (PROCESSED / "backtest_results.csv").exists():
    st.warning("No data yet. Run `python scripts/run_poc.py` first.")
    st.stop()

ts, res, seeds = load()

with st.sidebar:
    st.header("Filters")
    keyword = st.text_input("Keyword", "")
    categories = st.multiselect("Category", sorted(seeds["category"].unique()),
                                default=sorted(seeds["category"].unique()))
    if st.button("Refresh data"):
        with st.spinner("Collecting public data…"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / "run_poc.py")], check=False)
        st.cache_data.clear()
        st.rerun()

view = res[res["category"].isin(categories)]
if keyword:
    view = view[view["title"].str.contains(keyword, case=False)]

c1, c2, c3 = st.columns(3)
flagged = view["lead_months"].notna().sum()
c1.metric("Titles in backtest", len(view))
c2.metric("Flagged before the deal", f"{flagged} / {len(view)}")
c3.metric("Median warning", f"{view['lead_months'].median():.0f} months"
          if flagged else "—")

st.subheader("Backtest: radar alert versus adaptation announcement")
st.dataframe(
    view[["title", "category", "radar_alert", "first_wikipedia_page", "announcement_date",
          "lead_months", "announcement_event"]].rename(columns={
              "radar_alert": "Radar alert", "first_wikipedia_page": "First Wikipedia page",
              "announcement_date": "Deal announced", "lead_months": "Warning (months)",
              "announcement_event": "Deal"}),
    hide_index=True, width="stretch")

st.subheader("Signals over time")
title = st.selectbox("Title", view["title"].tolist())
if title:
    row = view[view["title"] == title].iloc[0]
    fig = go.Figure()
    for source, window, name in [("wikipedia", "full", "Wikipedia pageviews"),
                                 ("google_trends", "full", "Google search interest")]:
        s = ts[(ts.title == title) & (ts.source == source) & (ts.window == window)]
        if s.empty:
            continue
        y = 100 * s["value"] / s["value"].max()
        fig.add_trace(go.Scatter(x=s["date"], y=y, name=name, mode="lines"))
    fig.add_vline(x=row["announcement_date"], line_dash="dash",
                  annotation_text="Deal announced")
    if pd.notna(row["radar_alert"]):
        fig.add_vline(x=row["radar_alert"], line_color="#FF5A4E",
                      annotation_text="Radar alert")
    if pd.notna(row["first_wikipedia_page"]):
        fig.add_vline(x=row["first_wikipedia_page"], line_dash="dot", line_color="#5B3F8C",
                      annotation_text="First Wikipedia page", annotation_position="bottom right")
    fig.update_layout(yaxis_title="Index (100 = peak)", height=420,
                      margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")

st.info("Next: add YouTube and Reddit as early signals, a live watchlist scored "
        "Watch / Prepare / Act now, and a control group to measure false alerts.")
