"""Reusable Plotly chart components for the dashboard."""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any


def temperature_chart(forecast: List[Dict[str, Any]]) -> go.Figure:
    """Create a temperature trend chart with max/min and optional coarse overlay."""
    dates = [d["date"] for d in forecast]
    temp_max = [d.get("temp_max", d.get("temperature_2m_max", 0)) for d in forecast]
    temp_min = [d.get("temp_min", d.get("temperature_2m_min", 0)) for d in forecast]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=temp_max, mode="lines+markers",
        name="Max Temp", line=dict(color="#e74c3c", width=2),
        fill="tonexty",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=temp_min, mode="lines+markers",
        name="Min Temp", line=dict(color="#3498db", width=2),
    ))
    fig.update_layout(
        title="Temperature Trend", xaxis_title="Date", yaxis_title="°C",
        height=300, margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def rainfall_chart(forecast: List[Dict[str, Any]]) -> go.Figure:
    """Create a rainfall bar chart with humidity line overlay."""
    dates = [d["date"] for d in forecast]
    rainfall = [d.get("rainfall_mm", d.get("precipitation_sum", 0)) for d in forecast]
    humidity = [d.get("humidity", d.get("relative_humidity_2m_mean", 60)) for d in forecast]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=rainfall, name="Rainfall (mm)",
        marker_color="#3498db",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=humidity, mode="lines+markers",
        name="Humidity %", yaxis="y2",
        line=dict(color="#2ecc71", width=2),
    ))
    fig.update_layout(
        title="Rainfall & Humidity",
        yaxis=dict(title="Rainfall (mm)"),
        yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", range=[0, 100]),
        height=300, margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(x=0.01, y=0.99),
    )
    return fig


def risk_gauge(score: int) -> go.Figure:
    """Create a risk score gauge chart (0-100)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Risk Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 30], "color": "#2ecc71"},
                {"range": [30, 60], "color": "#f39c12"},
                {"range": [60, 80], "color": "#e67e22"},
                {"range": [80, 100], "color": "#e74c3c"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=0))
    return fig


def comparison_chart(coarse: List[Dict], downscaled: List[Dict]) -> go.Figure:
    """Create a side-by-side comparison chart of coarse vs downscaled."""
    dates = [d["date"] for d in downscaled]
    ds_temp = [d.get("temp_max", 0) for d in downscaled]
    coarse_temp = [d.get("temp_max", 0) for d in coarse[:len(downscaled)]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=coarse_temp, mode="lines+markers",
        name="Coarse (Block ~10km)", line=dict(color="#95a5a6", width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=ds_temp, mode="lines+markers",
        name="Downscaled (Panchayat ~1km)", line=dict(color="#27ae60", width=3),
    ))
    fig.update_layout(
        title="Coarse vs Downscaled Temperature",
        xaxis_title="Date", yaxis_title="Temperature (°C)",
        height=350, margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(x=0.01, y=0.99),
    )
    return fig
