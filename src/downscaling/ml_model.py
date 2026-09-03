"""
ML-based downscaling model predicting residuals over baseline interpolation.
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
from typing import Dict, Any, Tuple
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

from src.downscaling.features import FeatureEngineering
from src.downscaling.interpolation import StatisticalDownscaler

class MLDownscaler:
    """Machine learning model for predicting high-resolution downscaling residuals."""
    
    def __init__(self, model_type: str = 'xgboost'):
        self.model_type = model_type
        self.models = {
            'temp': XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5) if model_type == 'xgboost' else RandomForestRegressor(n_estimators=100, max_depth=10),
            'precip': XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5) if model_type == 'xgboost' else RandomForestRegressor(n_estimators=100, max_depth=10),
            'humidity': XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5) if model_type == 'xgboost' else RandomForestRegressor(n_estimators=100, max_depth=10),
            'wind': XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5) if model_type == 'xgboost' else RandomForestRegressor(n_estimators=100, max_depth=10)
        }
        self.feature_engineering = FeatureEngineering()
        self.statistical = StatisticalDownscaler()
        self.is_trained = False
        self.feature_cols = [
            'lat', 'lon', 'elevation', 'slope', 'aspect', 'distance_to_coast', 
            'elevation_difference', 'coarse_temp', 'coarse_precip', 'coarse_humidity', 
            'coarse_wind', 'day_of_year_sin', 'day_of_year_cos', 'is_monsoon'
        ]

    def train(self, training_data: pd.DataFrame) -> None:
        logger.info(f"Training {self.model_type} downscaling models...")
        X = training_data[self.feature_cols]
        
        for var in ['temp', 'precip', 'humidity', 'wind']:
            target_col = f'res_{var}'
            if target_col in training_data.columns:
                logger.info(f"Training {var} model...")
                y = training_data[target_col]
                self.models[var].fit(X, y)
            else:
                logger.warning(f"Target {target_col} not found in training data.")
                
        self.is_trained = True
        logger.info("Training complete.")

    def predict(self, features: pd.DataFrame) -> Dict[str, np.ndarray]:
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
            
        X = features[self.feature_cols]
        predictions = {}
        
        for var in ['temp', 'precip', 'humidity', 'wind']:
            predictions[var] = self.models[var].predict(X)
            
        return predictions

    def downscale(self, coarse_forecast_grid: Dict[str, np.ndarray], 
                  grid_lats: np.ndarray, grid_lons: np.ndarray,
                  target_points: pd.DataFrame, day_of_year: int) -> pd.DataFrame:
        if not self.is_trained:
            logger.warning("ML model not trained. Falling back to statistical downscaling.")
            
        mean_coarse_elev = 500.0  # Placeholder
        
        points_list = []
        for _, row in target_points.iterrows():
            point = {
                'lat': row['lat'],
                'lon': row['lon'],
                'elevation': row['elevation'],
                'terrain_info': {
                    'slope': row.get('slope', 0),
                    'aspect': row.get('aspect', 0),
                    'distance_to_coast': row.get('distance_to_coast', 1000),
                    'mean_coarse_elevation': mean_coarse_elev
                }
            }
            points_list.append(point)
            
        stat_forecasts = self.statistical.downscale(
            coarse_forecast_grid, grid_lats, grid_lons, points_list, mean_coarse_elev
        )
        
        results = []
        for i, stat in enumerate(stat_forecasts):
            results.append({
                'lat': stat.lat, 'lon': stat.lon, 'elevation': stat.elevation,
                'temp_baseline': stat.temperature,
                'precip_baseline': stat.precipitation,
                'humidity_baseline': stat.humidity,
                'wind_baseline': stat.wind_speed
            })
            
        df_results = pd.DataFrame(results)
        
        if not self.is_trained:
            return df_results.rename(columns={
                'temp_baseline': 'temp_final', 'precip_baseline': 'precip_final',
                'humidity_baseline': 'humidity_final', 'wind_baseline': 'wind_final'
            })
            
        coarse_single = {k: np.mean(v) for k, v in coarse_forecast_grid.items()} 
        
        features_df = self.feature_engineering.build_feature_matrix(
            points_list, coarse_single, day_of_year
        )
        
        residuals = self.predict(features_df)
        
        df_results['temp_final'] = df_results['temp_baseline'] + residuals['temp']
        df_results['precip_final'] = np.maximum(0, df_results['precip_baseline'] + residuals['precip'])
        df_results['humidity_final'] = np.clip(df_results['humidity_baseline'] + residuals['humidity'], 0, 100)
        df_results['wind_final'] = np.maximum(0, df_results['wind_baseline'] + residuals['wind'])
        
        return df_results

    def save_model(self, path: str) -> None:
        if not self.is_trained:
            logger.warning("Cannot save an untrained model.")
            return
            
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.models, save_path)
        logger.info(f"Model saved to {save_path}")

    def load_model(self, path: str) -> None:
        load_path = Path(path)
        if not load_path.exists():
            raise FileNotFoundError(f"Model file {load_path} not found.")
            
        self.models = joblib.load(load_path)
        self.is_trained = True
        logger.info(f"Model loaded from {load_path}")
        
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
            
        X = test_data[self.feature_cols]
        metrics = {}
        
        for var in ['temp', 'precip', 'humidity', 'wind']:
            target_col = f'res_{var}'
            if target_col in test_data.columns:
                y_true = test_data[target_col]
                y_pred = self.models[var].predict(X)
                
                metrics[var] = {
                    'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                    'mae': float(mean_absolute_error(y_true, y_pred)),
                    'r2': float(r2_score(y_true, y_pred))
                }
                
        return metrics

def generate_synthetic_training_data(n_samples: int = 5000) -> pd.DataFrame:
    np.random.seed(42)
    logger.info(f"Generating {n_samples} synthetic training samples...")
    
    lats = np.random.uniform(8.0, 37.0, n_samples)
    lons = np.random.uniform(68.0, 97.0, n_samples)
    
    elevations = np.random.exponential(scale=500, size=n_samples)
    elevations = np.clip(elevations, 0, 4000)
    
    slopes = np.random.uniform(0, 45, n_samples)
    aspects = np.random.uniform(0, 360, n_samples)
    distance_to_coast = np.random.uniform(0, 1000, n_samples)
    
    elevation_diffs = np.random.normal(0, 200, n_samples) 
    
    coarse_temp = 35 - (lats - 8) * 0.5 - (elevations / 1000) * 6.5 + np.random.normal(0, 2, n_samples)
    coarse_precip = np.random.exponential(scale=5, size=n_samples)
    coarse_humidity = np.clip(np.random.normal(60, 15, n_samples), 10, 100)
    coarse_wind = np.clip(np.random.normal(10, 5, n_samples), 0, 30)
    
    days = np.random.randint(1, 366, n_samples)
    day_sin = np.sin(2 * np.pi * days / 365.25)
    day_cos = np.cos(2 * np.pi * days / 365.25)
    
    is_monsoon = np.where((days >= 152) & (days <= 273), 1, 0)
    
    df = pd.DataFrame({
        'lat': lats,
        'lon': lons,
        'elevation': elevations,
        'slope': slopes,
        'aspect': aspects,
        'distance_to_coast': distance_to_coast,
        'elevation_difference': elevation_diffs,
        'coarse_temp': coarse_temp,
        'coarse_precip': coarse_precip,
        'coarse_humidity': coarse_humidity,
        'coarse_wind': coarse_wind,
        'day_of_year_sin': day_sin,
        'day_of_year_cos': day_cos,
        'is_monsoon': is_monsoon
    })
    
    df['res_temp'] = -0.5 * (df['elevation_difference'] / 100) + 0.1 * np.sin(np.radians(df['aspect'])) * df['slope'] + np.random.normal(0, 0.5, n_samples)
    df['res_precip'] = df['slope'] * 0.2 + (df['is_monsoon'] * df['elevation'] * 0.001) + np.random.normal(0, 1.0, n_samples)
    df['res_humidity'] = -0.5 * df['res_temp'] + np.random.normal(0, 2.0, n_samples)
    df['res_wind'] = 0.5 * (df['elevation_difference'] / 100) + np.random.normal(0, 1.0, n_samples)
    
    logger.info("Synthetic data generation complete.")
    return df
