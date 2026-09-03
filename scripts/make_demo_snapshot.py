"""Generate offline demo snapshots for live SIH demos (one file per block).

Runs the REAL pipeline once per block (Open-Meteo forecast + batch
elevations + statistical downscaling + risk assessment) and saves to
src/data/demo_<block_id>.json.

The dashboard's Demo mode reads these files, so the live demo works
even with no internet on stage.

Usage: python scripts/make_demo_snapshot.py [--block phanda]
"""
import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.panchayats import PanchayatService
from src.data.weather_api import OpenMeteoClient
from src.data.terrain import TerrainDataProvider
from src.downscaling.interpolation import StatisticalDownscaler
from src.advisory.risk_assessment import WeatherRiskAssessor

REF_ELEV = 500.0
DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"


async def build_block(block_id: str) -> None:
    svc = PanchayatService()
    info = svc.get_block_info(block_id)
    villages = svc.list_villages(block_id)
    stat = StatisticalDownscaler()
    risk = WeatherRiskAssessor()

    weather = OpenMeteoClient()
    terrain = TerrainDataProvider()
    try:
        coarse = await weather.get_forecast(info.center_lat, info.center_lon, days=7)
        elevs = await terrain.get_elevations_batch(
            [v.lat for v in villages], [v.lon for v in villages]
        )
    finally:
        await weather.close()
        await terrain.close()

    if not coarse.daily:
        raise RuntimeError(f"Upstream weather API returned no data for {block_id}")

    coarse_days = [{
        "date": d.date,
        "temp_max": d.temperature_2m_max,
        "temp_min": d.temperature_2m_min,
        "rainfall_mm": d.precipitation_sum,
        "humidity": d.relative_humidity_2m_mean,
        "wind_kmh": d.wind_speed_10m_max,
        "weather_code": d.weathercode,
        "weather_desc": d.weather_description or "Unknown",
    } for d in coarse.daily]

    out_villages = []
    for v, elev in zip(villages, elevs):
        elevation = round(elev if elev else (v.elevation_m or 0.0), 1)
        diff = elevation - REF_ELEV
        daily = [{
            "date": d.date,
            "temp_max": round(stat.apply_lapse_rate(d.temperature_2m_max, diff), 1),
            "temp_min": round(stat.apply_lapse_rate(d.temperature_2m_min, diff), 1),
            "rainfall_mm": round(max(0.0, stat.apply_precipitation_correction(
                d.precipitation_sum, elevation, REF_ELEV)), 1),
            "humidity": round(max(0.0, min(100.0, d.relative_humidity_2m_mean)), 1),
            "wind_kmh": round(max(0.0, stat.apply_wind_correction(
                d.wind_speed_10m_max, diff)), 1),
            "weather_desc": d.weather_description or "Unknown",
        } for d in coarse.daily]

        risks = risk.assess_risks([{
            "temperature": x["temp_max"], "rainfall": x["rainfall_mm"],
            "humidity": x["humidity"], "wind_speed": x["wind_kmh"],
        } for x in daily])
        score = risk.aggregate_risk_score(risks)
        color = risk.get_risk_color(score)
        level = {"GREEN": "Low", "YELLOW": "Moderate",
                 "ORANGE": "High", "RED": "Critical"}[color]
        top = max(risks, key=lambda r: r.severity) if risks else None

        out_villages.append({
            "id": v.id, "name": v.name, "hindi_name": v.hindi_name,
            "lat": v.lat, "lon": v.lon, "elevation_m": elevation,
            "population": v.population, "main_crops": v.main_crops,
            "geocoded": v.geocoded,
            "daily": daily,
            "risk_level": level, "risk_color": color.lower(),
            "top_risk": top.risk_type if top else "None",
            "risks": [{
                "type": r.risk_type, "severity": r.severity,
                "description": r.description, "actions": r.recommended_actions,
            } for r in risks],
        })

    snapshot = {
        "block_id": block_id,
        "block": info.block, "district": info.district, "state": info.state,
        "center_lat": info.center_lat, "center_lon": info.center_lon,
        "generated_on": str(date.today()),
        "source": "Snapshot of real Open-Meteo forecast + elevation API output, downscaled with lapse-rate model. For offline demo use.",
        "coarse": coarse_days,
        "villages": out_villages,
    }
    out = DATA_DIR / f"demo_{block_id}.json"
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Snapshot saved: {out} ({len(out_villages)} villages)")


async def main(blocks: list) -> None:
    for b in blocks:
        await build_block(b)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", default=None, help="Single block id (default: all blocks)")
    args = ap.parse_args()
    svc = PanchayatService()
    targets = [args.block] if args.block else [b.block_id for b in svc.list_blocks()]
    asyncio.run(main(targets))
