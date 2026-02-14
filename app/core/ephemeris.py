"""
Swiss Ephemeris Wrapper
Low-level interface to Swiss Ephemeris calculations
"""

import swisseph as swe
from datetime import datetime
from typing import Tuple, Optional
from app.core.config_loader import config_loader


class EphemerisEngine:
    """Swiss Ephemeris calculation engine"""

    _initialized = False

    @classmethod
    def initialize(cls, ephe_path: Optional[str] = None):
        """
        Initialize Swiss Ephemeris

        Args:
            ephe_path: Path to ephemeris data files (optional, None uses pyswisseph built-in data)
        """
        if not cls._initialized:
            if ephe_path is not None:
                # Only set path if explicitly provided
                swe.set_ephe_path(ephe_path)
            # If None, pyswisseph uses its own built-in ephemeris data
            cls._initialized = True

    @staticmethod
    def datetime_to_julian(dt: datetime) -> float:
        """
        Convert datetime to Julian Day Number

        Args:
            dt: Datetime object (assumed UTC)

        Returns:
            Julian Day Number
        """
        return swe.julday(
            dt.year,
            dt.month,
            dt.day,
            dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        )

    @staticmethod
    def julian_to_datetime(jd: float) -> datetime:
        """
        Convert Julian Day Number to datetime

        Args:
            jd: Julian Day Number

        Returns:
            UTC datetime
        """
        year, month, day, hour = swe.revjul(jd)
        hours = int(hour)
        minutes = int((hour - hours) * 60)
        seconds = int(((hour - hours) * 60 - minutes) * 60)

        return datetime(year, month, day, hours, minutes, seconds)

    @staticmethod
    def calculate_planet_position(
        jd: float,
        planet_id: int,
        flags: int = swe.FLG_SWIEPH | swe.FLG_SPEED
    ) -> Tuple[float, float, float, float]:
        """
        Calculate planet position

        Args:
            jd: Julian Day Number
            planet_id: Swiss Ephemeris planet constant
            flags: Calculation flags

        Returns:
            Tuple of (longitude, latitude, distance, speed)
        """
        result, ret = swe.calc_ut(jd, planet_id, flags)

        longitude = result[0]
        latitude = result[1]
        distance = result[2]
        speed = result[3]

        return longitude, latitude, distance, speed

    @staticmethod
    def calculate_houses(
        jd: float,
        latitude: float,
        longitude: float,
        house_system: str = 'P'
    ) -> Tuple[list, list]:
        """
        Calculate house cusps

        Args:
            jd: Julian Day Number
            latitude: Observer latitude (-90 to 90)
            longitude: Observer longitude (-180 to 180)
            house_system: House system code ('P'=Placidus, 'W'=Whole Sign, etc.)

        Returns:
            Tuple of (cusps, ascmc)
            - cusps: List of 13 cusp longitudes (index 0 unused, 1-12 are houses)
            - ascmc: [Ascendant, MC, ARMC, Vertex, Equatorial Asc, ...]
        """
        cusps, ascmc = swe.houses(jd, latitude, longitude, house_system.encode())

        return list(cusps), list(ascmc)

    @staticmethod
    def calculate_fixed_star(jd: float, star_name: str) -> Tuple[float, float]:
        """
        Calculate fixed star position

        Args:
            jd: Julian Day Number
            star_name: Star name (e.g., "Regulus", "Spica")

        Returns:
            Tuple of (longitude, latitude)
        """
        try:
            result, ret = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
            return result[0], result[1]  # longitude, latitude
        except Exception as e:
            # If star not found, return None
            return None, None

    @staticmethod
    def get_house_position(planet_longitude: float, house_cusps: list) -> int:
        """
        Determine which house a planet is in

        Args:
            planet_longitude: Planet's ecliptic longitude (0-360)
            house_cusps: List of 12 house cusp longitudes

        Returns:
            House number (1-12)
        """
        # Ensure we have 12 cusps (skip index 0 if present)
        if len(house_cusps) == 13:
            cusps = house_cusps[1:]
        else:
            cusps = house_cusps[:12]

        for i in range(12):
            cusp_current = cusps[i]
            cusp_next = cusps[(i + 1) % 12]

            # Handle zodiac wrap-around (360 -> 0)
            if cusp_next < cusp_current:
                cusp_next += 360
                planet_lon = planet_longitude
                if planet_lon < cusp_current:
                    planet_lon += 360
            else:
                planet_lon = planet_longitude

            if cusp_current <= planet_lon < cusp_next:
                return i + 1  # House 1-12

        # Fallback to 1st house
        return 1

    @staticmethod
    def calculate_part_of_fortune(
        asc_lon: float,
        sun_lon: float,
        moon_lon: float,
        is_day_birth: bool = True
    ) -> float:
        """
        Calculate Part of Fortune

        Args:
            asc_lon: Ascendant longitude
            sun_lon: Sun longitude
            moon_lon: Moon longitude
            is_day_birth: True if sun above horizon (day chart)

        Returns:
            Part of Fortune longitude
        """
        if is_day_birth:
            # Day formula: Asc + Moon - Sun
            pof = asc_lon + moon_lon - sun_lon
        else:
            # Night formula: Asc + Sun - Moon
            pof = asc_lon + sun_lon - moon_lon

        # Normalize to 0-360
        while pof < 0:
            pof += 360
        while pof >= 360:
            pof -= 360

        return pof

    @staticmethod
    def is_day_birth(sun_lon: float, asc_lon: float) -> bool:
        """
        Determine if birth is day or night

        Args:
            sun_lon: Sun longitude
            asc_lon: Ascendant longitude

        Returns:
            True if day birth (Sun above horizon)
        """
        # Sun is above horizon if it's between Asc and Desc (roughly)
        # More accurate: check if Sun is in houses 7-12
        desc = (asc_lon + 180) % 360

        # Simplified check
        if asc_lon < desc:
            return asc_lon <= sun_lon <= desc
        else:
            return sun_lon >= asc_lon or sun_lon <= desc


# Global instance
ephemeris = EphemerisEngine()
