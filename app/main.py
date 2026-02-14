"""
XiNiS Astrology API
Public API - no auth, CORS restricted by environment
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.ephemeris import ephemeris
from app.core.config_loader import config_loader

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("xinis")

# --- Config ---
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:80").split(",")


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ephemeris and configuration on startup"""
    config = config_loader.load()
    ephemeris.initialize(None)

    from app.core.celestial_bodies import get_celestial_bodies_to_calculate
    bodies = get_celestial_bodies_to_calculate()
    aspects = config_loader.get_aspects()
    house_systems = config_loader.get_house_systems()

    logger.info(
        "XiNiS API v1.0 ready | Bodies: %d | Aspects: %d | House systems: %d",
        len(bodies), len(aspects), len(house_systems),
    )
    yield
    logger.info("XiNiS API shutting down")


app = FastAPI(
    title="XiNiS Astrology API",
    description="Professional astrology calculation engine with Swiss Ephemeris",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=3600,
)

app.include_router(router)


# --- Global exception handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


@app.get("/")
def root():
    return {
        "name": "XiNiS Astrology API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
