"""
Returns Service
Business logic for Solar and Lunar Returns calculations
"""

from datetime import datetime
from typing import Optional
from app.models.chart import NatalChart, SolarReturnChart
from app.core.calculator import calculator


def calculate_solar_return(
    natal_chart: NatalChart,
    return_year: int,
    return_location_latitude: Optional[float] = None,
    return_location_longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    house_system: Optional[str] = None
) -> SolarReturnChart:
    """
    Calculate Solar Return chart for a given year

    Args:
        natal_chart: Natal chart
        return_year: Year for solar return
        return_location_latitude: Location latitude (uses natal if None)
        return_location_longitude: Location longitude (uses natal if None)
        location_name: Optional location name
        house_system: Optional house system (defaults to natal's system)

    Returns:
        SolarReturnChart object
    """
    return calculator.calculate_solar_return(
        natal_chart=natal_chart,
        return_year=return_year,
        return_location_latitude=return_location_latitude,
        return_location_longitude=return_location_longitude,
        location_name=location_name,
        house_system=house_system
    )


def calculate_lunar_return(
    natal_chart: NatalChart,
    return_date: datetime,
    return_location_latitude: Optional[float] = None,
    return_location_longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    house_system: Optional[str] = None
) -> SolarReturnChart:
    """
    Calculate Lunar Return chart for approximate date

    Args:
        natal_chart: Natal chart
        return_date: Approximate date for lunar return
        return_location_latitude: Location latitude (uses natal if None)
        return_location_longitude: Location longitude (uses natal if None)
        location_name: Optional location name
        house_system: Optional house system (defaults to natal's system)

    Returns:
        SolarReturnChart object (reused model)
    """
    return calculator.calculate_lunar_return(
        natal_chart=natal_chart,
        return_date=return_date,
        return_location_latitude=return_location_latitude,
        return_location_longitude=return_location_longitude,
        location_name=location_name,
        house_system=house_system
    )
