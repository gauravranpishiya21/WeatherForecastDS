"""
Statistical baseline downscaling using interpolation and physical corrections.
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from loguru import logger
import numpy as np

class DownscaledForecast(BaseModel):
    """Pydantic model for downscaled forecast data."""
    lat: float
    lon: float
    elevation: float
    temperature: float
    precipitation: float
    humidity: float
    wind_speed: float

class StatisticalDownscaler:
    """Statistical downscaler using bilinear interpolation and physical principles."""
    
    @staticmethod
    def bilinear_interpolate(coarse_grid: np.ndarray, target_lat: float, target_lon: float, 
                             grid_lats: np.ndarray, grid_lons: np.ndarray) -> float:
        try:
            lats = grid_lats.flatten()
            lons = grid_lons.flatten()
            vals = coarse_grid.flatten()
            
            distances = np.sqrt((lats - target_lat)**2 + (lons - target_lon)**2)
            
            if np.min(distances) < 1e-6:
                return float(vals[np.argmin(distances)])
                
            weights = 1.0 / distances
            interpolated = np.sum(weights * vals) / np.sum(weights)
            return float(interpolated)
        except Exception as e:
            logger.error(f"Error in interpolation: {e}")
            return float(np.mean(coarse_grid))

    @staticmethod
    def apply_lapse_rate(temperature: float, elevation_diff: float, lapse_rate: float = -6.5) -> float:
        correction = (elevation_diff / 1000.0) * lapse_rate
        return temperature + correction

    @staticmethod
    def apply_precipitation_correction(precip: float, elevation: float, reference_elevation: float) -> float:
        elevation_diff = max(0, elevation - reference_elevation)
        enhancement_factor = min(0.5, (elevation_diff / 100.0) * 0.05)
        return max(0.0, precip * (1.0 + enhancement_factor))
        
    @staticmethod
    def apply_wind_correction(wind: float, elevation_diff: float) -> float:
        if elevation_diff > 0:
            factor = min(2.0, 1.0 + (elevation_diff / 100.0) * 0.1)
        else:
            factor = max(0.5, 1.0 + (elevation_diff / 100.0) * 0.05)
        return wind * factor

    def downscale(self, coarse_forecast_grid: Dict[str, np.ndarray], 
                  grid_lats: np.ndarray, grid_lons: np.ndarray, 
                  target_points: List[Dict[str, Any]],
                  mean_coarse_elev: float) -> List[DownscaledForecast]:
        results = []
        try:
            for point in target_points:
                t_lat = point['lat']
                t_lon = point['lon']
                t_elev = point['elevation']
                
                interp_temp = self.bilinear_interpolate(coarse_forecast_grid.get('temp', np.zeros_like(grid_lats)), t_lat, t_lon, grid_lats, grid_lons)
                interp_precip = self.bilinear_interpolate(coarse_forecast_grid.get('precip', np.zeros_like(grid_lats)), t_lat, t_lon, grid_lats, grid_lons)
                interp_humidity = self.bilinear_interpolate(coarse_forecast_grid.get('humidity', np.zeros_like(grid_lats)), t_lat, t_lon, grid_lats, grid_lons)
                interp_wind = self.bilinear_interpolate(coarse_forecast_grid.get('wind', np.zeros_like(grid_lats)), t_lat, t_lon, grid_lats, grid_lons)
                
                elev_diff = t_elev - mean_coarse_elev
                final_temp = self.apply_lapse_rate(interp_temp, elev_diff)
                final_precip = self.apply_precipitation_correction(interp_precip, t_elev, mean_coarse_elev)
                final_wind = self.apply_wind_correction(interp_wind, elev_diff)
                
                final_humidity = max(0.0, min(100.0, interp_humidity))
                
                forecast = DownscaledForecast(
                    lat=t_lat,
                    lon=t_lon,
                    elevation=t_elev,
                    temperature=final_temp,
                    precipitation=final_precip,
                    humidity=final_humidity,
                    wind_speed=final_wind
                )
                results.append(forecast)
                
            return results
        except Exception as e:
            logger.error(f"Error during statistical downscaling: {e}")
            raise
