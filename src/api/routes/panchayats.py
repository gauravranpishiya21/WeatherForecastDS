"""Block-level panchayat endpoints for the SIH demo.

Any block (Phanda, Berasia, ...) -> all its panchayat villages, each with
downscaled weather + risk level. Only 2 upstream API calls per request:
one coarse forecast at the block center + one batch elevation call.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from pydantic import BaseModel

from src.data.panchayats import PanchayatService, PanchayatVillage
from src.data.weather_api import OpenMeteoClient
from src.data.terrain import TerrainDataProvider
from src.downscaling.interpolation import StatisticalDownscaler
from src.advisory.risk_assessment import WeatherRiskAssessor

router = APIRouter(prefix="/api/panchayats", tags=["panchayats"])

_service = PanchayatService()
_stat = StatisticalDownscaler()
_risk = WeatherRiskAssessor()
_REF_ELEV = 500.0  # reference elevation for lapse-rate correction


class VillageToday(BaseModel):
    temp_max: float
    temp_min: float
    rainfall_mm: float
    humidity: float
    wind_kmh: float
    weather_desc: str = ""


class VillageRisk(BaseModel):
    level: str  # Low | Moderate | High | Critical
    color: str  # green | yellow | orange | red
    top_risk: str = "None"
    severity: int = 0


class VillageSummary(BaseModel):
    id: str
    name: str
    hindi_name: str = ""
    lat: float
    lon: float
    elevation_m: float
    population: Optional[int] = None
    main_crops: List[str] = []
    geocoded: bool = False
    today: VillageToday
    risk: VillageRisk


class BlockOverview(BaseModel):
    block: str
    district: str
    state: str
    center_lat: float
    center_lon: float
    total_panchayats: int
    date: str
    villages: List[VillageSummary]


class VillageDay(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    rainfall_mm: float
    humidity: float
    wind_kmh: float
    weather_desc: str = ""


class VillageDetail(BaseModel):
    id: str
    name: str
    hindi_name: str = ""
    lat: float
    lon: float
    elevation_m: float
    population: Optional[int] = None
    main_crops: List[str] = []
    forecast: List[VillageDay]
    risks: List[dict]


def _downscale_day(day, elevation_m: float) -> dict:
    """Apply statistical downscaling for one coarse day at one elevation."""
    elev_diff = elevation_m - _REF_ELEV
    return {
        "date": day.date,
        "temperature": round(_stat.apply_lapse_rate(day.temperature_2m_max, elev_diff), 1),
        "temp_min": round(_stat.apply_lapse_rate(day.temperature_2m_min, elev_diff), 1),
        "rainfall": round(max(0.0, _stat.apply_precipitation_correction(
            day.precipitation_sum, elevation_m, _REF_ELEV)), 1),
        "humidity": round(max(0.0, min(100.0, day.relative_humidity_2m_mean)), 1),
        "wind_speed": round(max(0.0, _stat.apply_wind_correction(
            day.wind_speed_10m_max, elev_diff)), 1),
        "weather_code": day.weathercode,
        "weather_desc": day.weather_description or "Unknown",
    }


def _risk_summary(daily: List[dict]) -> VillageRisk:
    risks = _risk.assess_risks(daily)
    if not risks:
        return VillageRisk(level="Low", color="green")
    score = _risk.aggregate_risk_score(risks)
    color = _risk.get_risk_color(score)
    level = {"GREEN": "Low", "YELLOW": "Moderate", "ORANGE": "High", "RED": "Critical"}[color]
    top = max(risks, key=lambda r: r.severity)
    return VillageRisk(level=level, color=color.lower(), top_risk=top.risk_type, severity=top.severity)


@router.get("/blocks")
async def list_blocks():
    """List all available demo blocks."""
    return [b.model_dump() for b in _service.list_blocks()]


@router.get("", response_model=BlockOverview)
async def block_overview(block_id: str = Query("phanda", description="Block id, e.g. phanda, berasia")):
    """Return a whole block: every panchayat with today's downscaled
    weather + weekly risk level. Powers the block map + table."""
    try:
        info = _service.get_block_info(block_id)
        villages = _service.list_villages(block_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    logger.info(f"Block overview request: {info.block} ({len(villages)} panchayats)")

    weather = OpenMeteoClient()
    terrain = TerrainDataProvider()
    try:
        coarse = await weather.get_forecast(info.center_lat, info.center_lon, days=7)
        if not coarse.daily:
            raise HTTPException(status_code=504, detail="Upstream weather API returned no data")
        elevs = await terrain.get_elevations_batch(
            [v.lat for v in villages], [v.lon for v in villages]
        )
    finally:
        await weather.close()
        await terrain.close()

    out: List[VillageSummary] = []
    for v, elev in zip(villages, elevs):
        elevation = round(elev if elev else (v.elevation_m or 0.0), 1)
        daily = [_downscale_day(d, elevation) for d in coarse.daily]
        today = daily[0]
        risk = _risk_summary(daily)
        out.append(VillageSummary(
            id=v.id, name=v.name, hindi_name=v.hindi_name,
            lat=v.lat, lon=v.lon, elevation_m=elevation,
            population=v.population, main_crops=v.main_crops,
            geocoded=v.geocoded,
            today=VillageToday(
                temp_max=today["temperature"], temp_min=today["temp_min"],
                rainfall_mm=today["rainfall"], humidity=today["humidity"],
                wind_kmh=today["wind_speed"], weather_desc=today["weather_desc"],
            ),
            risk=risk,
        ))

    return BlockOverview(
        block=info.block, district=info.district, state=info.state,
        center_lat=info.center_lat, center_lon=info.center_lon,
        total_panchayats=info.total_panchayats,
        date=coarse.daily[0].date, villages=out,
    )


@router.get("/{village_id}", response_model=VillageDetail)
async def village_detail(village_id: str,
                         block_id: str = Query("phanda", description="Block id, e.g. phanda, berasia")):
    """7-day downscaled forecast + risk list for one panchayat."""
    try:
        v: Optional[PanchayatVillage] = _service.get_village(village_id, block_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if v is None:
        raise HTTPException(status_code=404, detail=f"Village '{village_id}' not found in block '{block_id}'")

    weather = OpenMeteoClient()
    terrain = TerrainDataProvider()
    try:
        coarse = await weather.get_forecast(v.lat, v.lon, days=7)
        if not coarse.daily:
            raise HTTPException(status_code=504, detail="Upstream weather API returned no data")
        elev = await terrain.get_elevation(v.lat, v.lon)
    finally:
        await weather.close()
        await terrain.close()

    elevation = round(elev if elev else (v.elevation_m or 0.0), 1)
    daily = [_downscale_day(d, elevation) for d in coarse.daily]
    risks = _risk.assess_risks(daily)

    return VillageDetail(
        id=v.id, name=v.name, hindi_name=v.hindi_name,
        lat=v.lat, lon=v.lon, elevation_m=elevation,
        population=v.population, main_crops=v.main_crops,
        forecast=[VillageDay(
            date=d["date"], temp_max=d["temperature"], temp_min=d["temp_min"],
            rainfall_mm=d["rainfall"], humidity=d["humidity"],
            wind_kmh=d["wind_speed"], weather_desc=d["weather_desc"],
        ) for d in daily],
        risks=[{
            "type": r.risk_type, "severity": r.severity,
            "description": r.description, "actions": r.recommended_actions,
        } for r in risks],
    )
