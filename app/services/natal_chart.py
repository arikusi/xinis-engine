"""
Natal Chart Service
Business logic for natal chart calculations
"""

from datetime import datetime
from typing import Optional
from app.models.chart import NatalChart
from app.core.calculator import calculator


def calculate_natal_chart(
    datetime_utc: datetime,
    latitude: float,
    longitude: float,
    location_name: Optional[str] = None,
    house_system: Optional[str] = None
) -> NatalChart:
    """
    Calculate natal chart

    Args:
        datetime_utc: Birth datetime in UTC
        latitude: Birth latitude (-90 to 90)
        longitude: Birth longitude (-180 to 180)
        location_name: Optional location name
        house_system: House system (defaults to config)

    Returns:
        NatalChart object
    """
    return calculator.calculate_natal_chart(
        datetime_utc=datetime_utc,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        house_system=house_system
    )
