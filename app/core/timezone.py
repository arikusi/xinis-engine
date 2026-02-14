"""
Timezone Module
Offline timezone resolution using timezonefinder + zoneinfo
Handles historical DST rules automatically
"""

from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from datetime import datetime

_tf = TimezoneFinder(in_memory=True)  # Singleton, keep in RAM


def get_timezone_str(lat: float, lng: float) -> str:
    """
    Get IANA timezone string from coordinates (e.g. 'Europe/Istanbul')

    Args:
        lat: Latitude (-90 to 90)
        lng: Longitude (-180 to 180)

    Returns:
        IANA timezone string, falls back to 'UTC' if not found
    """
    tz_str = _tf.timezone_at(lat=lat, lng=lng)
    return tz_str or "UTC"


def local_to_utc(local_dt: datetime, lat: float, lng: float) -> tuple[datetime, str]:
    """
    Convert local datetime to UTC. Applies historical DST rules automatically.

    Args:
        local_dt: Naive local datetime (no timezone info)
        lat: Latitude of the location
        lng: Longitude of the location

    Returns:
        Tuple of (utc_datetime_naive, timezone_str)
        utc_datetime is returned as naive (no tzinfo) for Swiss Ephemeris compatibility
    """
    tz_str = get_timezone_str(lat, lng)
    tz = ZoneInfo(tz_str)
    aware = local_dt.replace(tzinfo=tz)
    utc_dt = aware.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return utc_dt, tz_str
