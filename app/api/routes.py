"""
API Routes
FastAPI endpoints for chart calculations
No auth - public API. Timezone resolved from coordinates automatically.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.chart import (
    NatalChart, TransitChart, MultiHouseNatalChart,
    ProgressedChart, SolarReturnChart
)
from app.core.timezone import local_to_utc
from app.services import natal_chart, transits, export, progressions, returns

logger = logging.getLogger("xinis.api")

router = APIRouter(prefix="/api", tags=["astrology"])


# --- Request models ---

class NatalChartRequest(BaseModel):
    """Request model for natal chart calculation.
    Accepts local_datetime - timezone is resolved from coordinates automatically."""
    local_datetime: datetime = Field(..., description="Local birth datetime (naive, no timezone)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    location_name: Optional[str] = Field(None, description="Location name")
    house_system: Optional[str] = Field(None, description="House system (default: Placidus)")


class TransitRequest(BaseModel):
    natal_chart: NatalChart
    transit_datetime: datetime = Field(..., description="Transit datetime in UTC")
    transit_latitude: Optional[float] = Field(None, ge=-90, le=90)
    transit_longitude: Optional[float] = Field(None, ge=-180, le=180)
    house_system: Optional[str] = Field(None)


ExportFormat = Literal["json", "markdown", "ai_prompt"]


class ExportRequest(BaseModel):
    chart: Union[NatalChart, MultiHouseNatalChart, TransitChart, ProgressedChart, SolarReturnChart]
    format: ExportFormat = Field(..., description="Export format: json, markdown, ai_prompt")


class ProgressionRequest(BaseModel):
    natal_chart: NatalChart
    progression_date: datetime = Field(..., description="Date to progress to (UTC)")
    house_system: Optional[str] = Field(None)


class SolarReturnRequest(BaseModel):
    natal_chart: NatalChart
    return_year: int = Field(..., description="Year for solar return")
    return_location_latitude: Optional[float] = Field(None, ge=-90, le=90)
    return_location_longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = None
    house_system: Optional[str] = Field(None)


class LunarReturnRequest(BaseModel):
    natal_chart: NatalChart
    return_date: datetime = Field(..., description="Approximate date for lunar return (UTC)")
    return_location_latitude: Optional[float] = Field(None, ge=-90, le=90)
    return_location_longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = None
    house_system: Optional[str] = Field(None)


# --- Endpoints ---

@router.post("/natal-chart", response_model=Union[NatalChart, MultiHouseNatalChart])
def calculate_natal_chart_endpoint(request: NatalChartRequest):
    """
    Calculate natal chart.
    Accepts local datetime - timezone and UTC conversion handled automatically.
    """
    try:
        # Convert local datetime to UTC using coordinates
        utc_dt, tz_str = local_to_utc(request.local_datetime, request.latitude, request.longitude)

        chart = natal_chart.calculate_natal_chart(
            datetime_utc=utc_dt,
            latitude=request.latitude,
            longitude=request.longitude,
            location_name=request.location_name,
            house_system=request.house_system
        )

        # Enrich birth_data with timezone info
        chart.birth_data.timezone_str = tz_str
        chart.birth_data.local_datetime = request.local_datetime

        return chart

    except Exception as e:
        logger.error("Natal chart calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Natal chart calculation failed")


@router.post("/transits", response_model=TransitChart)
def calculate_transits_endpoint(request: TransitRequest):
    """Calculate transits to natal chart"""
    try:
        return transits.calculate_transits(
            natal_chart=request.natal_chart,
            transit_datetime=request.transit_datetime,
            transit_latitude=request.transit_latitude,
            transit_longitude=request.transit_longitude,
            house_system=request.house_system
        )
    except Exception as e:
        logger.error("Transit calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Transit calculation failed")


@router.post("/export")
def export_chart_endpoint(request: ExportRequest):
    """Export chart to various formats: json, markdown, ai_prompt"""
    try:
        chart = request.chart

        if request.format == "json":
            return {"data": export.to_json(chart), "format": "json"}

        elif request.format == "markdown":
            if isinstance(chart, TransitChart):
                return {"data": export.to_transit_markdown(chart), "format": "markdown"}
            elif isinstance(chart, ProgressedChart):
                return {"data": export.to_progression_markdown(chart), "format": "markdown"}
            elif isinstance(chart, SolarReturnChart):
                return {"data": export.to_solar_return_markdown(chart), "format": "markdown"}
            else:
                return {"data": export.to_markdown(chart), "format": "markdown"}

        elif request.format == "ai_prompt":
            if isinstance(chart, TransitChart):
                return {"data": export.to_transit_ai_prompt(chart), "format": "text"}
            elif isinstance(chart, ProgressedChart):
                return {"data": export.to_progression_ai_prompt(chart), "format": "text"}
            elif isinstance(chart, SolarReturnChart):
                return {"data": export.to_solar_return_ai_prompt(chart), "format": "text"}
            else:
                return {"data": export.to_ai_prompt(chart), "format": "text"}

    except Exception as e:
        logger.error("Export failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/config")
def get_config():
    """Get current configuration (public)"""
    from app.core.config_loader import config_loader

    config = config_loader.load()
    return {
        "celestial_bodies": config.get("celestial_bodies", {}),
        "house_systems": config.get("house_systems", {}),
        "aspects": {
            "major": list(config.get("aspects", {}).get("major", {}).keys()),
            "minor": list(config.get("aspects", {}).get("minor", {}).keys())
        }
    }


@router.post("/progressions", response_model=ProgressedChart)
def calculate_progressions_endpoint(request: ProgressionRequest):
    """Calculate secondary progressions (1 day = 1 year)"""
    try:
        return progressions.calculate_secondary_progression(
            natal_chart=request.natal_chart,
            progression_date=request.progression_date,
            house_system=request.house_system
        )
    except Exception as e:
        logger.error("Progression calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Progression calculation failed")


@router.post("/solar-return", response_model=SolarReturnChart)
def calculate_solar_return_endpoint(request: SolarReturnRequest):
    """Calculate Solar Return chart"""
    try:
        return returns.calculate_solar_return(
            natal_chart=request.natal_chart,
            return_year=request.return_year,
            return_location_latitude=request.return_location_latitude,
            return_location_longitude=request.return_location_longitude,
            location_name=request.location_name,
            house_system=request.house_system
        )
    except Exception as e:
        logger.error("Solar return calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Solar return calculation failed")


@router.post("/lunar-return", response_model=SolarReturnChart)
def calculate_lunar_return_endpoint(request: LunarReturnRequest):
    """Calculate Lunar Return chart"""
    try:
        return returns.calculate_lunar_return(
            natal_chart=request.natal_chart,
            return_date=request.return_date,
            return_location_latitude=request.return_location_latitude,
            return_location_longitude=request.return_location_longitude,
            location_name=request.location_name,
            house_system=request.house_system
        )
    except Exception as e:
        logger.error("Lunar return calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Lunar return calculation failed")


@router.post("/fixed-stars")
def calculate_fixed_stars_endpoint(request: NatalChartRequest):
    """Calculate fixed stars positions and conjunctions with planets"""
    try:
        from app.services.fixed_stars import (
            calculate_all_major_stars, calculate_all_clusters,
            find_conjunctions_with_planets
        )
        from app.services import natal_chart as natal_chart_service

        utc_dt, tz_str = local_to_utc(request.local_datetime, request.latitude, request.longitude)

        stars = calculate_all_major_stars(utc_dt)
        clusters = calculate_all_clusters(utc_dt)

        natal_chart_data = natal_chart_service.calculate_natal_chart(
            datetime_utc=utc_dt,
            latitude=request.latitude,
            longitude=request.longitude,
            location_name=request.location_name,
            house_system=request.house_system
        )

        planets_dict = {name: planet.model_dump() for name, planet in natal_chart_data.planets.items()}

        conjunctions = find_conjunctions_with_planets(
            stars=stars, planets=planets_dict, orb=1.0
        )

        return {
            "stars": stars,
            "clusters": clusters,
            "conjunctions": conjunctions,
            "calculation_date": utc_dt.isoformat(),
            "timezone_str": tz_str,
        }

    except Exception as e:
        logger.error("Fixed stars calculation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Fixed stars calculation failed")


class ExportFixedStarsRequest(BaseModel):
    fixed_stars_data: Dict[str, Any] = Field(..., description="Fixed stars calculation result")
    format: ExportFormat = Field(..., description="Export format: json, markdown, ai_prompt")


@router.post("/export-fixed-stars")
def export_fixed_stars_endpoint(request: ExportFixedStarsRequest):
    """Export fixed stars data to various formats"""
    try:
        if request.format == "json":
            return {"data": export.to_fixed_stars_json(request.fixed_stars_data), "format": "json"}
        elif request.format == "markdown":
            return {"data": export.to_fixed_stars_markdown(request.fixed_stars_data), "format": "markdown"}
        elif request.format == "ai_prompt":
            return {"data": export.to_fixed_stars_ai_prompt(request.fixed_stars_data), "format": "text"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fixed stars export failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Fixed stars export failed")


@router.get("/health")
def health_check():
    """Health check endpoint with real service verification"""
    from app.core.ephemeris import EphemerisEngine

    checks = {
        "ephemeris": EphemerisEngine._initialized,
        "config": config_loader._config is not None,
    }
    all_healthy = all(checks.values())

    return {
        "status": "ok" if all_healthy else "degraded",
        "service": "xinis",
        "version": "1.0.0",
        "checks": checks,
    }
