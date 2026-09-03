"""Village search endpoint for the Forecast page.

Search order (across ALL blocks):
  1. Bundled block datasets (instant, offline).
  2. Live Nominatim search restricted to Madhya Pradesh.
Never 500s — live failure just returns dataset-only results.
"""

from typing import Optional
from fastapi import APIRouter, Query
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

from src.data.panchayats import PanchayatService
from src.data.geocoding import GeocodingService

router = APIRouter(prefix="/api/search", tags=["search"])

_service = PanchayatService()
_geo: Optional[GeocodingService] = None


def _get_geo() -> GeocodingService:
    global _geo
    if _geo is None:
        _geo = GeocodingService()
    return _geo


@router.get("/villages")
async def search_villages(
    q: str = Query(..., min_length=2, description="Village name to search in Madhya Pradesh"),
):
    """Search MP villages by name; returns candidates with coordinates."""
    query = q.strip().lower()
    results = []

    for b in _service.list_blocks():
        for v in _service.list_villages(b.block_id):
            if query in v.name.lower() or (v.hindi_name and query in v.hindi_name):
                results.append({
                    "name": v.name, "hindi_name": v.hindi_name,
                    "lat": v.lat, "lon": v.lon,
                    "district": b.district, "block": b.block,
                    "block_id": b.block_id,
                    "source": "dataset",
                })

    try:
        live = await _get_geo().search_location(f"{q.strip()}, Madhya Pradesh, India")
        for loc in live[:5]:
            if loc.state and "madhya pradesh" not in loc.state.lower():
                continue
            if any(abs(r["lat"] - loc.latitude) < 0.005
                   and abs(r["lon"] - loc.longitude) < 0.005 for r in results):
                continue
            results.append({
                "name": (loc.panchayat or loc.display_name.split(",")[0]).strip(),
                "hindi_name": "",
                "lat": round(loc.latitude, 5), "lon": round(loc.longitude, 5),
                "district": loc.district or "", "block": loc.block or "",
                "block_id": "",
                "source": "nominatim",
            })
    except Exception as e:
        logger.warning(f"Live village search failed, dataset-only results: {e}")

    return {"query": q.strip(), "count": len(results), "results": results[:10]}
