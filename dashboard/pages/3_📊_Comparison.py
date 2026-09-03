"""Model Comparison Page.

Compares coarse (block-level) vs downscaled (panchayat-level) forecasts
with real visualizations and accuracy metrics.
"""

import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Comparison", page_icon="📊", layout="wide")

st.title("📊 Block vs Panchayat: Downscaling Comparison")

lat = st.session_state.get("lat", 23.275)
lon = st.session_state.get("lon", 77.335)
API_BASE = "http://localhost:8000"

st.markdown("""
This page demonstrates the effectiveness of our ML downscaling pipeline.
By downscaling coarse Open-Meteo data from a ~10km grid (Block level) to a ~1km grid (Panchayat level) using 
local elevation, terrain features, and lapse rate corrections, we achieve much higher precision for agricultural decisions.
""")

# --- Fetch forecast data ---
data = None
try:
    resp = httpx.get(
        f"{API_BASE}/api/forecast",
        params={"lat": lat, "lon": lon, "days": 7},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
except Exception:
    pass

if data is None:
    st.error("Unable to fetch data. Please ensure the API server is running.")
    st.stop()

coarse = data.get("coarse_forecast", [])
downscaled = data.get("downscaled_forecast", [])
metrics = data.get("improvement_metrics", {})

if not coarse or not downscaled:
    st.warning("No forecast data available for comparison.")
    st.stop()

# --- Metrics Overview ---
st.subheader("🎯 Downscaling Improvement Metrics")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Resolution", "10km → 1km", delta="10x improvement")
with m2:
    st.metric("Elevation", f"{metrics.get('elevation_m', 'N/A')}m", help="Local elevation for lapse rate correction")
with m3:
    st.metric("Model", metrics.get("model_type", "statistical_only").upper())
with m4:
    st.metric("Correction", metrics.get("rmse_reduction", "N/A"), help="Average temperature correction applied")

st.divider()

# --- Side-by-side comparison ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Coarse Forecast (Block Level, ~10km)")
    if coarse:
        dates = [d["date"] for d in coarse]
        fig_coarse = go.Figure()
        fig_coarse.add_trace(go.Scatter(
            x=dates, y=[d["temp_max"] for d in coarse],
            mode="lines+markers", name="Temp Max",
            line=dict(color="#e74c3c", width=2),
        ))
        fig_coarse.add_trace(go.Scatter(
            x=dates, y=[d["temp_min"] for d in coarse],
            mode="lines+markers", name="Temp Min",
            line=dict(color="#3498db", width=2),
        ))
        fig_coarse.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Temperature (°C)",
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_coarse, use_container_width=True)
        avg_temp = np.mean([d["temp_max"] for d in coarse])
        st.metric("Avg Max Temp", f"{avg_temp:.1f}°C")

with col2:
    st.subheader("🟢 Downscaled Forecast (Panchayat Level, ~1km)")
    if downscaled:
        dates = [d["date"] for d in downscaled]
        fig_ds = go.Figure()
        fig_ds.add_trace(go.Scatter(
            x=dates, y=[d["temp_max"] for d in downscaled],
            mode="lines+markers", name="Temp Max",
            line=dict(color="#27ae60", width=2),
        ))
        fig_ds.add_trace(go.Scatter(
            x=dates, y=[d["temp_min"] for d in downscaled],
            mode="lines+markers", name="Temp Min",
            line=dict(color="#2980b9", width=2),
        ))
        fig_ds.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Temperature (°C)",
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_ds, use_container_width=True)
        avg_temp_ds = np.mean([d["temp_max"] for d in downscaled])
        delta = avg_temp_ds - avg_temp
        st.metric("Avg Max Temp", f"{avg_temp_ds:.1f}°C", delta=f"{delta:+.1f}°C vs coarse")

# --- Overlay Comparison ---
st.subheader("📈 Temperature Overlay: Coarse vs Downscaled")
fig_overlay = go.Figure()
dates = [d["date"] for d in downscaled]

fig_overlay.add_trace(go.Scatter(
    x=dates, y=[d["temp_max"] for d in coarse],
    mode="lines+markers", name="Coarse Max",
    line=dict(color="#e74c3c", width=2, dash="dash"),
))
fig_overlay.add_trace(go.Scatter(
    x=dates, y=[d["temp_max"] for d in downscaled],
    mode="lines+markers", name="Downscaled Max",
    line=dict(color="#27ae60", width=3),
))
fig_overlay.add_trace(go.Scatter(
    x=dates, y=[d["temp_min"] for d in coarse],
    mode="lines+markers", name="Coarse Min",
    line=dict(color="#3498db", width=2, dash="dash"),
))
fig_overlay.add_trace(go.Scatter(
    x=dates, y=[d["temp_min"] for d in downscaled],
    mode="lines+markers", name="Downscaled Min",
    line=dict(color="#2980b9", width=3),
))
fig_overlay.update_layout(
    height=350, yaxis_title="Temperature (°C)",
    legend=dict(x=0.01, y=0.99),
)
st.plotly_chart(fig_overlay, use_container_width=True)

# --- Difference Analysis ---
st.subheader("🔍 Downscaling Corrections Applied")
diff_data = []
for i in range(min(len(coarse), len(downscaled))):
    diff_data.append({
        "date": coarse[i]["date"],
        "temp_max_diff": round(downscaled[i]["temp_max"] - coarse[i]["temp_max"], 2),
        "temp_min_diff": round(downscaled[i]["temp_min"] - coarse[i]["temp_min"], 2),
        "rain_diff": round(downscaled[i]["rainfall_mm"] - coarse[i]["rainfall_mm"], 2),
        "wind_diff": round(downscaled[i]["wind_kmh"] - coarse[i]["wind_kmh"], 2),
    })

if diff_data:
    fig_diff = go.Figure()
    fig_diff.add_trace(go.Bar(
        x=[d["date"] for d in diff_data],
        y=[d["temp_max_diff"] for d in diff_data],
        name="Temp Max Correction (°C)",
        marker_color="#e74c3c",
    ))
    fig_diff.add_trace(go.Bar(
        x=[d["date"] for d in diff_data],
        y=[d["temp_min_diff"] for d in diff_data],
        name="Temp Min Correction (°C)",
        marker_color="#3498db",
    ))
    fig_diff.update_layout(
        barmode="group", height=300,
        yaxis_title="Correction (°C)",
        title="Elevation Lapse Rate Corrections Applied by Downscaling",
    )
    st.plotly_chart(fig_diff, use_container_width=True)

    st.caption(
        f"Corrections are based on elevation difference ({metrics.get('elevation_m', 'N/A')}m vs 500m reference) "
        f"using the standard atmospheric lapse rate of -6.5°C/km."
    )

# --- Detailed Parameter Comparison ---
st.subheader("📋 Detailed Parameter Comparison")
import pandas as pd

comparison_rows = []
for i in range(min(len(coarse), len(downscaled))):
    comparison_rows.append({
        "Date": coarse[i]["date"],
        "Coarse Temp Max": coarse[i]["temp_max"],
        "Downscaled Temp Max": downscaled[i]["temp_max"],
        "Δ Temp Max": round(downscaled[i]["temp_max"] - coarse[i]["temp_max"], 2),
        "Coarse Rain (mm)": coarse[i]["rainfall_mm"],
        "Downscaled Rain (mm)": downscaled[i]["rainfall_mm"],
        "Δ Rain (mm)": round(downscaled[i]["rainfall_mm"] - coarse[i]["rainfall_mm"], 2),
    })

df = pd.DataFrame(comparison_rows)
st.dataframe(df, use_container_width=True, hide_index=True)
