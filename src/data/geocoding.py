import asyncio
import urllib.parse
from typing import List, Optional, Dict, Any
import httpx
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from pydantic import BaseModel
from cachetools import TTLCache

class LocationInfo(BaseModel):
    """Administrative location information."""
    display_name: str
    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    panchayat: Optional[str] = None
    latitude: float
    longitude: float

class GeocodingService:
    """Service for geocoding and reverse geocoding locations."""
    
    REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    SEARCH_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "AgroAdvisorySystem/1.0 (agro_advisory@example.com)"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)
        # Nominatim API terms of service require 1 second delay between requests
        self._last_request_time = 0.0
        self._cache = TTLCache(maxsize=500, ttl=86400 * 7) # Cache for 1 week

    async def _respect_rate_limit(self):
        """Ensure 1 second delay between API calls."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        if time_since_last < 1.1:
            await asyncio.sleep(1.1 - time_since_last)
        self._last_request_time = asyncio.get_event_loop().time()

    def _extract_admin_hierarchy(self, address: Dict[str, str], lat: float, lon: float, display_name: str) -> LocationInfo:
        """Extract state, district, block, panchayat from Nominatim address dict."""
        return LocationInfo(
            display_name=display_name,
            latitude=lat,
            longitude=lon,
            state=address.get("state"),
            district=address.get("state_district") or address.get("county") or address.get("district"),
            block=address.get("county") or address.get("municipality") or address.get("city_district"),
            panchayat=address.get("village") or address.get("suburb") or address.get("town") or address.get("neighbourhood")
        )

    async def reverse_geocode(self, lat: float, lon: float) -> LocationInfo:
        """Reverse geocode coordinates to get administrative locations."""
        cache_key = f"rev_{lat:.4f}_{lon:.4f}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        await self._respect_rate_limit()
        
        headers = {"User-Agent": self.USER_AGENT}
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": 18,
            "addressdetails": 1
        }
        
        logger.info(f"Reverse geocoding {lat}, {lon}")
        try:
            response = await self.client.get(self.REVERSE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.warning(f"Geocoding error for {lat}, {lon}: {data['error']}")
                return LocationInfo(display_name="Unknown", latitude=lat, longitude=lon)
                
            address = data.get("address", {})
            display_name = data.get("display_name", "")
            
            location = self._extract_admin_hierarchy(address, lat, lon, display_name)
            self._cache[cache_key] = location
            return location
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during reverse geocoding: {e}")
            return LocationInfo(display_name="Error", latitude=lat, longitude=lon)

    async def search_location(self, query: str) -> List[LocationInfo]:
        """Forward geocode a search query (focusing on India context implicitly if desired)."""
        cache_key = f"search_{query}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        await self._respect_rate_limit()
        
        headers = {"User-Agent": self.USER_AGENT}
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 5
        }
        
        logger.info(f"Searching location: {query}")
        try:
            response = await self.client.get(self.SEARCH_URL, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()
            
            locations = []
            for item in results:
                lat = float(item.get("lat", 0.0))
                lon = float(item.get("lon", 0.0))
                address = item.get("address", {})
                display_name = item.get("display_name", "")
                
                locations.append(self._extract_admin_hierarchy(address, lat, lon, display_name))
                
            self._cache[cache_key] = locations
            return locations
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during location search: {e}")
            return []

    async def get_administrative_hierarchy(self, lat: float, lon: float) -> LocationInfo:
        """Alias for reverse geocode returning the state -> district -> block -> panchayat hierarchy."""
        return await self.reverse_geocode(lat, lon)

    async def close(self):
        """Close the internal HTTP client."""
        await self.client.aclose()
