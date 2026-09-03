"""Kisan View — farmer-facing page. Hindi-first, big text, zero jargon.

Pick village + crop -> today's weather, traffic-light risk,
max 3 simple actions, 3-day outlook, SMS box.
Fully offline (bundled snapshot + local rules).
"""

import json
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Kisan", page_icon="🧑‍🌾", layout="centered")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "src" / "data"
BLOCKS = {"Phanda": "phanda", "Berasia": "berasia"}

T = {
    "hi": {
        "title": "🧑‍🌾 किसान सलाह",
        "village": "गांव चुनें", "crop": "फसल चुनें", "stage": "फसल की अवस्था",
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
        "village": "Select village", "crop": "Select crop", "stage": "Crop stage",
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

block_label = st.radio("Block / ब्लॉक", list(BLOCKS.keys()), horizontal=True)
snap = json.loads((DATA_DIR / f"demo_{BLOCKS[block_label]}.json").read_text(encoding="utf-8"))
villages = snap["villages"]

c1, c2 = st.columns(2)
with c1:
    vlabels = [f"{v['name']} ({v['hindi_name']})" for v in villages]
    vpick = st.selectbox(L["village"], vlabels)
with c2:
    cpick = st.selectbox(L["crop"], [f"{k} ({v})" for k, v in CROPS.items()])
v = villages[vlabels.index(vpick)]
crop = cpick.split(" (")[0]

from src.advisory.crop_rules import CropAdvisoryEngine
from src.advisory.risk_assessment import WeatherRiskAssessor

engine = CropAdvisoryEngine()
info = engine.get_crop_info(crop)
stages = [s.name for s in info.growth_stages] if info else []
stage_name = st.selectbox(L["stage"], stages) if stages else ""
stage = next((s for s in (info.growth_stages if info else []) if s.name == stage_name), None)

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

# --- Simple action lines (priority order, max 3) ---
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

# --- Render: big + simple ---
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
    st.success(a) if a.startswith("✅") else st.warning(a)

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
