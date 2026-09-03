"""Smart Crop Advisory Page.

Rule-engine + LLM advisory pipeline, in two modes:
  - Live API: POSTs to the FastAPI backend (needs API server + internet)
  - Demo snapshot (offline): computes locally from the bundled snapshot —
    crop engine, risk assessor and template advisory all run in-process.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import httpx
import plotly.graph_objects as go

st.set_page_config(page_title="Advisory", page_icon="🌾", layout="wide")

st.title("🌾 Smart Crop Advisory")

API_BASE = "http://localhost:8000"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "data"

mode = st.radio(
    "Data source",
    ["🔴 Live API", "📦 Demo snapshot (offline)"],
    horizontal=True,
)
use_demo = mode.startswith("📦")

crop = st.session_state.get("crop", "Wheat")
sowing_date_str = st.session_state.get("sowing_date", "2026-06-01")
language = st.session_state.get("language", "en")

SEV_COLOR = {"Critical": "red", "High": "orange", "Moderate": "yellow", "Low": "green"}


def _sev_label(s: int) -> str:
    if s >= 80:
        return "Critical"
    if s >= 60:
        return "High"
    if s >= 30:
        return "Moderate"
    return "Low"


def _advisory_live(lat: float, lon: float) -> dict | None:
    try:
        resp = httpx.post(
            f"{API_BASE}/api/advisory",
            json={"lat": lat, "lon": lon, "crop": crop,
                  "sowing_date": sowing_date_str, "language": language},
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()
        st.error(f"API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        st.warning(f"Could not connect to advisory API: {e}")
    return None


def _advisory_demo(snap: dict, village_id: str) -> dict | None:
    """Fully local advisory from the snapshot — zero network calls."""
    project_root = str(Path(__file__).resolve().parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from src.advisory.crop_rules import CropAdvisoryEngine
    from src.advisory.risk_assessment import WeatherRiskAssessor
    from src.advisory.llm_advisory import LLMAdvisoryGenerator

    v = next((x for x in snap["villages"] if x["id"] == village_id), None)
    if v is None:
        return None

    try:
        sowing = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        sowing = (datetime.now() - timedelta(days=30)).date()

    engine = CropAdvisoryEngine()
    stage = engine.determine_growth_stage(crop, sowing)
    if stage is None:
        info = engine.get_crop_info(crop)
        if info and info.growth_stages:
            stage = info.growth_stages[0]
        else:
            st.error(f"Crop '{crop}' not found. Pick another crop in the sidebar.")
            return None

    daily = [{
        "date": d["date"], "temperature": d["temp_max"],
        "rainfall": d["rainfall_mm"], "humidity": d["humidity"],
        "wind_speed": d["wind_kmh"],
    } for d in v["daily"]]

    crop_adv = engine.generate_advisory(crop, stage, daily[0])
    assessor = WeatherRiskAssessor()
    risks = assessor.assess_risks(daily)
    llm = LLMAdvisoryGenerator(api_key=None)  # template mode, offline
    loc_str = f"{v['name']}, {snap['block']}, {snap['district']}"
    gen = llm.generate_advisory(crop_adv, risks, loc_str, language)

    weekly = []
    for d in daily[:7]:
        da = engine.generate_advisory(crop, stage, d)
        prio = ("High" if da.risk_level in ("HIGH", "CRITICAL")
                else "Medium" if da.risk_level == "MODERATE" else "Low")
        summary = "; ".join(a.advice[:60] for a in da.action_items[:2])
        weekly.append({"date": d["date"],
                       "action": summary or "Continue routine practices",
                       "priority": prio})

    return {
        "location": {"lat": v["lat"], "lon": v["lon"],
                     "elevation": v["elevation_m"], "state": snap["state"],
                     "district": snap["district"], "block": snap["block"],
                     "panchayat": v["name"]},
        "crop": crop, "growth_stage": stage.name,
        "risks": [{"type": r.risk_type, "severity": _sev_label(r.severity),
                   "color": SEV_COLOR[_sev_label(r.severity)],
                   "description": r.description,
                   "actions": r.recommended_actions} for r in risks],
        "advisory": gen.advisory_text,
        "weekly_plan": weekly,
        "sms_advisory": gen.sms_version,
    }


advisory_data = None
if use_demo:
    BLOCKS = {"Phanda": "phanda", "Berasia": "berasia"}
    block_label = st.radio("Block", list(BLOCKS.keys()), horizontal=True, key="adv_block")
    snap = json.loads((DATA_DIR / f"demo_{BLOCKS[block_label]}.json").read_text(encoding="utf-8"))
    names = {x["name"]: x["id"] for x in snap["villages"]}
    st.info("📦 Offline demo mode — advisory computed locally, no internet needed.")
    pick = st.selectbox("Select panchayat", list(names.keys()))
    advisory_data = _advisory_demo(snap, names[pick])
else:
    lat = st.session_state.get("lat", 23.275)
    lon = st.session_state.get("lon", 77.335)
    advisory_data = _advisory_live(lat, lon)

if advisory_data is None:
    st.error("Unable to generate advisory. Start the API server, or switch to 📦 Demo snapshot.")
    st.stop()

# --- Header with Location and Crop Info ---
loc = advisory_data.get("location", {})
location_parts = [x for x in [loc.get("panchayat"), loc.get("block"),
                              loc.get("district"), loc.get("state")] if x]
location_str = ", ".join(location_parts) if location_parts else "Unknown"

col_header1, col_header2, col_header3 = st.columns(3)
with col_header1:
    st.metric("📍 Location", location_str)
with col_header2:
    st.metric("🌾 Crop", advisory_data.get("crop", crop))
with col_header3:
    st.metric("🌱 Growth Stage", advisory_data.get("growth_stage", "Unknown"))

st.divider()

# --- Main Advisory Content ---
col_main, col_risk = st.columns([3, 1])

with col_main:
    st.subheader(f"📝 {advisory_data.get('crop', crop)} Advisory")
    st.markdown(advisory_data.get("advisory", "No advisory available."))

    st.subheader("📅 Weekly Action Plan")
    for day in advisory_data.get("weekly_plan", []):
        date_str = day.get("date", "")
        try:
            day_label = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a %d %b")
        except (ValueError, TypeError):
            day_label = date_str
        priority = day.get("priority", "Low")
        icon = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
        with st.expander(f"{icon} {day_label} — {priority} Priority",
                         expanded=(priority == "High")):
            st.write(day.get("action", "Continue routine practices"))

with col_risk:
    st.subheader("⚠️ Risk Assessment")
    risks = advisory_data.get("risks", [])
    if risks:
        for risk in risks:
            severity = risk.get("severity", "Low")
            color = risk.get("color", "gray")
            icon = ("🔴" if color == "red" else "🟠" if color == "orange"
                    else "🟡" if color == "yellow" else "🟢")
            st.markdown(f"**{icon} {risk.get('type', 'Unknown')}** — {severity}")
            st.caption(risk.get("description", ""))
            for action in (risk.get("actions") or [])[:2]:
                st.caption(f"→ {action}")
            st.divider()
    else:
        st.success("🟢 No significant risks detected.")

# --- SMS Preview ---
st.divider()
st.subheader("📱 SMS Advisory Preview")
sms_text = advisory_data.get("sms_advisory", "No SMS advisory available.")
col_sms1, col_sms2 = st.columns(2)
with col_sms1:
    st.markdown("**SMS (160 chars, farmer-ready):**")
    st.info(sms_text)
with col_sms2:
    st.markdown("**How it's sent:**")
    st.caption("Via SMS gateway / WhatsApp API to registered farmers in the panchayat, in their language.")
