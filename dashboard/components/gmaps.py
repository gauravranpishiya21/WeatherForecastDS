"""Google Maps embed component for the dashboard.

Renders the block's panchayat villages on real Google Maps tiles
(Markers color-coded by risk) via st.components.v1.html.
Falls back to Folium/OpenStreetMap when no API key is configured.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, List


def get_maps_key() -> str:
    """Return the Google Maps API key from settings or environment."""
    try:
        root = str(Path(__file__).resolve().parent.parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from src.utils.config import get_settings
        key = get_settings().google_maps_api_key or ""
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GOOGLE_MAPS_API_KEY", "")


def gmaps_block_html(
    villages: List[dict[str, Any]],
    center_lat: float,
    center_lon: float,
    api_key: str,
    height: int = 420,
) -> str:
    """Build an HTML snippet with all villages as Google Maps markers."""
    markers = []
    for v in villages:
        t = v.get("today", {})
        r = v.get("risk", {})
        popup = (
            f"<b>{v.get('name', '')} ({v.get('hindi_name', '')})</b><br>"
            f"Elev: {v.get('elevation_m', '')} m<br>"
            f"Temp: {t.get('temp_max', '')}&deg; / {t.get('temp_min', '')}&deg;C<br>"
            f"Rain: {t.get('rainfall_mm', '')} mm | Hum: {t.get('humidity', '')}%<br>"
            f"Risk: {r.get('level', '')} ({r.get('top_risk', '')})"
        )
        markers.append({
            "name": v.get("name", ""),
            "lat": v.get("lat", 0.0),
            "lon": v.get("lon", 0.0),
            "color": r.get("color", "gray"),
            "popup": popup,
        })

    data_js = json.dumps(markers, ensure_ascii=False)
    return f"""
<div id="gmap-block" style="height:{height}px;width:100%;border-radius:10px;"></div>
<script>
  function initGMapBlock() {{
    const center = {{ lat: {center_lat}, lng: {center_lon} }};
    const map = new google.maps.Map(document.getElementById('gmap-block'), {{
      zoom: 12, center: center, mapTypeId: 'roadmap'
    }});
    const colors = {{ green: '#2ecc71', yellow: '#f1c40f', orange: '#e67e22', red: '#e74c3c' }};
    const data = {data_js};
    data.forEach(v => {{
      const marker = new google.maps.Marker({{
        position: {{ lat: v.lat, lng: v.lon }},
        map: map, title: v.name,
        icon: {{
          path: google.maps.SymbolPath.CIRCLE, scale: 9,
          fillColor: colors[v.color] || '#95a5a6', fillOpacity: 0.9,
          strokeWeight: 1.5, strokeColor: '#ffffff'
        }}
      }});
      const info = new google.maps.InfoWindow({{ content: v.popup }});
      marker.addListener('click', () => info.open(map, marker));
    }});
  }}
</script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initGMapBlock"></script>
"""
