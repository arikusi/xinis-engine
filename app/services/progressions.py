"""
Progressions Service
Business logic for secondary progressions calculations
"""

from datetime import datetime
from typing import Optional
from app.models.chart import NatalChart, ProgressedChart
from app.core.calculator import calculator


def calculate_secondary_progression(
    natal_chart: NatalChart,
    progression_date: datetime,
    house_system: Optional[str] = None
) -> ProgressedChart:
    """
    Calculate secondary progressed chart (1 day = 1 year)

    Args:
        natal_chart: Natal chart
        progression_date: Date to progress to (UTC)
        house_system: Optional house system (defaults to natal's system)

    Returns:
        ProgressedChart object
    """
    return calculator.calculate_progressed_chart(
        natal_chart=natal_chart,
        progression_date=progression_date,
        house_system=house_system
    )
