"""Location services API - real geocoding via OpenStreetMap Nominatim."""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict
from loguru import logger

from src.api.schemas import LocationInfo
from src.data.geocoding import GeocodingService
from src.utils.translation import get_supported_languages

router = APIRouter(prefix="/api", tags=["locations"])

_geocoding: GeocodingService = None


def _get_geocoding() -> GeocodingService:
    global _geocoding
    if _geocoding is None:
        _geocoding = GeocodingService()
    return _geocoding


@router.get("/locations/search")
async def search_locations(q: str = Query(..., min_length=2, description="Search query (place name)")) -> List[Dict]:
    """Search for locations by name using Nominatim geocoding.

    Returns matching locations with administrative hierarchy
    (state, district, block, panchayat).
    """
    logger.info(f"Location search: '{q}'")
    geocoding = _get_geocoding()
    try:
        results = await geocoding.search_location(q)
        locations = []
        for loc in results:
            locations.append({
                "name": loc.display_name,
                "lat": loc.latitude,
                "lon": loc.longitude,
                "state": loc.state or "",
                "district": loc.district or "",
                "block": loc.block or "",
                "panchayat": loc.panchayat or "",
            })
        return locations
    except Exception as e:
        logger.error(f"Location search error: {e}")
        return []


@router.get("/locations/reverse", response_model=LocationInfo)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Reverse geocode coordinates to get administrative location.

    Returns state, district, block, and panchayat information.
    """
    logger.info(f"Reverse geocode: ({lat}, {lon})")
    geocoding = _get_geocoding()
    try:
        location = await geocoding.reverse_geocode(lat, lon)
        return LocationInfo(
            lat=location.latitude,
            lon=location.longitude,
            state=location.state,
            district=location.district,
            block=location.block,
            panchayat=location.panchayat,
        )
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}")
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@router.get("/crops")
async def get_crops() -> List[Dict[str, str]]:
    """List all supported crops with their metadata."""
    from src.advisory.crop_rules import CropAdvisoryEngine
    engine = CropAdvisoryEngine()
    crops = []
    for name, info in engine.crops_data.items():
        crops.append({
            "id": name,
            "name": info.name,
            "hindi_name": info.hindi_name,
            "scientific_name": info.scientific_name,
            "seasons": ", ".join(info.seasons),
            "irrigation_sensitivity": info.irrigation_sensitivity,
        })
    return crops


@router.get("/languages")
async def get_languages() -> List[Dict[str, str]]:
    """List supported advisory languages."""
    return get_supported_languages()
