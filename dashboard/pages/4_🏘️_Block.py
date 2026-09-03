"""Block-level Panchayat View."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from components.gmaps import gmaps_block_html, get_maps_key

import streamlit as st
import httpx
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Block Panchayats", page_icon="🏘️", layout="wide", initial_sidebar_state="collapsed")
from dashboard.components.theme import inject_weather_theme, navigate_if_needed
inject_weather_theme(hide_sidebar=True)
navigate_if_needed("Block Map")

BLOCKS = {"Phanda": "phanda", "Berasia": "berasia"}
block_label = st.radio("Block (Bhopal district, MP)", list(BLOCKS.keys()), horizontal=True)
bid = BLOCKS[block_label]
st.title(f"🏘️ {block_label} Block, Bhopal (MP)")
st.caption("Block-level forecast downscaled to panchayat villages (~1 km resolution)")

API_BASE = "http://localhost:8000"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "data"

mode = st.radio("Data source", ["🔴 Live API", "📦 Demo snapshot (offline)"], horizontal=True)
use_demo = mode.startswith("📦")


def _load_snapshot(snap_path: Path) -> dict | None:
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception as e:
        st.error(f"Demo snapshot missing: {e}")
        return None
    villages = []
    for v in snap["villages"]:
        t = v["daily"][0]
        villages.append({
            "id": v["id"], "name": v["name"], "hindi_name": v["hindi_name"],
            "lat": v["lat"], "lon": v["lon"], "elevation_m": v["elevation_m"],
            "population": v.get("population"), "main_crops": v.get("main_crops", []),
            "today": {"temp_max": t["temp_max"], "temp_min": t["temp_min"],
                      "rainfall_mm": t["rainfall_mm"], "humidity": t["humidity"],
                      "wind_kmh": t["wind_kmh"], "weather_desc": t["weather_desc"]},
            "risk": {"level": v["risk_level"], "color": v["risk_color"],
                     "top_risk": v["top_risk"], "severity": 0},
        })
    return {
        "block": snap["block"], "district": snap["district"], "state": snap["state"],
        "center_lat": snap["center_lat"], "center_lon": snap["center_lon"],
        "total_panchayats": len(villages),
        "date": snap["coarse"][0]["date"] if snap.get("coarse") else "",
        "generated_on": snap.get("generated_on", ""), "villages": villages,
    }


def _fetch_live() -> dict | None:
    try:
        resp = httpx.get(f"{API_BASE}/api/panchayats", params={"block_id": bid}, timeout=60)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Could not connect to API: {e}")
    return None


if use_demo:
    data = _load_snapshot(DATA_DIR / f"demo_{bid}.json")
    if data:
        st.info(f"📦 Offline snapshot ({data.get('generated_on', 'N/A')})")
else:
    data = _fetch_live()
    if data:
        st.success("🔴 Live data from API.")
    else:
        st.error("API server not running. Switch to 📦 Demo snapshot.")

if data is None:
    st.stop()

villages = data.get("villages", [])

temps = [v["today"]["temp_max"] for v in villages]
rains = [v["today"]["rainfall_mm"] for v in villages]
high_risk = [v for v in villages if v["risk"]["level"] in ("High", "Critical")]

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Panchayats", len(villages))
with m2:
    st.metric("Avg Max Temp", f"{sum(temps)/len(temps):.1f}°C" if temps else "N/A")
with m3:
    st.metric("Max Rainfall", f"{max(rains):.1f} mm" if rains else "N/A")
with m4:
    st.metric("High/Critical Risk", len(high_risk))

st.subheader("🗺️ Panchayat Map")
_maps_key = get_maps_key()
_map_opts = ["Google Maps", "OpenStreetMap"] if _maps_key else ["OpenStreetMap"]
_map_style = st.radio("Map style", _map_opts, horizontal=True)
if _map_style == "Google Maps":
    st.components.v1.html(gmaps_block_html(villages, data["center_lat"], data["center_lon"], _maps_key), height=440)
else:
    m = folium.Map(location=[data["center_lat"], data["center_lon"]], zoom_start=12, tiles="OpenStreetMap")
    folium.Circle([data["center_lat"], data["center_lon"]], radius=9000, color="blue", weight=2,
                  dash_array="6 6", fill=True, fill_opacity=0.04, tooltip=f"{data['block']} Block").add_to(m)
    risk_icon = {"green": "green", "yellow": "orange", "orange": "orange", "red": "red"}
    for v in villages:
        t, r = v["today"], v["risk"]
        popup = (f"<b>{v['name']} ({v['hindi_name']})</b><br>Elev: {v['elevation_m']}m<br>"
                 f"Temp: {t['temp_max']}°/{t['temp_min']}°C<br>Rain: {t['rainfall_mm']}mm<br>Risk: {r['level']}")
        folium.CircleMarker([v["lat"], v["lon"]], radius=9, color=risk_icon.get(r["color"], "gray"),
                            fill=True, fill_opacity=0.75, popup=folium.Popup(popup, max_width=220),
                            tooltip=f"{v['name']} — {r['level']}").add_to(m)
    st_folium(m, width=None, height=420)

st.subheader("📋 All Panchayats")
rows = [{"Village": v["name"], "Elev (m)": v["elevation_m"],
         "Max °C": v["today"]["temp_max"], "Min °C": v["today"]["temp_min"],
         "Rain (mm)": v["today"]["rainfall_mm"], "Humidity %": v["today"]["humidity"],
         "Wind (km/h)": v["today"]["wind_kmh"], "Risk": v["risk"]["level"],
         "Top Risk": v["risk"]["top_risk"]} for v in villages]
st.dataframe(pd.DataFrame(rows).sort_values("Village").reset_index(drop=True), use_container_width=True, hide_index=True)

st.divider()
st.subheader("🔍 Panchayat Detail — 7-Day Forecast")
names = {v["name"]: v["id"] for v in villages}
choice = st.selectbox("Select panchayat", list(names.keys()))

detail = None
if use_demo:
    snap = json.loads((DATA_DIR / f"demo_{bid}.json").read_text(encoding="utf-8"))
    v = next(x for x in snap["villages"] if x["id"] == names[choice])
    detail = {
        "name": v["name"], "hindi_name": v["hindi_name"], "elevation_m": v["elevation_m"],
        "main_crops": v.get("main_crops", []),
        "forecast": [{"date": d["date"], "temp_max": d["temp_max"], "temp_min": d["temp_min"],
                       "rainfall_mm": d["rainfall_mm"], "humidity": d["humidity"],
                       "wind_kmh": d["wind_kmh"], "weather_desc": d["weather_desc"]} for d in v["daily"]],
        "risks": v.get("risks", []),
    }
else:
    try:
        resp = httpx.get(f"{API_BASE}/api/panchayats/{names[choice]}", params={"block_id": bid}, timeout=60)
        if resp.status_code == 200:
            detail = resp.json()
    except Exception as e:
        st.warning(f"Detail fetch failed: {e}")

if detail:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Village", f"{detail['name']} ({detail['hindi_name']})")
    with c2:
        st.metric("Elevation", f"{detail['elevation_m']} m")
    with c3:
        st.metric("Main Crops", ", ".join(detail.get("main_crops", [])) or "—")

    drows = [{"Date": d["date"], "Max °C": d["temp_max"], "Min °C": d["temp_min"],
              "Rain (mm)": d["rainfall_mm"], "Humidity %": d["humidity"],
              "Wind (km/h)": d["wind_kmh"], "Condition": d["weather_desc"]} for d in detail["forecast"]]
    st.dataframe(pd.DataFrame(drows), use_container_width=True, hide_index=True)

    if detail["risks"]:
        for r in detail["risks"]:
            st.warning(f"⚠️ **{r['type']}** (severity {r['severity']}): {r['description']}")
    else:
        st.success("🟢 No significant risks this week.")
