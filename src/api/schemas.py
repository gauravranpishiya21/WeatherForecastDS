"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class LocationInfo(BaseModel):
    lat: float
    lon: float
    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    panchayat: Optional[str] = None
    elevation: Optional[float] = None


class LocationRequest(BaseModel):
    lat: float
    lon: float
    crop: Optional[str] = None
    sowing_date: Optional[str] = None


class DailyForecast(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    rainfall_mm: float
    humidity: float
    wind_kmh: float
    weather_code: int = 0
    weather_desc: str = "Unknown"


class ForecastResponse(BaseModel):
    location: LocationInfo
    coarse_forecast: List[DailyForecast]
    downscaled_forecast: List[DailyForecast]
    improvement_metrics: Dict[str, Any]


class AdvisoryRequest(BaseModel):
    lat: float
    lon: float
    crop: str
    sowing_date: str
    language: str = 'en'


class RiskInfo(BaseModel):
    type: str
    severity: str
    color: str
    description: str
    actions: List[str]


class DailyAction(BaseModel):
    date: str
    action: str
    priority: str


class AdvisoryResponse(BaseModel):
    location: LocationInfo
    crop: str
    growth_stage: str
    risks: List[RiskInfo]
    advisory: str
    weekly_plan: List[DailyAction]
    sms_advisory: str


class Alert(BaseModel):
    type: str
    severity: str
    message: str
    valid_from: str
    valid_to: str


class AlertResponse(BaseModel):
    alerts: List[Alert]
