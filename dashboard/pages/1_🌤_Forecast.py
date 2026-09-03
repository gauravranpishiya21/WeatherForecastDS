"""7-Day Hyperlocal Forecast Page."""

import json
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.components.theme import inject_weather_theme, navigate_if_needed
from dashboard.components.data import load_all_villages, filter_villages, fetch_forecast

st.set_page_config(page_title="Hyperlocal Forecast", page_icon="🌤️", layout="wide", initial_sidebar_state="collapsed")
inject_weather_theme(hide_sidebar=True)
navigate_if_needed("7-Day Forecast")

st.title("🌤️ Hyperlocal 7-Day Downscaled Forecast")
st.caption("Panchayat-level ~1 km resolution forecast powered by terrain-aware downscaling")

lat = st.session_state.get("lat", 23.275)
lon = st.session_state.get("lon", 77.335)
API_BASE = "http://localhost:8000"
DATA_DIR = ROOT / "src" / "data"

# Load ALL villages from both blocks (cached)
all_villages = load_all_villages()
village_map = {v["name"]: v for v in all_villages}

st.subheader("🔍 Select Gram Panchayat Village")
search_query = st.text_input(
    "🔍 Search village",
    placeholder="Type village name in English or Hindi (e.g., Phanda, फांदा, Berasia, Samasgarh...)",
    key="forecast_search",
    label_visibility="collapsed",
)

if search_query:
    filtered = filter_villages(search_query)
else:
    filtered = all_villages

if filtered:
    vlabels = [f"[{v['_block']}] {v['name']} ({v['hindi_name']}) — {v['elevation_m']}m" for v in filtered]
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        selected_label = st.selectbox("📍 Matching villages", vlabels, key="village_search")
    with col_btn:
        st.write("")
        st.write("")
        load_clicked = st.button("📍 Load Forecast", key="btn_load_v")

    if load_clicked or st.session_state.get("village_name"):
        if load_clicked:
            v = filtered[vlabels.index(selected_label)]
            st.session_state["lat"] = v["lat"]
            st.session_state["lon"] = v["lon"]
            st.session_state["village_name"] = v["name"]
            st.session_state["selected_v"] = v
            st.rerun()
else:
    st.info("No villages match your search. Try a different name.")

lat = st.session_state.get("lat", lat)
lon = st.session_state.get("lon", lon)

# Fetch forecast data (fast — cached API availability)
data = fetch_forecast(lat, lon, 7)
is_live = data is not None

# Fallback to snapshot
if data is None:
    sel = st.session_state.get("selected_v") or (all_villages[0] if all_villages else None)
    if sel:
        demo = sel["_demo"]
        data = {
            "location": {
                "panchayat": sel["name"], "block": sel["_block"],
                "district": demo.get("district", "Bhopal"), "state": demo.get("state", "MP"),
                "lat": sel["lat"], "lon": sel["lon"],
            },
            "improvement_metrics": {"elevation_m": sel["elevation_m"], "model_type": "lapse_rate_ml_ensemble", "resolution": "1 km downscaled"},
            "downscaled_forecast": [
                {"date": d["date"], "temp_max": d["temp_max"], "temp_min": d["temp_min"],
                 "rainfall_mm": d["rainfall_mm"], "humidity": d["humidity"],
                 "wind_kmh": d["wind_kmh"], "weather_desc": d["weather_desc"]}
                for d in sel["daily"]
            ],
            "coarse_forecast": demo.get("coarse", []),
        }

if data is None:
    st.error("No forecast data available.")
    st.stop()

loc = data.get("location", {})
metrics = data.get("improvement_metrics", {})
location_name = st.session_state.get("village_name") or loc.get("panchayat") or f"{lat:.4f}, {lon:.4f}"

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"""
    <div style="margin-top: 10px;">
        <h2 style="margin: 0; color: #38bdf8;">📍 {location_name}</h2>
        <p style="color: #94a3b8; margin: 4px 0 0 0;">
            Block: <b>{loc.get('block', 'N/A')}</b>, District: <b>{loc.get('district', 'Bhopal')}</b> |
            Lat: {lat:.4f}°, Lon: {lon:.4f}° | Elevation: <b>{metrics.get('elevation_m', 'N/A')} m</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    badge = "🟢 LIVE API DATA" if is_live else "📦 OFFLINE SNAPSHOT"
    cls = "badge-green" if is_live else "badge-blue"
    st.markdown(f"<span class='weather-badge {cls}'>{badge}</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 7-Day Weather Cards
downscaled = data.get("downscaled_forecast", [])
if downscaled:
    st.subheader("📅 7-Day Hyperlocal Outlook")
    cols = st.columns(min(len(downscaled), 7))
    for i, d in enumerate(downscaled[:7]):
        dt = datetime.strptime(d["date"], "%Y-%m-%d") if "-" in d["date"] else datetime.now()
        day_str = dt.strftime("%a, %d %b") if i > 0 else "Today"
        rain = d.get("rainfall_mm", 0.0)
        desc = d.get("weather_desc", "").lower()
        if "rain" in desc or rain > 2.0:
            icon = "🌧️"
        elif "cloud" in desc or "overcast" in desc:
            icon = "⛅"
        elif "thunder" in desc:
            icon = "⛈️"
        else:
            icon = "☀️"
        with cols[i]:
            st.markdown(f"""
            <div class="glass-card" style="padding: 14px 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 13px; font-weight: 700; color: #94a3b8;">{day_str}</div>
                <div style="font-size: 32px; margin: 8px 0;">{icon}</div>
                <div style="font-size: 18px; font-weight: 800; color: #f8fafc;">
                    {d.get('temp_max', 0):.0f}° <span style="font-size: 13px; color: #64748b; font-weight: 500;">{d.get('temp_min', 0):.0f}°</span>
                </div>
                <div style="font-size: 12px; color: #38bdf8; margin-top: 6px; font-weight: 600;">💧 {rain:.1f} mm</div>
                <div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">💨 {d.get('wind_kmh', 10):.0f} km/h</div>
            </div>
            """, unsafe_allow_html=True)

# Charts & Map
st.markdown("<br>", unsafe_allow_html=True)
col_c1, col_c2 = st.columns([3, 2])

with col_c1:
    st.subheader("📈 Temperature & Precipitation")
    dates = [d["date"] for d in downscaled]
    t_max = [d.get("temp_max", 0) for d in downscaled]
    t_min = [d.get("temp_min", 0) for d in downscaled]
    rain_data = [d.get("rainfall_mm", 0) for d in downscaled]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=t_max, name="Max Temp (°C)", mode="lines+markers", line=dict(color="#f87171", width=3)))
    fig.add_trace(go.Scatter(x=dates, y=t_min, name="Min Temp (°C)", mode="lines+markers", line=dict(color="#38bdf8", width=3)))
    fig.add_trace(go.Bar(x=dates, y=rain_data, name="Rainfall (mm)", yaxis="y2", marker_color="rgba(56, 189, 248, 0.4)"))
    fig.update_layout(
        paper_bgcolor="rgba(15, 23, 42, 0.0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8"),
        yaxis=dict(title="Temperature (°C)", gridcolor="rgba(255,255,255,0.06)"),
        yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=20, b=10), height=340,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_c2:
    st.subheader("🗺️ Panchayat Map")
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup=f"<b>{location_name}</b><br>Elev: {metrics.get('elevation_m', 'N/A')}m",
                  icon=folium.Icon(color="blue", icon="cloud", prefix="fa")).add_to(m)
    folium.Circle([lat, lon], radius=1200, color="#38bdf8", fill=True, fill_opacity=0.18,
                  tooltip="Panchayat 1km Radius").add_to(m)
    st_folium(m, height=340, use_container_width=True)
