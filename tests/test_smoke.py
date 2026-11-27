"""Smoke tests. Run:  python -m pytest tests  (or: python tests/test_smoke.py)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radar.indicators import momentum, source_alerts, first_alert, emergence_score, status  # noqa: E402


def test_momentum_no_lookahead_and_missing_history():
    s = pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 10, 10], dtype=float)
    m = momentum(s)
    assert m.iloc[:8].isna().all()          # not enough history -> NaN, never inf
    assert np.isinf(m.iloc[11])             # from zero to a real level -> new entrant


def test_alert_needs_two_hot_months_and_floor():
    dates = pd.date_range("2020-01-01", periods=14, freq="MS")
    values = [1] * 9 + [5, 6, 8, 9, 10]
    a = source_alerts(pd.DataFrame({"date": dates, "value": values}), "google_trends")
    fa = first_alert(a)
    assert fa is not None and fa >= dates[10]


def test_first_alert_respects_announcement_and_publication():
    dates = pd.date_range("2020-01-01", periods=6, freq="MS")
    a = pd.DataFrame({"date": dates, "alert": [True] * 6})
    # a month only counts once it is over
    assert first_alert(a, before=pd.Timestamp("2020-01-15")) is None
    assert first_alert(a, after="2020-03-10") == pd.Timestamp("2020-03-01")


def test_score_and_status():
    assert status(emergence_score([8.0, 3.0], 1.0, 2, 2)) == "Act now"
    assert status(emergence_score([1.1], None, 0, 3)) == "Watch"


def test_watchlist_status_rules():
    from radar.watchlist import score
    n = 10
    df = pd.DataFrame({
        "story_id": [f"s{i}" for i in range(n)],
        "format": ["Webtoon"] * n,
        "accel_signal": np.linspace(0.0, 0.2, n),          # s9 accelerates most
        "activity_now": np.linspace(1, 10, n),
        "wiki_views_month": [np.nan] * (n - 2) + [500_000, 1_000],
        "wiki_momentum": [np.nan] * (n - 2) + [1.0, 2.0],
        "wiki_page_age_months": [np.nan] * (n - 2) + [40, 5],
        "wiki_adapted": [False] * n,
        "adaptation": [None] * (n - 3) + ["Anime (2026)", None, None],
        "fans_now": [1000] * n, "growth_90d": np.linspace(0.0, 0.2, n),
        "last_24h": [0] * n, "previous_days_avg": [0] * n,
    })
    out = score(df).set_index("story_id")
    assert out.loc["s7", "status"] == "Already adapted"
    assert out.loc["s9", "status"] == "Act now"        # top acceleration, small page (1k views)
    assert out.loc["s8", "status"] == "Prepare"        # accelerating but already well known
    assert out.loc["s0", "status"] == "Watch"
    assert out["score"].between(0, 100).all()


def test_web_server_serves_interface():
    """server.py serves the interface (JS as JavaScript, or browsers refuse the modules) and its data."""
    import json
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer

    sys.path.insert(0, str(ROOT))
    import server

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        def get(path):
            with urllib.request.urlopen(base + path, timeout=10) as r:
                return r.headers.get("Content-Type", ""), r.read()
        assert get("/")[0].startswith("text/html")
        for js in ["/js/main.js", "/js/scoring.js", "/js/extensions/index.js"]:
            assert get(js)[0].startswith("text/javascript"), js
        assert json.loads(get("/api/status")[1])["running"] is False
        if (ROOT / "web" / "data" / "radar.json").exists():
            data = json.loads(get("/data/radar.json")[1])
            assert data["stories"] and all("py" in s and "s" in s for s in data["stories"])
    finally:
        httpd.shutdown()


def test_streamlit_app_runs():
    if not (ROOT / "data" / "processed" / "backtest_results.csv").exists():
        return
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=60).run()
    assert not at.exception


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
