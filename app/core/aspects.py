"""
Aspect Calculator
Find and analyze aspects between celestial bodies
"""

from typing import List, Optional, Dict
from app.models.chart import Aspect, AspectPair, PlanetPosition
from app.core.config_loader import config_loader


def find_aspect_between(
    lon1: float,
    lon2: float,
    speed1: float,
    speed2: float,
    body1_name: str = "",
    body2_name: str = "",
    orb_multiplier: float = 1.0
) -> Optional[Aspect]:
    """
    Find aspect between two celestial bodies

    Args:
        lon1: Longitude of first body (0-360)
        lon2: Longitude of second body (0-360)
        speed1: Daily motion of first body
        speed2: Daily motion of second body
        body1_name: Name of first body (for orb multiplier)
        body2_name: Name of second body (for orb multiplier)
        orb_multiplier: Additional orb multiplier

    Returns:
        Aspect object or None if no aspect found
    """
    # Get aspect definitions from config
    aspect_definitions = config_loader.get_aspects()
    orb_multipliers = config_loader.get_orb_multipliers()

    # Calculate angular difference
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff

    # Apply orb multipliers for luminaries
    final_orb_mult = orb_multiplier
    for body_name in [body1_name, body2_name]:
        if body_name in orb_multipliers:
            final_orb_mult *= orb_multipliers[body_name]

    # Check each aspect definition
    for aspect_name, aspect_data in aspect_definitions.items():
        aspect_angle = aspect_data["angle"]
        base_orb = aspect_data["orb"]
        allowed_orb = base_orb * final_orb_mult

        exactness = abs(diff - aspect_angle)

        if exactness <= allowed_orb:
            # Aspect found!
            applying = is_applying(lon1, lon2, speed1, speed2, aspect_angle)
            strength = calculate_strength(exactness, allowed_orb)

            return Aspect(
                aspect_type=aspect_name,
                angle=aspect_angle,
                orb=round(exactness, 2),
                applying=applying,
                strength=strength,
                symbol=aspect_data.get("symbol", ""),
                nature=aspect_data.get("nature", "neutral")
            )

    return None


def is_applying(
    lon1: float,
    lon2: float,
    speed1: float,
    speed2: float,
    aspect_angle: float
) -> bool:
    """
    Determine if aspect is applying (getting closer) or separating

    Args:
        lon1: Longitude of first body
        lon2: Longitude of second body
        speed1: Daily motion of first body
        speed2: Daily motion of second body
        aspect_angle: Target aspect angle (0, 90, 120, etc.)

    Returns:
        True if applying, False if separating
    """
    # Calculate current angular distance
    current_diff = abs(lon1 - lon2)
    if current_diff > 180:
        current_diff = 360 - current_diff

    # Calculate future positions (1 day ahead)
    future_lon1 = lon1 + speed1
    future_lon2 = lon2 + speed2

    # Calculate future angular distance
    future_diff = abs(future_lon1 - future_lon2)
    if future_diff > 180:
        future_diff = 360 - future_diff

    # Current exactness vs exact aspect angle
    current_exactness = abs(current_diff - aspect_angle)
    future_exactness = abs(future_diff - aspect_angle)

    # Applying if future is more exact
    return future_exactness < current_exactness


def calculate_strength(exactness: float, max_orb: float) -> float:
    """
    Calculate aspect strength (0-100)

    Args:
        exactness: How far from exact (0 = exact)
        max_orb: Maximum orb allowed

    Returns:
        Strength percentage (100 = exact, 0 = at orb limit)
    """
    if max_orb == 0:
        return 100.0

    strength = 100.0 * (1.0 - (exactness / max_orb))
    return max(0.0, min(100.0, strength))


def find_all_aspects(
    planets: Dict[str, PlanetPosition],
    orb_multiplier: float = 1.0
) -> List[AspectPair]:
    """
    Find all aspects between all planets

    Args:
        planets: Dictionary of planet positions
        orb_multiplier: Global orb multiplier

    Returns:
        List of all aspect pairs found
    """
    aspects = []
    planet_list = list(planets.items())

    # Compare each planet pair
    for i, (name1, data1) in enumerate(planet_list):
        for name2, data2 in planet_list[i + 1:]:
            aspect = find_aspect_between(
                data1.longitude,
                data2.longitude,
                data1.speed,
                data2.speed,
                name1,
                name2,
                orb_multiplier
            )

            if aspect:
                aspects.append(AspectPair(
                    planet1=name1,
                    planet2=name2,
                    aspect=aspect
                ))

    return aspects


def find_transiting_aspects(
    natal_planets: Dict[str, PlanetPosition],
    transit_planets: Dict[str, PlanetPosition],
    orb_multiplier: float = 0.8  # Tighter orbs for transits
) -> List[AspectPair]:
    """
    Find aspects between transiting planets and natal planets

    Args:
        natal_planets: Natal planet positions
        transit_planets: Transit planet positions
        orb_multiplier: Orb multiplier for transits (typically tighter)

    Returns:
        List of transit-to-natal aspects
    """
    aspects = []

    for transit_name, transit_data in transit_planets.items():
        for natal_name, natal_data in natal_planets.items():
            aspect = find_aspect_between(
                transit_data.longitude,
                natal_data.longitude,
                transit_data.speed,
                natal_data.speed,
                transit_name,
                natal_name,
                orb_multiplier
            )

            if aspect:
                aspects.append(AspectPair(
                    planet1=f"Transit_{transit_name}",
                    planet2=f"Natal_{natal_name}",
                    aspect=aspect
                ))

    return aspects


def detect_patterns(
    planets: Dict[str, PlanetPosition],
    aspects: List[AspectPair]
) -> List:
    """
    Detect aspect patterns (Grand Trine, T-Square, etc.)

    Args:
        planets: All planet positions
        aspects: All aspects found

    Returns:
        List of patterns detected
    """
    from app.models.chart import Pattern
    patterns = []

    # Get pattern definitions from config
    pattern_defs = config_loader.get_patterns()

    # Build aspect graph for pattern detection
    aspect_graph = build_aspect_graph(aspects)

    # Detect Grand Trines
    if "grand_trine" in pattern_defs:
        grand_trines = detect_grand_trines(aspect_graph, pattern_defs["grand_trine"])
        patterns.extend(grand_trines)

    # Detect T-Squares
    if "t_square" in pattern_defs:
        t_squares = detect_t_squares(aspect_graph, pattern_defs["t_square"])
        patterns.extend(t_squares)

    # Detect Stelliums
    if "stellium" in pattern_defs:
        stelliums = detect_stelliums(planets, pattern_defs["stellium"])
        patterns.extend(stelliums)

    return patterns


def build_aspect_graph(aspects: List[AspectPair]) -> Dict[str, Dict[str, Aspect]]:
    """
    Build aspect graph for pattern detection

    Returns:
        Graph: {planet1: {planet2: aspect, ...}, ...}
    """
    graph = {}

    for aspect_pair in aspects:
        p1 = aspect_pair.planet1
        p2 = aspect_pair.planet2

        if p1 not in graph:
            graph[p1] = {}
        if p2 not in graph:
            graph[p2] = {}

        graph[p1][p2] = aspect_pair.aspect
        graph[p2][p1] = aspect_pair.aspect

    return graph


def detect_grand_trines(aspect_graph: dict, config: dict) -> List:
    """Detect Grand Trine patterns (3 planets in trine)"""
    from app.models.chart import Pattern

    patterns = []
    checked = set()

    for p1 in aspect_graph:
        for p2 in aspect_graph[p1]:
            if aspect_graph[p1][p2].aspect_type == "Trine":
                for p3 in aspect_graph[p2]:
                    if p3 != p1 and aspect_graph[p2][p3].aspect_type == "Trine":
                        if p1 in aspect_graph[p3] and aspect_graph[p3][p1].aspect_type == "Trine":
                            combo = tuple(sorted([p1, p2, p3]))
                            if combo not in checked:
                                checked.add(combo)
                                patterns.append(Pattern(
                                    pattern_type="Grand Trine",
                                    planets=list(combo),
                                    element="",
                                    strength=90.0
                                ))

    return patterns


def detect_t_squares(aspect_graph: dict, config: dict) -> List:
    """Detect T-Square patterns"""
    from app.models.chart import Pattern

    patterns = []
    checked = set()

    for p1 in aspect_graph:
        for p2 in aspect_graph[p1]:
            if aspect_graph[p1][p2].aspect_type == "Opposition":
                for p3 in aspect_graph:
                    if p3 != p1 and p3 != p2:
                        if (p1 in aspect_graph.get(p3, {}) and
                            aspect_graph[p3][p1].aspect_type == "Square" and
                            p2 in aspect_graph.get(p3, {}) and
                            aspect_graph[p3][p2].aspect_type == "Square"):

                            combo = tuple(sorted([p1, p2, p3]))
                            if combo not in checked:
                                checked.add(combo)
                                patterns.append(Pattern(
                                    pattern_type="T-Square",
                                    planets=list(combo),
                                    element=None,
                                    strength=85.0
                                ))

    return patterns


def detect_stelliums(planets: Dict[str, PlanetPosition], config: dict) -> List:
    """Detect Stellium patterns (3+ planets in same sign/house)"""
    from app.models.chart import Pattern

    patterns = []
    min_planets = config.get("min_planets", 3)

    # Group by sign
    sign_groups = {}
    for name, data in planets.items():
        sign = data.sign
        if sign not in sign_groups:
            sign_groups[sign] = []
        sign_groups[sign].append(name)

    # Find stelliums
    for sign, planet_names in sign_groups.items():
        if len(planet_names) >= min_planets:
            patterns.append(Pattern(
                pattern_type="Stellium",
                planets=planet_names,
                element=sign,
                strength=80.0
            ))

    return patterns
