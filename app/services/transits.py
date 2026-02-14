"""
Transit Service
Business logic for transit calculations
"""

from datetime import datetime
from typing import Optional
from app.models.chart import NatalChart, TransitChart
from app.core.calculator import calculator


def calculate_transits(
    natal_chart: NatalChart,
    transit_datetime: datetime,
    transit_latitude: Optional[float] = None,
    transit_longitude: Optional[float] = None,
    house_system: Optional[str] = None
) -> TransitChart:
    """
    Calculate transits to natal chart

    Args:
        natal_chart: Natal chart
        transit_datetime: Transit datetime (UTC)
        transit_latitude: Optional transit location latitude
        transit_longitude: Optional transit location longitude
        house_system: Optional house system (defaults to natal's system)

    Returns:
        TransitChart object
    """
    return calculator.calculate_transit_chart(
        natal_chart=natal_chart,
        transit_datetime=transit_datetime,
        transit_latitude=transit_latitude,
        transit_longitude=transit_longitude,
        house_system=house_system
    )
