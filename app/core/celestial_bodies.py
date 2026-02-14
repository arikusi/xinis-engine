"""
Celestial Bodies Mapping
Maps configuration body names to Swiss Ephemeris constants
"""

import swisseph as swe
from typing import Dict, List
from app.core.config_loader import config_loader


# Swiss Ephemeris ID mapping
CELESTIAL_BODY_MAP = {
    # Major Planets
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,

    # Nodes
    "True_Node": swe.TRUE_NODE,
    "Mean_Node": swe.MEAN_NODE,

    # Major Asteroids & Centaurs
    "Chiron": swe.CHIRON,
    "Ceres": swe.CERES,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,

    # Lilith (Black Moon)
    "Lilith": swe.MEAN_APOG,      # Mean Apogee (Black Moon Lilith)
    "True_Lilith": swe.OSCU_APOG, # Osculating Apogee (True Lilith)

    # Dwarf Planets
    "Eris": 136199,  # Swiss Ephemeris asteroid number
    "Sedna": 90377,

    # Additional Asteroids
    "Eros": 433,
    "Psyche": 16,
    "Hygiea": 10,

    # Centaurs
    "Nessus": 7066,
    "Pholus": 5145,
}

# Calculated points (not direct ephemeris)
CALCULATED_POINTS = {
    "Part_of_Fortune",
    "Vertex",
    "South_Node",
}

# Zodiac signs mapping
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_SYMBOLS = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓"
]


def get_celestial_bodies_to_calculate() -> Dict[str, int]:
    """
    Get all celestial bodies to calculate from config

    Returns:
        Dictionary mapping body name to Swiss Ephemeris ID
    """
    config = config_loader.get_celestial_bodies()
    bodies = {}

    # Major planets
    for body in config.get("major_planets", []):
        if body in CELESTIAL_BODY_MAP:
            bodies[body] = CELESTIAL_BODY_MAP[body]

    # Nodes
    for body in config.get("nodes", []):
        if body in CELESTIAL_BODY_MAP:
            bodies[body] = CELESTIAL_BODY_MAP[body]

    # Asteroids
    for body in config.get("asteroids", []):
        if body in CELESTIAL_BODY_MAP:
            bodies[body] = CELESTIAL_BODY_MAP[body]

    # Extended asteroids
    for body in config.get("extended_asteroids", []):
        if body in CELESTIAL_BODY_MAP:
            bodies[body] = CELESTIAL_BODY_MAP[body]

    return bodies


def get_calculated_points() -> List[str]:
    """
    Get calculated points (not from ephemeris)

    Returns:
        List of calculated point names
    """
    config = config_loader.get_celestial_bodies()
    return config.get("calculated_points", [])


def get_fixed_stars() -> List[str]:
    """
    Get fixed stars if enabled

    Returns:
        List of fixed star names
    """
    config = config_loader.get_fixed_stars()
    if config.get("enabled", False):
        return config.get("stars", [])
    return []


def longitude_to_sign(longitude: float) -> tuple[str, str, float]:
    """
    Convert ecliptic longitude to zodiac sign

    Args:
        longitude: 0-360 degrees

    Returns:
        Tuple of (sign_name, sign_symbol, degree_in_sign)
    """
    sign_index = int(longitude / 30)
    degree = longitude % 30

    return (
        ZODIAC_SIGNS[sign_index],
        ZODIAC_SYMBOLS[sign_index],
        degree
    )


def get_sign_element(sign_name: str) -> str:
    """Get element for a zodiac sign"""
    zodiac_config = config_loader.get_zodiac_signs()

    for sign in zodiac_config:
        if sign["name"] == sign_name:
            return sign.get("element", "")

    return ""


def get_sign_modality(sign_name: str) -> str:
    """Get modality for a zodiac sign"""
    zodiac_config = config_loader.get_zodiac_signs()

    for sign in zodiac_config:
        if sign["name"] == sign_name:
            return sign.get("modality", "")

    return ""
