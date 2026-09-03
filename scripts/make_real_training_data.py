"""Build ML training data from REAL ERA5 reanalysis (Open-Meteo archive).

For N MP locations spanning plains (~150 m) to highlands (~1050 m),
fetches daily 2023-2024 observations, takes the all-point daily mean as
the "coarse block signal", runs OUR statistical baseline per point, and
stores observed-minus-baseline residuals as ML targets.

Resumable: per-point checkpoints in data/era5_raw/ (re-runs skip done
points). Output: data/training_real.csv

Usage: python scripts/make_real_training_data.py
"""
import math
import sys
import time
from datetime import date
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.downscaling.interpolation import StatisticalDownscaler

# MP locations: (name, lat, lon) — plains to Pachmarhi highlands
POINTS = [
    ("Bhopal", 23.26, 77.41), ("Indore", 22.72, 75.86),
    ("Ujjain", 23.18, 75.78), ("Sagar", 23.84, 78.74),
    ("Rewa", 24.53, 81.30), ("Jabalpur", 23.16, 79.95),
    ("Gwalior", 26.22, 78.18), ("Pachmarhi", 22.47, 78.43),
    ("Hoshangabad", 22.75, 77.72), ("Khandwa", 21.83, 76.35),
    ("Khargone", 21.82, 75.61), ("Betul", 21.92, 77.90),
    ("Chhindwara", 22.06, 78.93), ("Mandla", 22.60, 80.37),
    ("Dindori", 22.95, 80.90), ("Amarkantak", 22.67, 81.75),
    ("Shahdol", 23.28, 81.35), ("Satna", 24.60, 80.83),
    ("Panna", 24.72, 80.18), ("Chhatarpur", 24.92, 79.59),
    ("Tikamgarh", 24.74, 78.83), ("Raisen", 23.33, 77.78),
    ("Vidisha", 23.53, 77.81), ("Sehore", 23.20, 77.08),
]

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
ELEV_URL = "https://api.open-meteo.com/v1/elevation"
REF_ELEV = 500.0
COAST = (21.60, 72.60)  # Gulf of Khambhat, nearest sea to MP
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "era5_raw"


def haversine_km(a: tuple, b: tuple) -> float:
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _get_with_retry(client: httpx.Client, url: str, params: dict,
                    timeout: float, tries: int = 4):
    last = None
    for attempt in range(tries):
        try:
            r = client.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            wait = 2 ** attempt
            print(f"    retry {attempt + 1}/{tries} after {wait}s ({type(e).__name__})", flush=True)
            time.sleep(wait)
    raise last


def batch_elevations(client: httpx.Client, lats: list, lons: list,
                     chunk: int = 50) -> list:
    """Elevation API has a per-request coordinate cap — chunk big batches."""
    out: list = []
    for i in range(0, len(lats), chunk):
        r = _get_with_retry(client, ELEV_URL, {
            "latitude": ",".join(map(str, lats[i:i + chunk])),
            "longitude": ",".join(map(str, lons[i:i + chunk])),
        }, timeout=60.0)
        out.extend(float(e) for e in r.json().get("elevation", []))
    return out


def fetch_daily(client: httpx.Client, lat: float, lon: float) -> pd.DataFrame:
    """Daily 2023-2024 series + daily-mean humidity from hourly RH."""
    r = _get_with_retry(client, ARCHIVE_URL, {
        "latitude": lat, "longitude": lon,
        "start_date": "2023-01-01", "end_date": "2024-12-31",
        "daily": ["temperature_2m_max", "temperature_2m_min",
                  "precipitation_sum", "wind_speed_10m_max"],
        "hourly": ["relative_humidity_2m"],
        "timezone": "auto",
    }, timeout=180.0)
    d = r.json()
    daily, hourly = d.get("daily", {}), d.get("hourly", {})
    rh_by_day: dict = {}
    for ts, rh in zip(hourly.get("time", []), hourly.get("relative_humidity_2m", [])):
        if rh is None:
            continue
        rh_by_day.setdefault(ts[:10], []).append(rh)
    rows = []
    for i, day in enumerate(daily.get("time", [])):
        rh_vals = rh_by_day.get(day, [])
        rows.append({
            "date": day,
            "tmax": daily["temperature_2m_max"][i],
            "tmin": daily["temperature_2m_min"][i],
            "precip": daily["precipitation_sum"][i],
            "wind": daily["wind_speed_10m_max"][i],
            "rh": (sum(rh_vals) / len(rh_vals)) if rh_vals else float("nan"),
        })
    return pd.DataFrame(rows).dropna().reset_index(drop=True)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stat = StatisticalDownscaler()
    client = httpx.Client()
    try:
        # ONE batch call: elevations for all points
        lats = [p[1] for p in POINTS]
        lons = [p[2] for p in POINTS]
        er = batch_elevations(client, lats, lons)
        elevs = [(e if e else 500.0) for e in er]
        # pad defensively in case of short responses
        elevs = (elevs + [500.0] * len(POINTS))[:len(POINTS)]
        print(f"elevations: min {min(elevs):.0f} m, max {max(elevs):.0f} m", flush=True)

        # ONE batch call: 3x3 neighbourhoods for all points -> slope/aspect
        step = 1.0 / 111.0
        glats, glons = [], []
        for _, lat, lon in POINTS:
            for i in range(3):
                for j in range(3):
                    glats.append(lat + (i - 1) * step)
                    glons.append(lon + (j - 1) * step)
        flat = batch_elevations(client, glats, glons)
        flat = (flat + [500.0] * len(glats))[:len(glats)]
        grids = np.array(flat).reshape(len(POINTS), 3, 3)
        slopes, aspects = [], []
        for g in grids:
            dy, dx = np.gradient(g, 1000.0, 1000.0)
            slopes.append(float(np.degrees(np.arctan(np.sqrt(dx[1, 1] ** 2 + dy[1, 1] ** 2)))))
            aspects.append(float(np.degrees(np.arctan2(dx[1, 1], dy[1, 1]))) % 360.0)
        print("terrain done", flush=True)

        # Per-point archive series with checkpoint resume
        meta = {}
        for idx, ((name, lat, lon), elev) in enumerate(zip(POINTS, elevs)):
            ckpt = RAW_DIR / f"{idx:02d}_{name}.csv"
            if ckpt.exists():
                df = pd.read_csv(ckpt)
                print(f"[{idx + 1}/{len(POINTS)}] {name}: checkpoint ({len(df)} days)", flush=True)
            else:
                print(f"[{idx + 1}/{len(POINTS)}] {name}: fetching...", flush=True)
                df = fetch_daily(client, lat, lon)
                df.to_csv(ckpt, index=False)
                print(f"[{idx + 1}/{len(POINTS)}] {name}: saved ({len(df)} days)", flush=True)
                time.sleep(1)
            meta[name] = {"df": df, "lat": lat, "lon": lon, "elev": elev,
                          "slope": slopes[idx], "aspect": aspects[idx],
                          "coast": haversine_km((lat, lon), COAST)}
    finally:
        client.close()

    # Coarse daily signal = all-point mean (real synoptic state)
    all_dates = meta[POINTS[0][0]]["df"]["date"]
    coarse = pd.DataFrame({"date": all_dates})
    for col in ["tmax", "tmin", "precip", "wind", "rh"]:
        coarse[col] = np.mean([meta[n]["df"][col].values for n, _, _ in POINTS], axis=0)

    rows = []
    for name, lat, lon in POINTS:
        m = meta[name]
        obs = m["df"].set_index("date")
        for _, c in coarse.iterrows():
            day = c["date"]
            if day not in obs.index:
                continue
            o = obs.loc[day]
            diff = m["elev"] - REF_ELEV
            base_t = stat.apply_lapse_rate(float(c["tmax"]), diff)
            base_p = max(0.0, stat.apply_precipitation_correction(float(c["precip"]), m["elev"], REF_ELEV))
            base_h = max(0.0, min(100.0, float(c["rh"])))
            base_w = max(0.0, stat.apply_wind_correction(float(c["wind"]), diff))
            doy = date.fromisoformat(day).timetuple().tm_yday
            rows.append({
                "lat": lat, "lon": lon, "elevation": m["elev"],
                "slope": m["slope"], "aspect": m["aspect"],
                "distance_to_coast": m["coast"],
                "elevation_difference": diff,
                "coarse_temp": float(c["tmax"]), "coarse_precip": float(c["precip"]),
                "coarse_humidity": float(c["rh"]), "coarse_wind": float(c["wind"]),
                "day_of_year_sin": math.sin(2 * math.pi * doy / 365.25),
                "day_of_year_cos": math.cos(2 * math.pi * doy / 365.25),
                "is_monsoon": 1 if 152 <= doy <= 273 else 0,
                "res_temp": float(o["tmax"]) - base_t,
                "res_precip": float(o["precip"]) - base_p,
                "res_humidity": float(o["rh"]) - base_h,
                "res_wind": float(o["wind"]) - base_w,
            })

    out = Path(__file__).resolve().parent.parent / "data" / "training_real.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {len(rows)} real-data rows -> {out}")


if __name__ == "__main__":
    main()
