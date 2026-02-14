"""
XiNiS Data Models
Pydantic models for chart data structures
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    name: Optional[str] = Field(None, description="Location name (optional)")


class BirthData(BaseModel):
    """Birth/event data"""
    datetime_utc: datetime = Field(..., description="UTC datetime")
    location: Location
    julian_day: float = Field(..., description="Julian Day Number")
    timezone_str: Optional[str] = Field(None, description="IANA timezone (e.g. Europe/Istanbul)")
    local_datetime: Optional[datetime] = Field(None, description="Original local datetime")


class PlanetPosition(BaseModel):
    """Celestial body position"""
    name: str = Field(..., description="Planet/body name")
    longitude: float = Field(..., ge=0, lt=360, description="Ecliptic longitude (0-360)")
    latitude: float = Field(..., description="Ecliptic latitude")
    distance: float = Field(..., ge=0, description="Distance in AU (0 for fixed stars)")
    speed: float = Field(..., description="Daily motion in degrees/day")

    # Computed properties
    sign: str = Field(..., description="Zodiac sign")
    sign_symbol: str = Field(..., description="Zodiac sign symbol")
    degree: float = Field(..., ge=0, lt=30, description="Degree within sign (0-30)")
    house: int = Field(..., ge=1, le=12, description="House position (1-12)")
    retrograde: bool = Field(..., description="Is retrograde?")


class Aspect(BaseModel):
    """Aspect between two points"""
    aspect_type: str = Field(..., description="Aspect name (Trine, Square, etc.)")
    angle: float = Field(..., description="Exact angle of aspect (0, 90, 120, etc.)")
    orb: float = Field(..., ge=0, description="Orb/exactness in degrees")
    applying: bool = Field(..., description="Is aspect applying (getting closer)?")
    strength: float = Field(..., ge=0, le=100, description="Aspect strength 0-100")
    symbol: str = Field(..., description="Aspect symbol")
    nature: str = Field(..., description="Aspect nature (harmonious/challenging/neutral)")


class AspectPair(BaseModel):
    """Aspect between two celestial bodies"""
    planet1: str = Field(..., description="First planet/body name")
    planet2: str = Field(..., description="Second planet/body name")
    aspect: Aspect


class Pattern(BaseModel):
    """Aspect pattern (Grand Trine, T-Square, etc.)"""
    pattern_type: str = Field(..., description="Pattern name")
    planets: List[str] = Field(..., description="Planets involved")
    element: Optional[str] = Field(None, description="Element (Fire/Earth/Air/Water)")
    strength: float = Field(..., ge=0, le=100, description="Pattern strength")


class HouseData(BaseModel):
    """House system data"""
    system: str = Field(..., description="House system name")
    cusps: List[float] = Field(..., min_length=12, max_length=12, description="12 house cusps")
    ascendant: float = Field(..., ge=0, lt=360, description="Ascendant (1st house cusp)")
    mc: float = Field(..., ge=0, lt=360, description="Midheaven (10th house cusp)")
    vertex: float = Field(..., ge=0, lt=360, description="Vertex")
    equatorial_ascendant: Optional[float] = Field(None, ge=0, lt=360)


class NatalChart(BaseModel):
    """Complete natal chart"""
    birth_data: BirthData
    planets: Dict[str, PlanetPosition] = Field(..., description="All planetary positions")
    houses: HouseData
    aspects: List[AspectPair] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)


class MultiHouseNatalChart(BaseModel):
    """Natal chart with multiple house systems"""
    birth_data: BirthData
    planets: Dict[str, PlanetPosition] = Field(..., description="All planetary positions")
    all_houses: Dict[str, HouseData] = Field(..., description="All house systems calculated")
    aspects: List[AspectPair] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)


class TransitData(BaseModel):
    """Transit information"""
    transit_date: datetime
    transit_location: Location
    transit_planets: Dict[str, PlanetPosition]
    transit_to_natal_aspects: List[AspectPair]


class TransitChart(BaseModel):
    """Transit chart with natal comparison"""
    natal_chart: NatalChart
    transit_data: TransitData


class ProgressedChart(BaseModel):
    """Secondary progressed chart"""
    natal_chart: NatalChart
    progressed_date: datetime
    progressed_planets: Dict[str, PlanetPosition]
    progressed_houses: HouseData
    progressed_to_natal_aspects: List[AspectPair]


class SolarReturnChart(BaseModel):
    """Solar return chart"""
    natal_chart: NatalChart
    return_year: int
    return_datetime: datetime
    return_location: Location
    return_planets: Dict[str, PlanetPosition]
    return_houses: HouseData
