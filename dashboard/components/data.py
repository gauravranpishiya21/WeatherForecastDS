"""Shared data helpers: load villages + fast API checks with caching.

Reduces lag on localhost by caching API availability and connection failures
in st.session_state so every page render doesn't re-try a dead connection.
"""

from pathlib import Path

import httpx
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "data"
API_BASE = "http://localhost:8000"


@st.cache_data(ttl=300, show_spinner=False)
def load_all_villages() -> list[dict]:
    """Load all villages from both demo blocks, tagged with block name."""
    out = []
    for bid in ("phanda", "berasia"):
        fpath = DATA_DIR / f"demo_{bid}.json"
        if fpath.exists():
            import json
            snap = json.loads(fpath.read_text(encoding="utf-8"))
            block = snap.get("block", bid.title())
            for v in snap["villages"]:
                v["_block"] = block
                v["_demo"] = snap
            out.extend(snap["villages"])
    return out


def filter_villages(query: str) -> list[dict]:
    """Filter loaded villages by name / hindi name / block."""
    villages = load_all_villages()
    if not query:
        return villages
    q = query.strip().lower()
    return [v for v in villages
            if q in v["name"].lower()
            or q in v.get("hindi_name", "").lower()
            or q in v.get("_block", "").lower()]


def api_is_available() -> bool:
    """Return True if the local API responds fast. Caches result so we
    don't wait on a dead connection on every rerun."""
    if "api_available" in st.session_state:
        return st.session_state["api_available"]
    available = False
    try:
        resp = httpx.get(f"{API_BASE}/api/health" if True else API_BASE, timeout=0.7)
        available = resp.status_code == 200
    except Exception:
        available = False
    st.session_state["api_available"] = available
    return available


def fetch_forecast(lat: float, lon: float, days: int = 7) -> dict | None:
    """Fetch forecast, returns None fast if API unavailable."""
    if not api_is_available():
        return None
    try:
        resp = httpx.get(f"{API_BASE}/api/forecast",
                         params={"lat": lat, "lon": lon, "days": days}, timeout=2.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        st.session_state["api_available"] = False
    return None
