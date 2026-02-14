"""
Core Chart Calculator
High-level chart calculation orchestration
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from app.models.chart import (
    NatalChart, BirthData, Location, PlanetPosition,
    HouseData, AspectPair, Pattern
)
from app.core.ephemeris import ephemeris
from app.core.celestial_bodies import (
    get_celestial_bodies_to_calculate,
    get_calculated_points,
    get_fixed_stars,
    longitude_to_sign
)
from app.core.aspects import find_all_aspects, detect_patterns
from app.core.config_loader import config_loader


class ChartCalculator:
    """Main chart calculation engine"""

    def __init__(self):
        """Initialize calculator and ephemeris"""
        ephemeris.initialize()

    def calculate_natal_chart(
        self,
        datetime_utc: datetime,
        latitude: float,
        longitude: float,
        location_name: Optional[str] = None,
        house_system: Optional[str] = None,
        calculate_all_houses: bool = False
    ):
        """
        Calculate complete natal chart

        Args:
            datetime_utc: Birth datetime in UTC
            latitude: Birth location latitude
            longitude: Birth location longitude
            location_name: Optional location name
            house_system: House system to use (defaults to config, or "All" for all systems)
            calculate_all_houses: If True, calculate all house systems

        Returns:
            NatalChart or MultiHouseNatalChart object
        """
        from app.models.chart import MultiHouseNatalChart

        # Convert to Julian Day
        jd = ephemeris.datetime_to_julian(datetime_utc)

        # Create location and birth data
        location = Location(
            latitude=latitude,
            longitude=longitude,
            name=location_name
        )

        birth_data = BirthData(
            datetime_utc=datetime_utc,
            location=location,
            julian_day=jd
        )

        # Check if "All" house systems requested
        if house_system == "All" or calculate_all_houses:
            return self._calculate_all_house_systems(jd, latitude, longitude, birth_data)

        # Get house system
        if house_system is None:
            house_system = config_loader.get_house_system_default()

        # Calculate houses
        house_data = self._calculate_houses(jd, latitude, longitude, house_system)

        # Calculate all celestial bodies
        planets = self._calculate_all_bodies(jd, house_data.cusps)

        # Calculate Part of Fortune and other calculated points
        self._add_calculated_points(planets, house_data, house_data.cusps)

        # Find all aspects
        aspects = find_all_aspects(planets)

        # Detect patterns
        patterns = detect_patterns(planets, aspects)

        return NatalChart(
            birth_data=birth_data,
            planets=planets,
            houses=house_data,
            aspects=aspects,
            patterns=patterns
        )

    def _calculate_all_house_systems(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        birth_data: BirthData
    ):
        """Calculate chart with all house systems"""
        from app.models.chart import MultiHouseNatalChart

        # Get all house systems
        house_systems = config_loader.get_house_systems()

        # Calculate all house systems
        all_houses = {}
        for system_name in house_systems.keys():
            house_data = self._calculate_houses(jd, latitude, longitude, system_name)
            all_houses[system_name] = house_data

        # Use first house system (Placidus by default) for planet positions
        default_system = config_loader.get_house_system_default()
        default_cusps = all_houses[default_system].cusps

        # Calculate all celestial bodies
        planets = self._calculate_all_bodies(jd, default_cusps)

        # Calculate Part of Fortune and other calculated points
        self._add_calculated_points(planets, all_houses[default_system], default_cusps)

        # Find all aspects
        aspects = find_all_aspects(planets)

        # Detect patterns
        patterns = detect_patterns(planets, aspects)

        return MultiHouseNatalChart(
            birth_data=birth_data,
            planets=planets,
            all_houses=all_houses,
            aspects=aspects,
            patterns=patterns
        )

    def _calculate_all_bodies(
        self,
        jd: float,
        house_cusps: list
    ) -> Dict[str, PlanetPosition]:
        """Calculate all celestial bodies"""
        planets = {}

        # Get bodies to calculate from config
        bodies_map = get_celestial_bodies_to_calculate()

        for body_name, body_id in bodies_map.items():
            try:
                lon, lat, dist, speed = ephemeris.calculate_planet_position(jd, body_id)

                sign, sign_symbol, degree = longitude_to_sign(lon)
                house = ephemeris.get_house_position(lon, house_cusps)
                retrograde = speed < 0

                planets[body_name] = PlanetPosition(
                    name=body_name,
                    longitude=round(lon, 4),
                    latitude=round(lat, 4),
                    distance=round(dist, 6),
                    speed=round(speed, 6),
                    sign=sign,
                    sign_symbol=sign_symbol,
                    degree=round(degree, 2),
                    house=house,
                    retrograde=retrograde
                )

            except Exception as e:
                logging.getLogger("xinis.calculator").warning("Could not calculate %s: %s", body_name, e)
                continue

        # Calculate fixed stars if enabled
        fixed_stars = get_fixed_stars()
        for star_name in fixed_stars:
            try:
                lon, lat = ephemeris.calculate_fixed_star(jd, star_name)
                if lon is not None:
                    sign, sign_symbol, degree = longitude_to_sign(lon)
                    house = ephemeris.get_house_position(lon, house_cusps)

                    planets[star_name] = PlanetPosition(
                        name=star_name,
                        longitude=round(lon, 4),
                        latitude=round(lat, 4),
                        distance=0.0,
                        speed=0.0,
                        sign=sign,
                        sign_symbol=sign_symbol,
                        degree=round(degree, 2),
                        house=house,
                        retrograde=False
                    )
            except Exception as e:
                logging.getLogger("xinis.calculator").warning("Could not calculate fixed star %s: %s", star_name, e)
                continue

        return planets

    def _calculate_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        house_system: str
    ) -> HouseData:
        """Calculate house cusps"""
        # Get house system code
        house_systems = config_loader.get_house_systems()
        system_data = house_systems.get(house_system, {})

        # Handle both old format (string) and new format (dict)
        if isinstance(system_data, dict):
            system_code = system_data.get("code", "P")
        else:
            system_code = system_data

        # Calculate houses
        cusps, ascmc = ephemeris.calculate_houses(jd, latitude, longitude, system_code)

        # Extract important points
        ascendant = ascmc[0]
        mc = ascmc[1]
        vertex = ascmc[3] if len(ascmc) > 3 else ascendant
        eq_asc = ascmc[4] if len(ascmc) > 4 else None

        return HouseData(
            system=house_system,
            cusps=cusps[1:13] if len(cusps) > 12 else cusps[:12],
            ascendant=round(ascendant, 4),
            mc=round(mc, 4),
            vertex=round(vertex, 4),
            equatorial_ascendant=round(eq_asc, 4) if eq_asc else None
        )

    def _add_calculated_points(
        self,
        planets: Dict[str, PlanetPosition],
        house_data: HouseData,
        house_cusps: list
    ):
        """Add calculated points (Part of Fortune, etc.)"""
        calculated_points = get_calculated_points()

        if "Part_of_Fortune" in calculated_points:
            if "Sun" in planets and "Moon" in planets:
                sun_lon = planets["Sun"].longitude
                moon_lon = planets["Moon"].longitude
                asc_lon = house_data.ascendant

                # Determine if day or night birth
                is_day = ephemeris.is_day_birth(sun_lon, asc_lon)

                # Calculate Part of Fortune
                pof_lon = ephemeris.calculate_part_of_fortune(
                    asc_lon, sun_lon, moon_lon, is_day
                )

                sign, sign_symbol, degree = longitude_to_sign(pof_lon)
                house = ephemeris.get_house_position(pof_lon, house_cusps)

                planets["Part_of_Fortune"] = PlanetPosition(
                    name="Part_of_Fortune",
                    longitude=round(pof_lon, 4),
                    latitude=0.0,
                    distance=0.0,
                    speed=0.0,
                    sign=sign,
                    sign_symbol=sign_symbol,
                    degree=round(degree, 2),
                    house=house,
                    retrograde=False
                )

        if "South_Node" in calculated_points:
            if "True_Node" in planets:
                north_node_lon = planets["True_Node"].longitude
                south_node_lon = (north_node_lon + 180) % 360

                sign, sign_symbol, degree = longitude_to_sign(south_node_lon)
                house = ephemeris.get_house_position(south_node_lon, house_cusps)

                planets["South_Node"] = PlanetPosition(
                    name="South_Node",
                    longitude=round(south_node_lon, 4),
                    latitude=0.0,
                    distance=0.0,
                    speed=-planets["True_Node"].speed,
                    sign=sign,
                    sign_symbol=sign_symbol,
                    degree=round(degree, 2),
                    house=house,
                    retrograde=False
                )

    def calculate_transit_chart(
        self,
        natal_chart: NatalChart,
        transit_datetime: datetime,
        transit_latitude: Optional[float] = None,
        transit_longitude: Optional[float] = None,
        house_system: Optional[str] = None
    ):
        """
        Calculate transits to natal chart

        Args:
            natal_chart: Natal chart
            transit_datetime: Transit datetime (UTC)
            transit_latitude: Location latitude (uses natal if None)
            transit_longitude: Location longitude (uses natal if None)
            house_system: House system to use (uses natal's if None)

        Returns:
            TransitChart object
        """
        from app.models.chart import TransitChart, TransitData
        from app.core.aspects import find_transiting_aspects

        # Use natal location if transit location not specified
        if transit_latitude is None:
            transit_latitude = natal_chart.birth_data.location.latitude
        if transit_longitude is None:
            transit_longitude = natal_chart.birth_data.location.longitude

        # Calculate transit positions
        jd = ephemeris.datetime_to_julian(transit_datetime)

        # Use specified house system or natal's system
        target_house_system = house_system if house_system else natal_chart.houses.system
        house_data = self._calculate_houses(
            jd,
            transit_latitude,
            transit_longitude,
            target_house_system
        )

        transit_planets = self._calculate_all_bodies(jd, house_data.cusps)

        # Find transit-to-natal aspects
        transit_aspects = find_transiting_aspects(
            natal_chart.planets,
            transit_planets
        )

        transit_data = TransitData(
            transit_date=transit_datetime,
            transit_location=Location(
                latitude=transit_latitude,
                longitude=transit_longitude
            ),
            transit_planets=transit_planets,
            transit_to_natal_aspects=transit_aspects
        )

        return TransitChart(
            natal_chart=natal_chart,
            transit_data=transit_data
        )

    def calculate_progressed_chart(
        self,
        natal_chart: NatalChart,
        progression_date: datetime,
        house_system: Optional[str] = None
    ):
        """
        Calculate secondary progressed chart (1 day = 1 year)

        Args:
            natal_chart: Natal chart
            progression_date: Date to progress to (UTC)
            house_system: House system to use (uses natal's if None)

        Returns:
            ProgressedChart object
        """
        from app.models.chart import ProgressedChart
        from app.core.aspects import find_transiting_aspects

        # Calculate progression
        birth_dt = natal_chart.birth_data.datetime_utc
        years_elapsed = (progression_date - birth_dt).days / 365.25

        # Secondary progression: 1 day = 1 year
        # So add years_elapsed days to birth date
        from datetime import timedelta
        progressed_dt = birth_dt + timedelta(days=years_elapsed)

        # Calculate progressed positions
        jd = ephemeris.datetime_to_julian(progressed_dt)

        # Use natal location and house system
        natal_lat = natal_chart.birth_data.location.latitude
        natal_lon = natal_chart.birth_data.location.longitude

        # Calculate progressed houses with specified or natal house system
        target_house_system = house_system if house_system else natal_chart.houses.system
        house_data = self._calculate_houses(
            jd,
            natal_lat,
            natal_lon,
            target_house_system
        )

        # Calculate progressed planets
        progressed_planets = self._calculate_all_bodies(jd, house_data.cusps)

        # Find progressed-to-natal aspects
        progressed_aspects = find_transiting_aspects(
            natal_chart.planets,
            progressed_planets
        )

        return ProgressedChart(
            natal_chart=natal_chart,
            progressed_date=progression_date,
            progressed_planets=progressed_planets,
            progressed_houses=house_data,
            progressed_to_natal_aspects=progressed_aspects
        )

    def calculate_solar_return(
        self,
        natal_chart: NatalChart,
        return_year: int,
        return_location_latitude: Optional[float] = None,
        return_location_longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        house_system: Optional[str] = None
    ):
        """
        Calculate Solar Return chart (Sun returns to natal position)

        Args:
            natal_chart: Natal chart
            return_year: Year for solar return
            return_location_latitude: Location latitude (uses natal if None)
            return_location_longitude: Location longitude (uses natal if None)
            location_name: Optional location name
            house_system: House system to use (uses natal's if None)

        Returns:
            SolarReturnChart object
        """
        from app.models.chart import SolarReturnChart

        # Get natal Sun position
        natal_sun_lon = natal_chart.planets["Sun"].longitude

        # Use natal location if not specified
        if return_location_latitude is None:
            return_location_latitude = natal_chart.birth_data.location.latitude
        if return_location_longitude is None:
            return_location_longitude = natal_chart.birth_data.location.longitude

        # Find when Sun returns to natal position in the given year
        # Start from birthday in return_year
        birth_dt = natal_chart.birth_data.datetime_utc
        search_dt = birth_dt.replace(year=return_year)

        # Search for exact Sun return (within 0.01 deg)
        config = config_loader.load()
        precision = config.get("returns", {}).get("solar_return", {}).get("precision", 0.01)

        return_datetime = self._find_sun_return(search_dt, natal_sun_lon, precision)

        # Calculate chart for return moment
        jd = ephemeris.datetime_to_julian(return_datetime)

        # Use specified house system or natal's system
        target_house_system = house_system if house_system else natal_chart.houses.system
        house_data = self._calculate_houses(
            jd,
            return_location_latitude,
            return_location_longitude,
            target_house_system
        )

        return_planets = self._calculate_all_bodies(jd, house_data.cusps)

        return SolarReturnChart(
            natal_chart=natal_chart,
            return_year=return_year,
            return_datetime=return_datetime,
            return_location=Location(
                latitude=return_location_latitude,
                longitude=return_location_longitude,
                name=location_name
            ),
            return_planets=return_planets,
            return_houses=house_data
        )

    def calculate_lunar_return(
        self,
        natal_chart: NatalChart,
        return_date: datetime,
        return_location_latitude: Optional[float] = None,
        return_location_longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        house_system: Optional[str] = None
    ):
        """
        Calculate Lunar Return chart (Moon returns to natal position)

        Args:
            natal_chart: Natal chart
            return_date: Approximate date for lunar return
            return_location_latitude: Location latitude (uses natal if None)
            return_location_longitude: Location longitude (uses natal if None)
            location_name: Optional location name
            house_system: House system to use (uses natal's if None)

        Returns:
            SolarReturnChart object (reused for lunar returns)
        """
        from app.models.chart import SolarReturnChart

        # Get natal Moon position
        natal_moon_lon = natal_chart.planets["Moon"].longitude

        # Use natal location if not specified
        if return_location_latitude is None:
            return_location_latitude = natal_chart.birth_data.location.latitude
        if return_location_longitude is None:
            return_location_longitude = natal_chart.birth_data.location.longitude

        # Search for exact Moon return (within 0.1 deg)
        config = config_loader.load()
        precision = config.get("returns", {}).get("lunar_return", {}).get("precision", 0.1)

        return_datetime = self._find_moon_return(return_date, natal_moon_lon, precision)

        # Calculate chart for return moment
        jd = ephemeris.datetime_to_julian(return_datetime)

        # Use specified house system or natal's system
        target_house_system = house_system if house_system else natal_chart.houses.system
        house_data = self._calculate_houses(
            jd,
            return_location_latitude,
            return_location_longitude,
            target_house_system
        )

        return_planets = self._calculate_all_bodies(jd, house_data.cusps)

        return SolarReturnChart(
            natal_chart=natal_chart,
            return_year=return_date.year,
            return_datetime=return_datetime,
            return_location=Location(
                latitude=return_location_latitude,
                longitude=return_location_longitude,
                name=location_name
            ),
            return_planets=return_planets,
            return_houses=house_data
        )

    def _find_sun_return(
        self,
        approximate_date: datetime,
        target_longitude: float,
        precision: float
    ) -> datetime:
        """Find exact moment when Sun returns to target longitude"""
        from datetime import timedelta

        # Search in 1-hour increments, then refine
        search_dt = approximate_date - timedelta(days=2)
        end_dt = approximate_date + timedelta(days=2)

        best_dt = search_dt
        best_diff = 360.0

        # Coarse search (hourly)
        current_dt = search_dt
        while current_dt <= end_dt:
            jd = ephemeris.datetime_to_julian(current_dt)
            sun_lon, _, _, _ = ephemeris.calculate_planet_position(jd, 0)

            diff = abs(sun_lon - target_longitude)
            if diff > 180:
                diff = 360 - diff

            if diff < best_diff:
                best_diff = diff
                best_dt = current_dt

            current_dt += timedelta(hours=1)

        # Fine search (minute)
        search_dt = best_dt - timedelta(hours=2)
        end_dt = best_dt + timedelta(hours=2)
        best_diff = 360.0

        current_dt = search_dt
        while current_dt <= end_dt:
            jd = ephemeris.datetime_to_julian(current_dt)
            sun_lon, _, _, _ = ephemeris.calculate_planet_position(jd, 0)

            diff = abs(sun_lon - target_longitude)
            if diff > 180:
                diff = 360 - diff

            if diff < best_diff:
                best_diff = diff
                best_dt = current_dt

            if diff < precision:
                return best_dt

            current_dt += timedelta(minutes=1)

        return best_dt

    def _find_moon_return(
        self,
        approximate_date: datetime,
        target_longitude: float,
        precision: float
    ) -> datetime:
        """Find exact moment when Moon returns to target longitude"""
        from datetime import timedelta

        search_dt = approximate_date - timedelta(days=2)
        end_dt = approximate_date + timedelta(days=2)

        best_dt = search_dt
        best_diff = 360.0

        # Coarse search (hourly)
        current_dt = search_dt
        while current_dt <= end_dt:
            jd = ephemeris.datetime_to_julian(current_dt)
            moon_lon, _, _, _ = ephemeris.calculate_planet_position(jd, 1)

            diff = abs(moon_lon - target_longitude)
            if diff > 180:
                diff = 360 - diff

            if diff < best_diff:
                best_diff = diff
                best_dt = current_dt

            current_dt += timedelta(hours=1)

        # Fine search (5 minutes)
        search_dt = best_dt - timedelta(hours=2)
        end_dt = best_dt + timedelta(hours=2)
        best_diff = 360.0

        current_dt = search_dt
        while current_dt <= end_dt:
            jd = ephemeris.datetime_to_julian(current_dt)
            moon_lon, _, _, _ = ephemeris.calculate_planet_position(jd, 1)

            diff = abs(moon_lon - target_longitude)
            if diff > 180:
                diff = 360 - diff

            if diff < best_diff:
                best_diff = diff
                best_dt = current_dt

            if diff < precision:
                return best_dt

            current_dt += timedelta(minutes=5)

        return best_dt


# Global calculator instance
calculator = ChartCalculator()
