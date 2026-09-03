import json
import os
from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

class PestCondition(BaseModel):
    pest_name: str
    temp_min: float
    temp_max: float
    humidity_min: float

class GrowthStage(BaseModel):
    name: str
    duration_days: int
    optimal_temp_min: float
    optimal_temp_max: float
    critical_temp_min: float
    critical_temp_max: float
    optimal_rainfall_mm_per_week: float
    max_rainfall_mm_per_day: float
    optimal_humidity_min: float
    optimal_humidity_max: float
    wind_damage_threshold_kmh: float

class CropInfo(BaseModel):
    name: str
    hindi_name: str
    scientific_name: str
    seasons: List[str]
    irrigation_sensitivity: str
    growth_stages: List[GrowthStage]
    pest_conditions: List[PestCondition]

class ActionItem(BaseModel):
    category: str
    advice: str

class CropAdvisory(BaseModel):
    crop_name: str
    growth_stage: str
    risk_level: str
    action_items: List[ActionItem]

class CropAdvisoryEngine:
    """Rule-based engine for generating crop advisories based on weather data."""
    def __init__(self, data_path: str = None):
        self.crops_data: Dict[str, CropInfo] = {}
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), "crop_data", "crops.json")
        self.data_path = data_path
        self.load_crops()

    def load_crops(self) -> None:
        """Load crop knowledge base from JSON file."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    self.crops_data[item["name"].lower()] = CropInfo(**item)
            logger.info(f"Loaded {len(self.crops_data)} crops from knowledge base.")
        except Exception as e:
            logger.error(f"Failed to load crops data: {e}")
            raise

    def get_crop_info(self, crop_name: str) -> Optional[CropInfo]:
        """Get crop information by name."""
        return self.crops_data.get(crop_name.lower())

    def determine_growth_stage(self, crop_name: str, sowing_date: date) -> Optional[GrowthStage]:
        """Determine current growth stage based on sowing date."""
        crop_info = self.get_crop_info(crop_name)
        if not crop_info:
            return None
        
        days_since_sowing = (date.today() - sowing_date).days
        if days_since_sowing < 0:
            return None
            
        accumulated_days = 0
        for stage in crop_info.growth_stages:
            accumulated_days += stage.duration_days
            if days_since_sowing <= accumulated_days:
                return stage
        
        # If past all stages, return the last one (e.g. maturity/harvest)
        return crop_info.growth_stages[-1] if crop_info.growth_stages else None

    def generate_advisory(self, crop_name: str, growth_stage: GrowthStage, weather_forecast: Dict[str, Any]) -> CropAdvisory:
        """Generate advisory based on growth stage thresholds and weather forecast."""
        crop_info = self.get_crop_info(crop_name)
        if not crop_info:
            raise ValueError(f"Crop {crop_name} not found.")

        temp = weather_forecast.get("temperature", 25)
        humidity = weather_forecast.get("humidity", 60)
        rainfall = weather_forecast.get("rainfall", 0)
        wind_speed = weather_forecast.get("wind_speed", 10)

        risk_level = "LOW"
        action_items = []

        # Temperature checks
        if temp > growth_stage.critical_temp_max:
            risk_level = "CRITICAL"
            action_items.append(ActionItem(category="Temperature", advice="Critical heat stress. Ensure adequate irrigation to cool the crop."))
        elif temp < growth_stage.critical_temp_min:
            risk_level = "CRITICAL"
            action_items.append(ActionItem(category="Temperature", advice="Critical cold/frost risk. Consider protective measures like light irrigation or covering."))
        elif temp > growth_stage.optimal_temp_max or temp < growth_stage.optimal_temp_min:
            if risk_level == "LOW": risk_level = "MODERATE"
            action_items.append(ActionItem(category="Temperature", advice="Sub-optimal temperatures observed. Monitor crop health."))

        # Rainfall checks
        if rainfall > growth_stage.max_rainfall_mm_per_day:
            risk_level = "HIGH"
            action_items.append(ActionItem(category="Irrigation", advice="Heavy rainfall expected. Delay irrigation and ensure proper field drainage."))
        elif rainfall < (growth_stage.optimal_rainfall_mm_per_week / 7):
            if risk_level == "LOW": risk_level = "MODERATE"
            action_items.append(ActionItem(category="Irrigation", advice="Low rainfall. Schedule irrigation according to soil moisture."))
        else:
            action_items.append(ActionItem(category="Irrigation", advice="Optimal rainfall. Skip irrigation if soil moisture is sufficient."))

        # Wind checks
        if wind_speed > growth_stage.wind_damage_threshold_kmh:
            risk_level = max(risk_level, "HIGH")
            action_items.append(ActionItem(category="Protection", advice="Strong winds expected. Avoid spraying and provide support to tall crops if applicable."))

        # Pest checks
        for pest in crop_info.pest_conditions:
            if pest.temp_min <= temp <= pest.temp_max and humidity >= pest.humidity_min:
                risk_level = max(risk_level, "HIGH")
                action_items.append(ActionItem(category="Pest", advice=f"Favorable conditions for {pest.pest_name}. Monitor field and prepare preventive sprays."))

        if not action_items:
            action_items.append(ActionItem(category="General", advice="Weather is optimal for current growth stage. Continue routine practices."))

        return CropAdvisory(
            crop_name=crop_info.name,
            growth_stage=growth_stage.name,
            risk_level=risk_level,
            action_items=action_items
        )

    def get_weekly_plan(self, crop_name: str, growth_stage: GrowthStage, weekly_forecast: List[Dict[str, Any]]) -> List[CropAdvisory]:
        """Generate a 7-day action plan based on weekly forecast."""
        plan = []
        for daily_forecast in weekly_forecast[:7]:
            plan.append(self.generate_advisory(crop_name, growth_stage, daily_forecast))
        return plan
