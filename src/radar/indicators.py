"""Emergence indicators, computed on monthly series.

Plain-language version (the one we present):
  1. Is the buzz accelerating?        -> momentum: last 3 months versus the 6 months before
  2. Is it spreading?                 -> breadth: on how many sources it accelerates
  3. Is the mainstream still unaware? -> awareness gap: niche momentum minus mainstream momentum

The rule is fixed *before* looking at the results and applied identically to every title.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Minimum level for a signal to count, per source (avoids alerts on near-zero noise).
FLOORS = {
    "google_trends": 2.0,     # points on the 0-100 Google Trends scale
    "wikipedia": 1_000.0,     # human pageviews per month
    "youtube_videos": 5.0,    # videos per month
    "reddit_posts": 5.0,      # posts per week
}

MOMENTUM_THRESHOLD = 2.0      # recent level at least twice the recent past
CONSECUTIVE = 2               # ... for two months in a row


def momentum(series: pd.Series, recent: int = 3, past: int = 6) -> pd.Series:
    """Ratio of the mean of the last `recent` points to the mean of the `past` points
    just before them. Uses only data available at each date (no look-ahead)."""
    s = series.astype(float)
    recent_mean = s.rolling(recent, min_periods=recent).mean()
    past_mean = s.shift(recent).rolling(past, min_periods=past).mean()
    m = recent_mean / past_mean.replace(0, np.nan)
    # Starting from exactly zero (a new title): strong momentum if the recent level is real.
    # Missing history (NaN) stays NaN: no history is not the same as zero interest.
    new_entrant = (past_mean == 0) & (recent_mean > 0)
    m[new_entrant] = np.inf
    return m


def source_alerts(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """df: columns date, value (monthly). Adds momentum, level, alert (bool)."""
    out = df.sort_values("date").copy()
    out["level"] = out["value"].rolling(3, min_periods=3).mean()
    out["momentum"] = momentum(out["value"])
    hot = (out["momentum"] >= MOMENTUM_THRESHOLD) & (out["level"] >= FLOORS.get(source, 0))
    # require CONSECUTIVE hot months in a row
    out["alert"] = hot.rolling(CONSECUTIVE, min_periods=CONSECUTIVE).sum() == CONSECUTIVE
    out["source"] = source
    return out


def first_alert(alerts: pd.DataFrame, before: pd.Timestamp | None = None,
                after: pd.Timestamp | None = None) -> pd.Timestamp | None:
    """Earliest alert month.

    - `before`: only months that were *complete* before this date count (no look-ahead: a monthly
      point is only known once the month is over).
    - `after`: ignore months before the title existed (e.g. searches for a homonym).
    """
    a = alerts[alerts["alert"]]
    if before is not None:
        a = a[a["date"] + pd.offsets.MonthBegin(1) <= before]
    if after is not None:
        a = a[a["date"] >= pd.Timestamp(after).to_period("M").start_time]
    return None if a.empty else a["date"].min()


def known_at(alert_month: pd.Timestamp) -> pd.Timestamp:
    """Date at which a monthly alert is actually available: the end of that month."""
    return alert_month + pd.offsets.MonthBegin(1)


def emergence_score(niche_momentum: list[float], mainstream_momentum: float | None,
                    accelerating_sources: int, total_sources: int) -> float:
    """0-100 score for the live radar.

    - 50 pts: strength of niche acceleration (log2 of momentum, capped at x8)
    - 30 pts: breadth (share of sources accelerating)
    - 20 pts: awareness gap (niche accelerates faster than the mainstream)
    """
    finite = [m for m in niche_momentum if m is not None and np.isfinite(m)]
    strength = np.clip(np.log2(max(finite)) / 3, 0, 1) if finite else 0.0
    breadth = accelerating_sources / total_sources if total_sources else 0.0
    gap = 0.0
    if finite and mainstream_momentum and np.isfinite(mainstream_momentum):
        gap = np.clip((max(finite) - mainstream_momentum) / max(finite), 0, 1)
    return round(50 * strength + 30 * breadth + 20 * gap, 1)


def status(score: float) -> str:
    if score >= 70:
        return "Act now"
    if score >= 40:
        return "Prepare"
    return "Watch"
