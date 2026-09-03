"""Kisan View — farmer-facing page. Hindi-first, big text, zero jargon."""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "src" / "data"

from dashboard.components.theme import inject_weather_theme, render_voice_button, navigate_if_needed
from src.advisory.crop_rules import CropAdvisoryEngine
from src.advisory.risk_assessment import WeatherRiskAssessor

st.set_page_config(page_title="Kisan", page_icon="🧑‍🌾", layout="centered", initial_sidebar_state="collapsed")
inject_weather_theme(hide_sidebar=True)
navigate_if_needed("Kisan View")

BLOCKS = {"Phanda": "phanda", "Berasia": "berasia"}

T = {
    "hi": {
        "title": "🧑‍🌾 किसान सलाह",
        "village": "गांव खोजें", "crop": "फसल चुनें", "stage": "फसल की अवस्था",
        "today": "आज का मौसम", "risk": "खतरा", "do": "आज क्या करें",
        "next3": "अगले 3 दिन", "sms": "मोबाइल SMS",
        "ok": "सब ठीक है", "no_rain_irr": "बारिश नहीं है — फसल में पानी दें",
        "rain_skip": "आज बारिश है — सिंचाई न करें",
        "heat": "बहुत गर्मी है — शाम को हल्की सिंचाई करें",
        "frost": "पाला पड़ सकता है — शाम को हल्की सिंचाई करें",
        "wind": "तेज हवा है — छिड़काव न करें",
        "fungus": "फफूंद का खतरा — खेत देख लें",
        "pest": "कीट लग सकता है — नीम तेल छिड़कें",
        "hot_crop": "गर्मी फसल के लिए ज्यादा है — पानी का ध्यान रखें",
        "cold_crop": "ठंड फसल के लिए ज्यादा है — निगरानी रखें",
        "fine": "मौसम ठीक है — रोज जैसे काम करें",
        "d0": "आज", "d1": "कल", "d2": "परसों",
    },
    "en": {
        "title": "🧑‍🌾 Farmer Advisory",
        "village": "Search village", "crop": "Select crop", "stage": "Crop stage",
        "today": "Today's weather", "risk": "Risk", "do": "What to do today",
        "next3": "Next 3 days", "sms": "Mobile SMS",
        "ok": "All OK", "no_rain_irr": "No rain — irrigate your field",
        "rain_skip": "Rain today — skip irrigation",
        "heat": "Extreme heat — light evening irrigation",
        "frost": "Frost possible — light evening irrigation",
        "wind": "Strong wind — do not spray",
        "fungus": "Fungus risk — inspect your field",
        "pest": "Pest risk — spray neem oil",
        "hot_crop": "Too hot for this stage — ensure water",
        "cold_crop": "Too cold for this stage — monitor crop",
        "fine": "Weather is fine — routine work",
        "d0": "Today", "d1": "Tomorrow", "d2": "Day after",
    },
}

CROPS = {"Soybean": "सोयाबीन", "Wheat": "गेहूं", "Chickpea": "चना",
         "Mustard": "सरसों", "Maize": "मक्का"}

lang = st.radio("भाषा / Language", ["हिन्दी", "English"], horizontal=True)
L = T["hi"] if lang == "हिन्दी" else T["en"]
st.title(L["title"])

# Load ALL villages from both blocks
all_villages = []
for bid in ("phanda", "berasia"):
    fpath = DATA_DIR / f"demo_{bid}.json"
    if fpath.exists():
        snap = json.loads(fpath.read_text(encoding="utf-8"))
        for v in snap["villages"]:
            v["_block"] = snap.get("block", bid.title())
            v["_demo"] = snap
        all_villages.extend(snap["villages"])

village_map = {v["name"]: v for v in all_villages}

# --- Village Search Bar ---
st.markdown(f"**{L['village']}**")
search_query = st.text_input(
    "🔍 " + L["village"],
    placeholder="Type village name in English or Hindi (e.g., Phanda, फांदा, Berasia, Samasgarh...)",
    key="kisan_search",
    label_visibility="collapsed",
)

# Filter villages based on search
if search_query:
    search_lower = search_query.lower()
    filtered = [v for v in all_villages
                if search_lower in v["name"].lower()
                or search_lower in v.get("hindi_name", "").lower()
                or search_lower in v.get("_block", "").lower()]
else:
    filtered = all_villages

if filtered:
    vlabels = [f"[{v['_block']}] {v['name']} ({v.get('hindi_name', '')})" for v in filtered]
    selected_label = st.selectbox(
        "📍 " + ("मिले गांव" if lang == "हिन्दी" else "Matching Villages"),
        vlabels, key="kisan_village_select"
    )
    sel_idx = vlabels.index(selected_label)
    v = filtered[sel_idx]
else:
    # No demo data — let user enter coordinates manually
    st.warning("⚠️ " + ("गांव डेटा नहीं मिला — कृपया coordinates दर्ज करें" if lang == "हिन्दी" else "Village not in demo data — enter coordinates below"))
    manual_col1, manual_col2 = st.columns(2)
    with manual_col1:
        manual_lat = st.number_input("Latitude", value=23.275, format="%.4f", key="kisan_lat")
    with manual_col2:
        manual_lon = st.number_input("Longitude", value=77.335, format="%.4f", key="kisan_lon")
    manual_name = st.text_input("Village Name", value="Unknown Village", key="kisan_vname")

    # Create a synthetic village entry with 7 days of placeholder data
    from datetime import datetime, timedelta
    today = datetime.now()
    placeholder_daily = []
    for di in range(7):
        d = today + timedelta(days=di)
        placeholder_daily.append({
            "date": d.strftime("%Y-%m-%d"),
            "temp_max": 35.0, "temp_min": 24.0,
            "rainfall_mm": 2.0, "humidity": 65.0,
            "wind_kmh": 12.0, "weather_desc": "Partly Cloudy",
        })
    v = {
        "name": manual_name, "hindi_name": manual_name,
        "lat": manual_lat, "lon": manual_lon,
        "elevation_m": 500,
        "_block": "Manual",
        "_demo": {"block": "Manual", "district": "—", "state": "—", "coarse": []},
        "daily": placeholder_daily,
    }
    # Store for other pages
    st.session_state["lat"] = manual_lat
    st.session_state["lon"] = manual_lon
    st.session_state["village_name"] = manual_name

# Store selected village in session state
st.session_state["lat"] = v["lat"]
st.session_state["lon"] = v["lon"]
st.session_state["village_name"] = v["name"]
st.session_state["selected_v"] = v

# Crop & Stage
c1, c2 = st.columns(2)
with c1:
    cpick = st.selectbox(L["crop"], [f"{k} ({v_hin})" for k, v_hin in CROPS.items()])
with c2:
    crop = cpick.split(" (")[0]
    engine = CropAdvisoryEngine()
    info = engine.get_crop_info(crop)
    stages = [s.name for s in info.growth_stages] if info else []
    stage_name = st.selectbox(L["stage"], stages) if stages else ""
    stage = next((s for s in (info.growth_stages if info else []) if s.name == stage_name), None)

# --- Weather Analysis ---
daily = v["daily"]
t = daily[0]
week_rain = sum(d["rainfall_mm"] for d in daily[:7])
assessor = WeatherRiskAssessor()
risks = assessor.assess_risks([{
    "temperature": d["temp_max"], "rainfall": d["rainfall_mm"],
    "humidity": d["humidity"], "wind_speed": d["wind_kmh"],
} for d in daily[:7]])
score = assessor.aggregate_risk_score(risks)
light = "🟢" if score < 30 else "🟡" if score < 60 else "🔴"

actions = []
if t["temp_max"] > 40:
    actions.append("🔥 " + L["heat"])
elif t["temp_min"] < 5:
    actions.append("🥶 " + L["frost"])
if t["wind_kmh"] > 40:
    actions.append("💨 " + L["wind"])
if t["rainfall_mm"] >= 5:
    actions.append("🌧️ " + L["rain_skip"])
elif week_rain < 10:
    actions.append("💧 " + L["no_rain_irr"])
if any(r.risk_type == "High Humidity Disease" for r in risks):
    actions.append("🦠 " + L["fungus"])
if info:
    for pest in info.pest_conditions:
        if pest.temp_min <= t["temp_max"] <= pest.temp_max and t["humidity"] >= pest.humidity_min:
            actions.append("🐛 " + L["pest"] + f" ({pest.pest_name})")
            break
if stage:
    if t["temp_max"] > stage.optimal_temp_max + 3:
        actions.append("🌡️ " + L["hot_crop"])
    elif t["temp_max"] < stage.optimal_temp_min - 3:
        actions.append("🌡️ " + L["cold_crop"])
if not actions:
    actions.append("✅ " + L["fine"])
actions = actions[:3]

# --- Render ---
st.divider()
st.subheader(L["today"])
icon = "🌧️" if t["rainfall_mm"] >= 5 else "🌦️" if t["rainfall_mm"] > 0 else "🔥" if t["temp_max"] > 38 else "☀️"
st.header(f"{icon} {t['temp_max']:.0f}°C  |  💧 {t['rainfall_mm']:.0f} mm")

st.subheader(f"{L['risk']}: {light}")
if risks:
    top = max(risks, key=lambda r: r.severity)
    st.write(f"{light} {top.risk_type}")
else:
    st.write(f"🟢 {L['ok']}")

st.subheader("👉 " + L["do"])
for a in actions:
    if a.startswith("✅"):
        st.success(a)
    else:
        st.warning(a)

st.subheader("📅 " + L["next3"])
cols = st.columns(3)
for i, col in enumerate(cols):
    d = daily[i]
    di = "🌧️" if d["rainfall_mm"] >= 5 else "🌦️" if d["rainfall_mm"] > 0 else "☀️"
    with col:
        st.write(f"**{[L['d0'], L['d1'], L['d2']][i]}**")
        st.write(di)
        st.write(f"{d['temp_max']:.0f}° / {d['temp_min']:.0f}°")
        st.write(f"💧 {d['rainfall_mm']:.0f} mm")

st.subheader("📱 " + L["sms"])
sms = f"{v['name']}: {actions[0][2:]}"[:160]
st.info(sms)
