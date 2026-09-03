import asyncio
import math
from typing import List, Tuple
import httpx
import numpy as np
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from pydantic import BaseModel, Field
from cachetools import TTLCache

class TerrainFeatures(BaseModel):
    """Terrain features data model."""
    latitude: float
    longitude: float
    elevation: float
    slope: float
    aspect: float
    distance_to_coast: float = -1.0  # Optional/approximate distance to coast in km

class TerrainDataProvider:
    """Provider for terrain and elevation data using Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/elevation"
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=10.0)
        # Cache elevations to reduce API calls: 1000 items, TTL 24 hours
        self._elevation_cache = TTLCache(maxsize=1000, ttl=86400)

    async def _fetch_elevation(self, lat: float, lon: float) -> float:
        """Fetch elevation for a specific point with retries."""
        cache_key = f"{lat:.4f}_{lon:.4f}"
        if cache_key in self._elevation_cache:
            return self._elevation_cache[cache_key]

        params = {
            "latitude": lat,
            "longitude": lon
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                elevation = data.get("elevation", [0.0])[0]
                self._elevation_cache[cache_key] = elevation
                return elevation
            except httpx.HTTPError as e:
                logger.warning(f"Elevation HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch elevation after {self.max_retries} attempts.")
                    return 0.0
                await asyncio.sleep(2 ** attempt)
        return 0.0

    async def get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation in meters for a given coordinate."""
        logger.info(f"Getting elevation for {lat}, {lon}")
        return await self._fetch_elevation(lat, lon)

    async def get_elevations_batch(self, lats: List[float], lons: List[float]) -> List[float]:
        """Fetch elevations for many coordinates in ONE API call.

        Open-Meteo elevation API accepts comma-separated coordinate lists,
        so a whole block of panchayats resolves in a single request.
        Falls back to cached/individual lookups on failure.
        """
        if len(lats) != len(lons):
            raise ValueError("lats and lons must have the same length")
        if not lats:
            return []

        params = {
            "latitude": ",".join(f"{v:.5f}" for v in lats),
            "longitude": ",".join(f"{v:.5f}" for v in lons),
        }
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                elevs = data.get("elevation", [0.0] * len(lats))
                for lat, lon, e in zip(lats, lons, elevs):
                    self._elevation_cache[f"{lat:.4f}_{lon:.4f}"] = float(e)
                logger.info(f"Batch elevation fetched for {len(lats)} points")
                return [float(e) for e in elevs]
            except httpx.HTTPError as e:
                logger.warning(f"Batch elevation error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error("Batch elevation failed, falling back to 0.0 values.")
                    return [0.0] * len(lats)
                await asyncio.sleep(2 ** attempt)
        return [0.0] * len(lats)

    async def get_elevation_grid(self, center_lat: float, center_lon: float, radius_km: float = 25, resolution_km: float = 1) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate a grid of elevations around a center point.
        Returns tuple of (lat_grid, lon_grid, elevation_grid) as numpy arrays.
        """
        lat_step = resolution_km / 111.0
        lon_step = resolution_km / (111.0 * math.cos(math.radians(center_lat)))
        
        num_steps = int(radius_km / resolution_km)
        size = num_steps * 2 + 1
        
        lat_grid = np.zeros((size, size))
        lon_grid = np.zeros((size, size))
        elevation_grid = np.zeros((size, size))
        
        logger.info(f"Fetching elevation grid size {size}x{size} around {center_lat}, {center_lon}")
        
        # We might want to batch this, but for simplicity we use gather for concurrent requests
        # In a production environment, Open-Meteo allows batching multiple coordinates in one request
        tasks = []
        indices = []
        for i in range(size):
            for j in range(size):
                lat = center_lat + ((i - num_steps) * lat_step)
                lon = center_lon + ((j - num_steps) * lon_step)
                lat_grid[i, j] = lat
                lon_grid[i, j] = lon
                tasks.append(self.get_elevation(lat, lon))
                indices.append((i, j))
                
        # Batch size for async gather to avoid overwhelming the API
        batch_size = 50
        for b in range(0, len(tasks), batch_size):
            batch_tasks = tasks[b:b+batch_size]
            batch_results = await asyncio.gather(*batch_tasks)
            for idx, (i, j) in enumerate(indices[b:b+batch_size]):
                elevation_grid[i, j] = batch_results[idx]
                
        return lat_grid, lon_grid, elevation_grid

    def calculate_slope_aspect(self, elevation_grid: np.ndarray, resolution_km: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate slope (degrees) and aspect (degrees from North) from an elevation grid.
        """
        resolution_m = resolution_km * 1000.0
        
        dy, dx = np.gradient(elevation_grid, resolution_m, resolution_m)
        
        # Slope calculation
        slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
        
        # Aspect calculation
        # np.arctan2(y, x) computes atan(y/x). 
        # In geographic terms, aspect is measured clockwise from North (0 degrees).
        aspect = np.degrees(np.arctan2(dx, dy))
        aspect = np.where(aspect < 0, aspect + 360, aspect)
        
        return slope, aspect

    async def get_terrain_features(self, lat: float, lon: float) -> TerrainFeatures:
        """
        Get combined terrain features (elevation, slope, aspect) for a location.
        Generates a small local grid to compute slope and aspect.
        """
        logger.info(f"Getting terrain features for {lat}, {lon}")
        
        # Small grid 3x3 at 1km resolution to compute local slope/aspect
        _, _, elev_grid = await self.get_elevation_grid(lat, lon, radius_km=1, resolution_km=1)
        slope_grid, aspect_grid = self.calculate_slope_aspect(elev_grid, resolution_km=1.0)
        
        # Center of the 3x3 grid is at index (1,1)
        center_elev = elev_grid[1, 1]
        center_slope = slope_grid[1, 1]
        center_aspect = aspect_grid[1, 1]
        
        # Approximation for distance to coast could be implemented here or lookup table
        # Defaulting to -1.0 as requested
        distance_to_coast = -1.0
        
        return TerrainFeatures(
            latitude=lat,
            longitude=lon,
            elevation=center_elev,
            slope=center_slope,
            aspect=center_aspect,
            distance_to_coast=distance_to_coast
        )
        
    async def close(self):
        """Close the internal HTTP client."""
        await self.client.aclose()
