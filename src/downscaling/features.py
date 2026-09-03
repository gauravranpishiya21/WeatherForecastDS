"""
Feature engineering pipeline for weather downscaling.
"""
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from pydantic import BaseModel, Field
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

class DownscalingFeatures(BaseModel):
    """Pydantic model for downscaling features."""
    lat: float
    lon: float
    elevation: float
    slope: float
    aspect: float
    distance_to_coast: float
    elevation_difference: float
    coarse_temp: float
    coarse_precip: float
    coarse_humidity: float
    coarse_wind: float
    day_of_year_sin: float
    day_of_year_cos: float
    is_monsoon: int

class FeatureEngineering:
    """Feature engineering pipeline for downscaling models."""
    
    @staticmethod
    def _cyclical_encoding(day_of_year: int) -> tuple[float, float]:
        """Encode day of year as a cyclical feature."""
        # 365.25 for leap years
        sin_val = math.sin(2 * math.pi * day_of_year / 365.25)
        cos_val = math.cos(2 * math.pi * day_of_year / 365.25)
        return sin_val, cos_val

    def build_features(self, lat: float, lon: float, elevation: float, 
                       terrain_info: Dict[str, float], coarse_forecast: Dict[str, Any], 
                       day_of_year: int) -> DownscalingFeatures:
        """
        Build a feature vector for a single point.
        """
        try:
            day_sin, day_cos = self._cyclical_encoding(day_of_year)
            is_monsoon = 1 if 152 <= day_of_year <= 273 else 0
            elevation_diff = elevation - terrain_info.get('mean_coarse_elevation', elevation)
            
            features = DownscalingFeatures(
                lat=lat,
                lon=lon,
                elevation=elevation,
                slope=terrain_info.get('slope', 0.0),
                aspect=terrain_info.get('aspect', 0.0),
                distance_to_coast=terrain_info.get('distance_to_coast', 1000.0),
                elevation_difference=elevation_diff,
                coarse_temp=coarse_forecast.get('temp', 0.0),
                coarse_precip=coarse_forecast.get('precip', 0.0),
                coarse_humidity=coarse_forecast.get('humidity', 0.0),
                coarse_wind=coarse_forecast.get('wind', 0.0),
                day_of_year_sin=day_sin,
                day_of_year_cos=day_cos,
                is_monsoon=is_monsoon
            )
            return features
        except Exception as e:
            logger.error(f"Error building features: {e}")
            raise

    def build_feature_matrix(self, grid_points: List[Dict[str, Any]], coarse_forecast: Dict[str, Any], day_of_year: int) -> pd.DataFrame:
        """
        Build a DataFrame of features for multiple grid points.
        """
        feature_list = []
        for point in grid_points:
            features = self.build_features(
                lat=point['lat'],
                lon=point['lon'],
                elevation=point['elevation'],
                terrain_info=point.get('terrain_info', {}),
                coarse_forecast=coarse_forecast,
                day_of_year=day_of_year
            )
            feature_list.append(features.model_dump())
            
        return pd.DataFrame(feature_list)
