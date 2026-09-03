"""Advisory API endpoint - real pipeline connecting weather data to agro-advisories."""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

from src.api.schemas import (
    AdvisoryRequest, AdvisoryResponse, LocationInfo,
    RiskInfo, DailyAction,
)
from src.data.weather_api import OpenMeteoClient
from src.data.terrain import TerrainDataProvider
from src.data.geocoding import GeocodingService
from src.downscaling.interpolation import StatisticalDownscaler
from src.advisory.crop_rules import CropAdvisoryEngine
from src.advisory.risk_assessment import WeatherRiskAssessor
from src.advisory.llm_advisory import LLMAdvisoryGenerator
from src.utils.config import get_settings

router = APIRouter(prefix="/api/advisory", tags=["advisory"])

# Lazy-initialized singletons
_crop_engine: Optional[CropAdvisoryEngine] = None
_risk_assessor: Optional[WeatherRiskAssessor] = None
_llm_generator: Optional[LLMAdvisoryGenerator] = None


def _get_crop_engine() -> CropAdvisoryEngine:
    global _crop_engine
    if _crop_engine is None:
        _crop_engine = CropAdvisoryEngine()
    return _crop_engine


def _get_risk_assessor() -> WeatherRiskAssessor:
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = WeatherRiskAssessor()
    return _risk_assessor


def _get_llm_generator() -> LLMAdvisoryGenerator:
    global _llm_generator
    if _llm_generator is None:
        settings = get_settings()
        _llm_generator = LLMAdvisoryGenerator(
            api_key=settings.gemini_api_key or None,
            model_name=settings.gemini_model,
        )
    return _llm_generator


@router.post("", response_model=AdvisoryResponse)
async def get_advisory(request: AdvisoryRequest):
    """Generate crop-specific agro-meteorological advisory.

    Pipeline:
    1. Fetch weather forecast for the location
    2. Apply downscaling (statistical + ML)
    3. Run crop-specific rule engine
    4. Assess weather risks
    5. Generate natural language advisory via LLM (or template fallback)
    6. Translate to requested language
    """
    logger.info(f"Advisory request: lat={request.lat}, lon={request.lon}, crop={request.crop}, lang={request.language}")

    try:
        # Step 1: Fetch weather forecast
        weather_client = OpenMeteoClient()
        try:
            coarse_point = await weather_client.get_forecast(request.lat, request.lon, days=7)
        finally:
            await weather_client.close()

        if not coarse_point.daily:
            raise HTTPException(status_code=504, detail="Upstream weather API returned no data")

        # Step 2: Get terrain for downscaling
        terrain_provider = TerrainDataProvider()
        try:
            terrain = await terrain_provider.get_terrain_features(request.lat, request.lon)
        finally:
            await terrain_provider.close()

        # Step 3: Apply downscaling to get accurate forecasts
        stat = StatisticalDownscaler()
        elev_diff = terrain.elevation - 500.0
        daily_forecasts = []
        for day in coarse_point.daily:
            daily_forecasts.append({
                "date": day.date,
                "temperature": round(stat.apply_lapse_rate(day.temperature_2m_max, elev_diff), 1),
                "temp_min": round(stat.apply_lapse_rate(day.temperature_2m_min, elev_diff), 1),
                "rainfall": round(max(0, stat.apply_precipitation_correction(day.precipitation_sum, terrain.elevation, 500.0)), 1),
                "humidity": round(max(0, min(100, day.relative_humidity_2m_mean)), 1),
                "wind_speed": round(max(0, stat.apply_wind_correction(day.wind_speed_10m_max, elev_diff)), 1),
                "weather_code": day.weathercode,
            })

        # Step 4: Get location info
        geocoding = GeocodingService()
        try:
            location_info = await geocoding.reverse_geocode(request.lat, request.lon)
            location_str = f"{request.lat:.4f}, {request.lon:.4f}"
            if location_info.panchayat:
                location_str = f"{location_info.panchayat}, {location_info.block or ''}, {location_info.district or ''}"
        except Exception:
            location_info = None
            location_str = f"{request.lat:.4f}, {request.lon:.4f}"
        finally:
            await geocoding.close()

        # Step 5: Run crop advisory engine
        crop_engine = _get_crop_engine()
        try:
            sowing_date = datetime.strptime(request.sowing_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # Default: assume sowing was 30 days ago
            sowing_date = (datetime.now() - timedelta(days=30)).date()

        growth_stage = crop_engine.determine_growth_stage(request.crop, sowing_date)
        if growth_stage is None:
            # Fallback: use first growth stage
            crop_info = crop_engine.get_crop_info(request.crop)
            if crop_info and crop_info.growth_stages:
                growth_stage = crop_info.growth_stages[0]
            else:
                raise HTTPException(status_code=400, detail=f"Crop '{request.crop}' not found in knowledge base")

        # Use first day's forecast for immediate advisory
        today_weather = daily_forecasts[0] if daily_forecasts else {}
        crop_advisory = crop_engine.generate_advisory(
            request.crop, growth_stage, today_weather
        )

        # Step 6: Assess weather risks
        risk_assessor = _get_risk_assessor()
        weather_risks = risk_assessor.assess_risks(daily_forecasts)
        risk_score = risk_assessor.aggregate_risk_score(weather_risks)
        risk_color = risk_assessor.get_risk_color(risk_score)

        # Step 7: Generate natural language advisory via LLM
        llm = _get_llm_generator()
        llm_response = llm.generate_advisory(
            crop_advisory=crop_advisory,
            weather_risks=weather_risks,
            location_info=location_str,
            language=request.language,
        )

        # Step 8: Build weekly action plan
        weekly_plan = []
        for day_forecast in daily_forecasts[:7]:
            day_advisory = crop_engine.generate_advisory(request.crop, growth_stage, day_forecast)
            priority = "High" if day_advisory.risk_level in ("HIGH", "CRITICAL") else "Medium" if day_advisory.risk_level == "MODERATE" else "Low"
            action_summary = "; ".join([a.advice[:50] for a in day_advisory.action_items[:2]])
            weekly_plan.append(DailyAction(
                date=day_forecast["date"],
                action=action_summary or "Continue routine practices",
                priority=priority,
            ))

        # Step 9: Format risk info
        risk_infos = []
        for risk in weather_risks:
            severity_str = "Critical" if risk.severity >= 80 else "High" if risk.severity >= 60 else "Moderate" if risk.severity >= 30 else "Low"
            risk_color_map = {"Critical": "red", "High": "orange", "Moderate": "yellow", "Low": "green"}
            risk_infos.append(RiskInfo(
                type=risk.risk_type,
                severity=severity_str,
                color=risk_color_map.get(severity_str, "gray"),
                description=risk.description,
                actions=risk.recommended_actions,
            ))

        location = LocationInfo(
            lat=request.lat, lon=request.lon,
            elevation=round(terrain.elevation, 1),
            state=location_info.state if location_info else None,
            district=location_info.district if location_info else None,
            block=location_info.block if location_info else None,
            panchayat=location_info.panchayat if location_info else None,
        )

        return AdvisoryResponse(
            location=location,
            crop=request.crop,
            growth_stage=growth_stage.name,
            risks=risk_infos,
            advisory=llm_response.advisory_text,
            weekly_plan=weekly_plan,
            sms_advisory=llm_response.sms_version,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advisory pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Advisory generation failed: {str(e)}")
