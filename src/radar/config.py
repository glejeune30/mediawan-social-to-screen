"""Paths and shared settings."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SEEDS = DATA / "seeds"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
MANUAL = DATA / "manual"          # manual CSV exports (e.g. Google Trends) when an API refuses
CHARTS = ROOT / "presentation" / "assets"

for p in (RAW, PROCESSED, MANUAL, CHARTS):
    p.mkdir(parents=True, exist_ok=True)

# Generic client name, as asked by the Wikimedia API (no personal data in it).
USER_AGENT = "MediawanRadarStudentProject/0.1 (academic case study)"

try:  # optional: read API keys from a local .env file (never committed)
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "mediawan-radar/0.1")
NYT_API_KEY = os.getenv("NYT_API_KEY")
