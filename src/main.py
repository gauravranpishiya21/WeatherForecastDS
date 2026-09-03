"""Hyperlocal Weather Downscaling & Agro-Advisory System (SIH26074).

FastAPI application entry point.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger
from contextlib import asynccontextmanager

from .utils.config import get_settings
from .api.routes import forecast, advisory, locations, panchayats, search


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("Hyperlocal Weather Downscaling & Agro-Advisory System")
    logger.info("SIH2026 Problem 74")
    logger.info("=" * 60)
    logger.info(f"Default region: {settings.default_region} ({settings.default_lat}, {settings.default_lon})")
    logger.info(f"Gemini API configured: {'Yes' if settings.gemini_api_key else 'No (template fallback)'}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Hyperlocal Weather Downscaling & Agro-Advisory System",
    description=(
        "API for downscaling block-level weather forecasts to panchayat/farm-level "
        "resolution and generating crop-specific agricultural advisories. "
        "Built for Smart India Hackathon 2026 (SIH26074)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(forecast.router, tags=["Forecast"])
app.include_router(advisory.router, tags=["Advisory"])
app.include_router(locations.router, tags=["Locations"])
app.include_router(panchayats.router, tags=["Panchayats"])
app.include_router(search.router, tags=["Search"])


@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Hyperlocal Weather Downscaling & Agro-Advisory System is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
