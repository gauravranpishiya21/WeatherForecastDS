"""7-Day Hyperlocal Forecast Page.

Displays downscaled weather forecast with interactive maps and charts.
"""

import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Forecast", page_icon="🌤", layout="wide")

st.title("🌤 Hyperlocal 7-Day Forecast")

lat = st.session_state.get("lat", 23.275)
lon = st.session_state.get("lon", 77.335)
API_BASE = "http://localhost:8000"

# --- Village Search: any MP village -> its personal 7-day status ---
st.subheader("🔍 Search MP Village")
with st.form("vsearch_form", clear_on_submit=False):
    sq = st.text_input("Village name", placeholder="e.g., Phanda, Samasgarh, Berasia…")
    submitted = st.form_submit_button("🔍 Search")

if submitted and sq and len(sq.strip()) >= 2:
    try:
        r = httpx.get(f"{API_BASE}/api/search/villages",
                      params={"q": sq.strip()}, timeout=25)
        st.session_state["vcands"] = r.json().get("results", []) if r.status_code == 200 else []
    except Exception as e:
        st.warning(f"Search failed (is the API running?): {e}")
        st.session_state["vcands"] = []

cands = st.session_state.get("vcands", [])
if cands:
    labels = [f"{c['name']} — {c.get('block', '')}, {c.get('district', '')} [{c['source']}]"
              for c in cands]
    pick = st.selectbox("Matching villages", labels, key="vpick")
    if st.button("📍 Load village weather", key="vload"):
        sel = cands[labels.index(pick)]
        st.session_state["lat"] = sel["lat"]
        st.session_state["lon"] = sel["lon"]
        st.session_state["village_name"] = sel["name"]
        st.rerun()
elif submitted:
    st.caption("No matching village found — try another spelling.")

# --- Fetch real forecast data from API ---
data = None
try:
    resp = httpx.get(
        f"{API_BASE}/api/forecast",
        params={"lat": lat, "lon": lon, "days": 7},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
except Exception as e:
    st.warning(f"Could not connect to API: {e}")

if data is None:
    st.error("Unable to fetch forecast data. Please ensure the API server is running on port 8000.")
    st.stop()

# --- Location Info ---
loc = data.get("location", {})
metrics = data.get("improvement_metrics", {})

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    location_parts = [v for v in [loc.get("panchayat"), loc.get("block"), loc.get("district"), loc.get("state")] if v]
    location_str = ", ".join(location_parts) if location_parts else f"{lat:.4f}, {lon:.4f}"
    title_name = st.session_state.get("village_name", "") or location_str
    st.subheader(f"📍 {title_name}")
    st.caption(f"Lat: {lat:.4f} | Lon: {lon:.4f} | Elevation: {metrics.get('elevation_m', 'N/A')}m")

with col_header2:
    model_badge = metrics.get("model_type", "statistical_only")
    if model_badge != "statistical_only":
        st.success(f"🤖 ML Model: {model_badge.upper()}")
    else:
        st.info("📐 Statistical Downscaling")

# --- Interactive Map ---
st.subheader("🗺️ Interactive Map")
m = folium.Map(location=[lat, lon], zoom_start=12, tiles="OpenStreetMap")
folium.Marker(
    [lat, lon],
    popup=f"<b>{location_str}</b><br>Elevation: {metrics.get('elevation_m', 'N/A')}m",
    icon=folium.Icon(color="red", icon="cloud", prefix="fa"),
).add_to(m)

# Add temperature heatmap markers for downscaled data
coarse = data.get("coarse_forecast", [])
downscaled = data.get("downscaled_forecast", [])
if downscaled:
    today = downscaled[0]
    temp = today.get("temp_max", 25)
    color = "red" if temp > 35 else "orange" if temp > 30 else "blue" if temp < 10 else "green"
    folium.CircleMarker(
        [lat, lon],
        radius=20,
        color=color,
        fill=True,
        fill_opacity=0.4,
        popup=f"<b>Today</b><br>Temp: {temp}°C<br>Rain: {today.get('rainfall_mm', 0)}mm",
    ).add_to(m)

st_folium(m, width=None, height=350)

# --- 7-Day Weather Cards ---
st.subheader("📅 7-Day Weather Outlook")

if downscaled:
    cols = st.columns(7)
    for i, day in enumerate(downscaled[:7]):
        with cols[i]:
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
            day_name = date_obj.strftime("%a")
            date_str = date_obj.strftime("%d %b")

            st.markdown(f"**{day_name}**")
            st.caption(date_str)

            # Weather icon based on conditions
            rain = day.get("rainfall_mm", 0)
            temp_max = day.get("temp_max", 25)
            if rain > 10:
                st.markdown("🌧️")
            elif rain > 0:
                st.markdown("🌦️")
            elif temp_max > 35:
                st.markdown("🔥")
            elif temp_max < 5:
                st.markdown("🥶")
            else:
                st.markdown("☀️")

            st.markdown(f"**{temp_max:.1f}°** / {day.get('temp_min', 0):.1f}°")
            st.caption(f"💧 {rain:.1f}mm")
            st.caption(f"💨 {day.get('wind_kmh', 0):.0f} km/h")

# --- Temperature & Rainfall Trend Charts ---
# --- Rainfall Focus + Advisory Link (per-village, drives advisory) ---
if downscaled:
    st.subheader("🌧️ Rainfall Focus (next 7 days)")
    tot_rain = sum(d.get("rainfall_mm", 0) for d in downscaled)
    rainy_days = [d for d in downscaled if d.get("rainfall_mm", 0) >= 2.5]
    heaviest = max(downscaled, key=lambda d: d.get("rainfall_mm", 0))
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Total Rain (7-day)", f"{tot_rain:.1f} mm")
    with r2:
        st.metric("Rainy Days (≥2.5mm)", len(rainy_days))
    with r3:
        st.metric("Heaviest Day", f"{heaviest['date'][5:]} ({heaviest.get('rainfall_mm', 0):.1f} mm)")
    with r4:
        if tot_rain >= 35:
            verdict = "Skip irrigation — enough rain"
        elif tot_rain >= 10:
            verdict = "Light irrigation only if dry"
        else:
            verdict = "No useful rain — irrigate"
        st.metric("Irrigation Verdict", verdict)

    if st.button("🌾 Optimize advisory for this village →", type="primary"):
        try:
            st.switch_page("pages/2_🌾_Advisory.py")
        except Exception:
            st.caption("Open the **Advisory** page in the sidebar — this village is already selected.")

st.subheader("📊 Weather Trends")

if downscaled:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        dates = [d["date"] for d in downscaled]
        temp_max = [d["temp_max"] for d in downscaled]
        temp_min = [d["temp_min"] for d in downscaled]
        coarse_temp = [d["temp_max"] for d in coarse] if coarse else [None] * len(dates)

        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=dates, y=temp_max, mode="lines+markers",
            name="Downscaled Max", line=dict(color="#e74c3c", width=3),
        ))
        fig_temp.add_trace(go.Scatter(
            x=dates, y=temp_min, mode="lines+markers",
            name="Downscaled Min", line=dict(color="#3498db", width=3),
        ))
        if coarse and coarse[0].get("temp_max"):
            fig_temp.add_trace(go.Scatter(
                x=dates, y=[d["temp_max"] for d in coarse],
                mode="lines", name="Coarse (Block)",
                line=dict(color="#95a5a6", width=2, dash="dash"),
            ))
        fig_temp.update_layout(
            title="Temperature (°C)", xaxis_title="Date", yaxis_title="Temp °C",
            height=300, margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with col_chart2:
        rainfall = [d.get("rainfall_mm", 0) for d in downscaled]
        humidity = [d.get("humidity", 60) for d in downscaled]

        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(
            x=dates, y=rainfall, name="Rainfall (mm)",
            marker_color="#3498db",
        ))
        fig_rain.add_trace(go.Scatter(
            x=dates, y=humidity, mode="lines+markers",
            name="Humidity %", yaxis="y2",
            line=dict(color="#2ecc71", width=2),
        ))
        fig_rain.update_layout(
            title="Rainfall & Humidity",
            xaxis_title="Date",
            yaxis=dict(title="Rainfall (mm)", side="left"),
            yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", range=[0, 100]),
            height=300, margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_rain, use_container_width=True)

    # --- Wind & Improvement Metrics ---
    col_wind, col_metrics = st.columns([2, 1])

    with col_wind:
        wind = [d.get("wind_kmh", 0) for d in downscaled]
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(
            x=dates, y=wind, mode="lines+markers",
            fill="tozeroy", name="Wind Speed (km/h)",
            line=dict(color="#9b59b6", width=2),
        ))
        fig_wind.update_layout(
            title="Wind Speed (km/h)", xaxis_title="Date", yaxis_title="km/h",
            height=250, margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_wind, use_container_width=True)

    with col_metrics:
        st.subheader("Improvement Metrics")
        for key, value in metrics.items():
            label = key.replace("_", " ").title()
            st.metric(label=label, value=str(value))
else:
    st.warning("No forecast data available.")
