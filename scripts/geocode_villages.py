"""Replace approximate village coordinates with real geocoded ones.

Uses the free Open-Meteo geocoding API (no key needed):
  https://geocoding-api.open-meteo.com/v1/search
Accepts a hit only if admin1 is Madhya Pradesh AND it falls within
~0.25 degrees of the block center. Persists with "geocoded": true.
Villages with no acceptable hit keep approximate demo coordinates.

Usage: python scripts/geocode_villages.py
"""
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.panchayats import PanchayatService

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_DEG = 0.25


def geocode(client: httpx.Client, name: str) -> list:
    r = client.get(GEO_URL, params={
        "name": name,
        "count": 8, "language": "en", "format": "json",
    }, timeout=30.0)
    r.raise_for_status()
    return r.json().get("results", []) or []


def main() -> None:
    svc = PanchayatService()
    client = httpx.Client()
    try:
        for info in svc.list_blocks():
            block = svc._get_block(info.block_id)
            cx, cy = info.center_lat, info.center_lon
            fixed, kept = 0, 0
            for v in block.get("villages", []):
                if v.get("geocoded"):
                    fixed += 1
                    continue
                try:
                    hits = geocode(client, v["name"])
                except Exception as e:
                    print(f"  [{info.block_id}] {v['name']}: API failed ({e}), kept approximate", flush=True)
                    kept += 1
                    continue
                best = None
                for h in hits:
                    if h.get("country") != "India":
                        continue
                    if "madhya pradesh" not in str(h.get("admin1", "")).lower():
                        continue
                    if abs(h["latitude"] - cx) <= MAX_DEG and abs(h["longitude"] - cy) <= MAX_DEG:
                        best = h
                        break
                if best is None:
                    print(f"  [{info.block_id}] {v['name']}: no in-MP hit, kept approximate", flush=True)
                    kept += 1
                    continue
                v["lat"] = round(best["latitude"], 5)
                v["lon"] = round(best["longitude"], 5)
                v["geocoded"] = True
                fixed += 1
                print(f"  [{info.block_id}] {v['name']}: -> ({v['lat']}, {v['lon']})", flush=True)
                time.sleep(0.5)
            svc.save_block(info.block_id)
            print(f"[{info.block_id}] geocoded={fixed} approximate={kept}", flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    main()
