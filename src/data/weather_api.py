import asyncio
import math
from typing import List, Optional
import httpx
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from pydantic import BaseModel, Field

# WMO Weather interpretation codes mapped to human-readable descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle (light)", 57: "Freezing drizzle (dense)",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain (light)", 67: "Freezing rain (heavy)",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def weather_code_to_description(code: int) -> str:
    """Convert WMO weather code to human-readable description."""
    return WMO_CODES.get(code, f"Unknown ({code})")

class DailyForecast(BaseModel):
    """Daily forecast data model."""
    date: str
    temperature_2m_max: float
    temperature_2m_min: float
    apparent_temperature_max: float
    apparent_temperature_min: float
    precipitation_sum: float
    precipitation_probability_max: int
    relative_humidity_2m_mean: float
    wind_speed_10m_max: float
    wind_direction_10m_dominant: float
    weathercode: int
    weather_description: str = ""
    soil_temperature_0cm: Optional[float] = None
    soil_moisture_0_to_1cm: Optional[float] = None

class CurrentWeather(BaseModel):
    """Current weather data model."""
    time: str
    temperature_2m: float
    relative_humidity_2m: float
    apparent_temperature: float
    is_day: int
    precipitation: float
    weathercode: int
    weather_description: str = ""
    wind_speed_10m: float
    wind_direction_10m: float

class WeatherPoint(BaseModel):
    """Weather data for a specific point."""
    latitude: float
    longitude: float
    current: Optional[CurrentWeather] = None
    daily: List[DailyForecast] = Field(default_factory=list)

class ForecastGrid(BaseModel):
    """Grid of weather forecasts for downscaling."""
    center_latitude: float
    center_longitude: float
    points: List[WeatherPoint] = Field(default_factory=list)

class OpenMeteoClient:
    """Client for fetching weather data from Open-Meteo."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _fetch(self, params: dict) -> dict:
        """Helper to fetch data with retries and exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP {e.response.status_code} on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed after {self.max_retries} attempts.")
                    raise
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        return {}

    async def get_forecast(self, lat: float, lon: float, days: int = 7) -> WeatherPoint:
        """Fetch daily forecast for a specific location from Open-Meteo."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max", "temperature_2m_min",
                "apparent_temperature_max", "apparent_temperature_min",
                "precipitation_sum", "precipitation_probability_max",
                "wind_speed_10m_max", "wind_direction_10m_dominant",
                "weathercode"
            ],
            "hourly": ["relative_humidity_2m", "soil_temperature_0cm", "soil_moisture_0_to_1cm"],
            "timezone": "auto",
            "forecast_days": days
        }

        logger.info(f"Fetching forecast for ({lat:.4f}, {lon:.4f}) for {days} days")
        data = await self._fetch(params)

        daily_data = data.get("daily", {})
        hourly_data = data.get("hourly", {})

        forecasts = []
        if daily_data:
            dates = daily_data.get("time", [])
            for i, date in enumerate(dates):
                hours_in_day = 24
                start_idx = i * hours_in_day
                end_idx = start_idx + hours_in_day

                rh_mean = 0.0
                rh_vals = hourly_data.get("relative_humidity_2m", [])[start_idx:end_idx]
                if rh_vals:
                    valid_rh = [v for v in rh_vals if v is not None]
                    if valid_rh:
                        rh_mean = sum(valid_rh) / len(valid_rh)

                soil_temp = None
                soil_t_vals = hourly_data.get("soil_temperature_0cm", [])[start_idx:end_idx]
                if soil_t_vals:
                    valid_st = [v for v in soil_t_vals if v is not None]
                    if valid_st:
                        soil_temp = sum(valid_st) / len(valid_st)

                soil_moisture = None
                soil_m_vals = hourly_data.get("soil_moisture_0_to_1cm", [])[start_idx:end_idx]
                if soil_m_vals:
                    valid_sm = [v for v in soil_m_vals if v is not None]
                    if valid_sm:
                        soil_moisture = sum(valid_sm) / len(valid_sm)

                wc = daily_data.get("weathercode", [0])[i] if i < len(daily_data.get("weathercode", [])) else 0

                forecast = DailyForecast(
                    date=date,
                    temperature_2m_max=daily_data.get("temperature_2m_max", [0.0])[i],
                    temperature_2m_min=daily_data.get("temperature_2m_min", [0.0])[i],
                    apparent_temperature_max=daily_data.get("apparent_temperature_max", [0.0])[i],
                    apparent_temperature_min=daily_data.get("apparent_temperature_min", [0.0])[i],
                    precipitation_sum=daily_data.get("precipitation_sum", [0.0])[i],
                    precipitation_probability_max=daily_data.get("precipitation_probability_max", [0])[i],
                    wind_speed_10m_max=daily_data.get("wind_speed_10m_max", [0.0])[i],
                    wind_direction_10m_dominant=daily_data.get("wind_direction_10m_dominant", [0.0])[i],
                    weathercode=wc,
                    weather_description=weather_code_to_description(wc),
                    relative_humidity_2m_mean=round(rh_mean, 1),
                    soil_temperature_0cm=round(soil_temp, 1) if soil_temp is not None else None,
                    soil_moisture_0_to_1cm=round(soil_moisture, 4) if soil_moisture is not None else None,
                )
                forecasts.append(forecast)

        return WeatherPoint(latitude=lat, longitude=lon, daily=forecasts)

    async def get_current_weather(self, lat: float, lon: float) -> WeatherPoint:
        """Fetch current weather conditions."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "weathercode", "wind_speed_10m",
                "wind_direction_10m"
            ],
            "timezone": "auto"
        }
        
        logger.info(f"Fetching current weather for ({lat:.4f}, {lon:.4f})")
        data = await self._fetch(params)
        
        current_data = data.get("current", {})
        wc = current_data.get("weathercode", 0)
        current = CurrentWeather(
            time=current_data.get("time", ""),
            temperature_2m=current_data.get("temperature_2m", 0.0),
            relative_humidity_2m=current_data.get("relative_humidity_2m", 0.0),
            apparent_temperature=current_data.get("apparent_temperature", 0.0),
            is_day=current_data.get("is_day", 1),
            precipitation=current_data.get("precipitation", 0.0),
            weathercode=wc,
            weather_description=weather_code_to_description(wc),
            wind_speed_10m=current_data.get("wind_speed_10m", 0.0),
            wind_direction_10m=current_data.get("wind_direction_10m", 0.0)
        )
        
        return WeatherPoint(latitude=lat, longitude=lon, current=current)

    async def get_grid_forecast(self, center_lat: float, center_lon: float, radius_km: float = 25, resolution_km: float = 5) -> ForecastGrid:
        """Fetch forecasts for a grid of points around a center location."""
        lat_step = resolution_km / 111.0
        grid_points = []
        num_steps = int(radius_km / resolution_km)
        
        for i in range(-num_steps, num_steps + 1):
            for j in range(-num_steps, num_steps + 1):
                lat = center_lat + (i * lat_step)
                lon_step = resolution_km / (111.0 * math.cos(math.radians(max(abs(lat), 0.01))))
                lon = center_lon + (j * lon_step)
                distance = math.sqrt((i * resolution_km)**2 + (j * resolution_km)**2)
                if distance <= radius_km:
                    grid_points.append((lat, lon))
        
        logger.info(f"Fetching grid forecast for {len(grid_points)} points around ({center_lat:.4f}, {center_lon:.4f})")
        
        tasks = [self.get_forecast(lat, lon, days=3) for lat, lon in grid_points]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_points = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Grid point fetch error: {result}")
            else:
                valid_points.append(result)
                
        return ForecastGrid(
            center_latitude=center_lat,
            center_longitude=center_lon,
            points=valid_points
        )

    async def close(self):
        """Close the internal HTTP client."""
        await self.client.aclose()
