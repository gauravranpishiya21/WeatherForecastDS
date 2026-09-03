"""Panchayat dataset service for the block-level SIH demo.

Multi-block loader: reads every `blocks/*.json` file
(`phanda.json`, `berasia.json`, ...). Coordinates marked
`"geocoded": true` came from live Nominatim geocoding
(see scripts/geocode_villages.py); the rest are approximate
demo locations refreshed with live elevations at request time.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from pydantic import BaseModel, Field


class PanchayatVillage(BaseModel):
    """A single panchayat village in a block."""

    id: str
    name: str
    hindi_name: str = ""
    lat: float
    lon: float
    elevation_m: Optional[float] = None  # fallback; live value fetched at runtime
    population: Optional[int] = None
    main_crops: List[str] = Field(default_factory=list)
    geocoded: bool = False  # True once replaced with real Nominatim coords


class BlockInfo(BaseModel):
    """Block-level metadata."""

    block_id: str
    block: str
    district: str
    state: str
    center_lat: float
    center_lon: float
    total_panchayats: int


class PanchayatService:
    """Loads and serves block panchayat datasets (default block: phanda)."""

    DEFAULT_BLOCK = "phanda"

    def __init__(self, blocks_dir: Optional[str] = None):
        if blocks_dir is None:
            blocks_dir = str(Path(__file__).resolve().parent / "blocks")
        self.blocks_dir = Path(blocks_dir)
        self._blocks: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        files = sorted(self.blocks_dir.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No block datasets in {self.blocks_dir}")
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    self._blocks[fp.stem.lower()] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {fp}: {e}")
                raise
        total = sum(len(b.get("villages", [])) for b in self._blocks.values())
        logger.info(f"Loaded {len(self._blocks)} blocks, {total} panchayats: {sorted(self._blocks)}.")

    def _get_block(self, block_id: str) -> dict:
        bid = (block_id or self.DEFAULT_BLOCK).lower().strip()
        if bid not in self._blocks:
            raise ValueError(f"Unknown block '{block_id}'. Available: {sorted(self._blocks)}")
        return self._blocks[bid]

    def list_blocks(self) -> List[BlockInfo]:
        out = []
        for bid, b in self._blocks.items():
            out.append(BlockInfo(
                block_id=bid, block=b.get("block", bid),
                district=b.get("district", ""), state=b.get("state", ""),
                center_lat=float(b.get("center_lat", 0.0)),
                center_lon=float(b.get("center_lon", 0.0)),
                total_panchayats=len(b.get("villages", [])),
            ))
        return sorted(out, key=lambda x: x.block_id)

    def get_block_info(self, block_id: str = DEFAULT_BLOCK) -> BlockInfo:
        b = self._get_block(block_id)
        return BlockInfo(
            block_id=block_id.lower().strip(), block=b.get("block", ""),
            district=b.get("district", ""), state=b.get("state", ""),
            center_lat=float(b.get("center_lat", 0.0)),
            center_lon=float(b.get("center_lon", 0.0)),
            total_panchayats=len(b.get("villages", [])),
        )

    def list_villages(self, block_id: str = DEFAULT_BLOCK) -> List[PanchayatVillage]:
        return [PanchayatVillage(**v) for v in self._get_block(block_id).get("villages", [])]

    def get_village(self, village_id: str,
                    block_id: str = DEFAULT_BLOCK) -> Optional[PanchayatVillage]:
        vid = village_id.lower().strip()
        for v in self._get_block(block_id).get("villages", []):
            if str(v.get("id", "")).lower() == vid:
                return PanchayatVillage(**v)
        return None

    def save_block(self, block_id: str) -> None:
        """Persist (possibly geocoded) block data back to its JSON file."""
        bid = block_id.lower().strip()
        fp = self.blocks_dir / f"{bid}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(self._blocks[bid], f, ensure_ascii=False, indent=1)
        logger.info(f"Saved {bid} dataset ({len(self._blocks[bid].get('villages', []))} villages).")
