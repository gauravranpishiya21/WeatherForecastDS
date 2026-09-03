"""Folium map components for the dashboard."""

import folium
from typing import List, Dict, Any, Optional


def create_forecast_map(
    lat: float,
    lon: float,
    forecast_data: Optional[Dict[str, Any]] = None,
    zoom_start: int = 12,
) -> folium.Map:
    """Create a Folium map with location marker and optional weather overlay.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        forecast_data: Optional forecast data for weather overlays.
        zoom_start: Initial zoom level.

    Returns:
        Folium Map object.
    """
    m = folium.Map(location=[lat, lon], zoom_start=zoom_start, tiles="OpenStreetMap")

    # Main location marker
    popup_html = f"<b>Selected Location</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}"
    if forecast_data:
        today = forecast_data.get("downscaled_forecast", [{}])[0] if forecast_data.get("downscaled_forecast") else {}
        if today:
            popup_html += f"<br>Temp: {today.get('temp_max', 'N/A')}°C"
            popup_html += f"<br>Rain: {today.get('rainfall_mm', 'N/A')}mm"

    folium.Marker(
        [lat, lon],
        popup=folium.Popup(popup_html, max_width=200),
        icon=folium.Icon(color="red", icon="cloud", prefix="fa"),
    ).add_to(m)

    # Add circle overlay for temperature indication
    if forecast_data:
        downscaled = forecast_data.get("downscaled_forecast", [])
        if downscaled:
            today = downscaled[0]
            temp = today.get("temp_max", 25)
            color = "red" if temp > 35 else "orange" if temp > 30 else "blue" if temp < 10 else "green"
            folium.CircleMarker(
                [lat, lon], radius=25,
                color=color, fill=True, fill_opacity=0.3,
                popup=f"Temperature: {temp}°C",
            ).add_to(m)

    return m
