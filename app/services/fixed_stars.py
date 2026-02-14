"""
Fixed Stars Service
Calculate positions of major fixed stars and star clusters with precession
Uses J2000.0 coordinates and applies precession to target date
"""

import swisseph as swe
from datetime import datetime
from typing import List, Dict, Optional


# Zodiac sign names (index-based lookup)
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# J2000.0 epoch Julian Day
_J2000_JD = 2451545.0

# Precession rate: ~50.29 arcseconds per year
_PRECESSION_RATE = 50.29 / 3600.0

# Major fixed stars - J2000.0 ecliptic coordinates
MAJOR_STARS = {
    "Regulus": {
        "traditional_name": "Regulus",
        "constellation": "Leo",
        "lon_j2000": 149.656,
        "lat_j2000": 0.465,
        "magnitude": 1.35,
        "nature": "Mars-Jupiter",
        "meaning": "Royal star - Success, leadership, honor, courage",
    },
    "Spica": {
        "traditional_name": "Spica",
        "constellation": "Virgo",
        "lon_j2000": 203.987,
        "lat_j2000": -2.046,
        "magnitude": 0.98,
        "nature": "Venus-Mars",
        "meaning": "Abundance, protection, knowledge, gifts",
    },
    "Algol": {
        "traditional_name": "Algol",
        "constellation": "Perseus",
        "lon_j2000": 55.995,
        "lat_j2000": 22.416,
        "magnitude": 2.12,
        "nature": "Saturn-Jupiter",
        "meaning": "Demon star - Danger, transformation, power, intensity",
    },
    "Aldebaran": {
        "traditional_name": "Aldebaran",
        "constellation": "Taurus",
        "lon_j2000": 69.792,
        "lat_j2000": -5.469,
        "magnitude": 0.85,
        "nature": "Mars",
        "meaning": "Bull's eye - Courage, honor, warrior energy, eloquence",
    },
    "Antares": {
        "traditional_name": "Antares",
        "constellation": "Scorpio",
        "lon_j2000": 249.534,
        "lat_j2000": -4.554,
        "magnitude": 1.09,
        "nature": "Mars-Jupiter",
        "meaning": "Heart of Scorpion - Passion, war, danger, obsession",
    },
    "Sirius": {
        "traditional_name": "Sirius",
        "constellation": "Canis Major",
        "lon_j2000": 104.075,
        "lat_j2000": -39.598,
        "magnitude": -1.46,
        "nature": "Jupiter-Mars",
        "meaning": "Dog star - Fame, power, loyalty, heat, ambition",
    },
    "Procyon": {
        "traditional_name": "Procyon",
        "constellation": "Canis Minor",
        "lon_j2000": 114.985,
        "lat_j2000": -16.039,
        "magnitude": 0.34,
        "nature": "Mercury-Mars",
        "meaning": "Activity, sudden change, swiftness, rashness",
    },
    "Betelgeuse": {
        "traditional_name": "Betelgeuse",
        "constellation": "Orion",
        "lon_j2000": 88.646,
        "lat_j2000": -16.009,
        "magnitude": 0.50,
        "nature": "Mars-Mercury",
        "meaning": "War, victory, rapid success, everlasting fame",
    },
    "Rigel": {
        "traditional_name": "Rigel",
        "constellation": "Orion",
        "lon_j2000": 78.628,
        "lat_j2000": -31.067,
        "magnitude": 0.13,
        "nature": "Jupiter-Mars",
        "meaning": "Knowledge, arts, success, honors, riches",
    },
    "Altair": {
        "traditional_name": "Altair",
        "constellation": "Aquila",
        "lon_j2000": 301.750,
        "lat_j2000": 29.291,
        "magnitude": 0.77,
        "nature": "Mars-Jupiter",
        "meaning": "Courage, ambition, rise to power, liberality",
    },
    "Vega": {
        "traditional_name": "Vega",
        "constellation": "Lyra",
        "lon_j2000": 285.122,
        "lat_j2000": 61.753,
        "magnitude": 0.03,
        "nature": "Venus-Mercury",
        "meaning": "Charisma, artistic talent, social grace, beneficence",
    },
    "Arcturus": {
        "traditional_name": "Arcturus",
        "constellation": "Bootes",
        "lon_j2000": 213.943,
        "lat_j2000": 30.747,
        "magnitude": -0.05,
        "nature": "Mars-Jupiter",
        "meaning": "Protection, fortune, honors, riches, prosperity",
    },
    "Capella": {
        "traditional_name": "Capella",
        "constellation": "Auriga",
        "lon_j2000": 81.528,
        "lat_j2000": 22.877,
        "magnitude": 0.08,
        "nature": "Mercury-Mars",
        "meaning": "Curiosity, exploration, learning, inquisitiveness",
    },
    "Fomalhaut": {
        "traditional_name": "Fomalhaut",
        "constellation": "Piscis Austrinus",
        "lon_j2000": 333.776,
        "lat_j2000": -21.018,
        "magnitude": 1.16,
        "nature": "Venus-Mercury",
        "meaning": "Idealism, devotion to ideals, malevolence if ill-aspected",
    },
    "Deneb": {
        "traditional_name": "Deneb",
        "constellation": "Cygnus",
        "lon_j2000": 314.980,
        "lat_j2000": 57.466,
        "magnitude": 1.25,
        "nature": "Venus-Mercury",
        "meaning": "Justice, power, brightness, good fortune",
    },
}

STAR_CLUSTERS = {
    "Pleiades": {
        "traditional_name": "Pleiades (Seven Sisters)",
        "messier": "M45",
        "constellation": "Taurus",
        "lon_j2000": 59.776,
        "lat_j2000": 4.03,
        "meaning": "Tears, loss, group energy, collective consciousness, mourning",
    },
    "Hyades": {
        "traditional_name": "Hyades",
        "constellation": "Taurus",
        "lon_j2000": 69.792,
        "lat_j2000": -5.469,
        "meaning": "Rain bringers, passion, emotional intensity, tears",
    },
    "Praesepe": {
        "traditional_name": "Praesepe (Beehive Cluster)",
        "messier": "M44",
        "constellation": "Cancer",
        "lon_j2000": 127.550,
        "lat_j2000": 0.160,
        "meaning": "Collective, swarm energy, community, nebulous vision",
    },
}


def _apply_precession(lon_j2000: float, target_jd: float) -> float:
    """Apply precession from J2000.0 to target date"""
    years = (target_jd - _J2000_JD) / 365.25
    return (lon_j2000 + _PRECESSION_RATE * years) % 360


def _to_zodiac(longitude: float) -> tuple[str, float]:
    """Convert longitude to (sign_name, degree_in_sign)"""
    return _SIGNS[int(longitude / 30)], longitude % 30


def _datetime_to_jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def calculate_star_position(star_name: str, datetime_utc: datetime) -> Dict:
    """Calculate fixed star position with precession"""
    info = MAJOR_STARS.get(star_name)
    if not info:
        raise ValueError(f"Unknown star: {star_name}")

    jd = _datetime_to_jd(datetime_utc)
    lon = _apply_precession(info["lon_j2000"], jd)
    sign, degree = _to_zodiac(lon)

    return {
        "name": star_name,
        "traditional_name": info["traditional_name"],
        "constellation": info["constellation"],
        "longitude": lon,
        "latitude": info["lat_j2000"],
        "magnitude": info["magnitude"],
        "nature": info["nature"],
        "meaning": info["meaning"],
        "sign": sign,
        "degree": degree,
    }


def calculate_all_major_stars(datetime_utc: datetime) -> List[Dict]:
    """Calculate all major fixed stars, sorted by brightness"""
    stars = []
    for name in MAJOR_STARS:
        try:
            stars.append(calculate_star_position(name, datetime_utc))
        except Exception:
            continue
    stars.sort(key=lambda s: s.get("magnitude", 10))
    return stars


def calculate_cluster(cluster_name: str, datetime_utc: datetime) -> Dict:
    """Calculate star cluster position"""
    info = STAR_CLUSTERS.get(cluster_name)
    if not info:
        raise ValueError(f"Unknown cluster: {cluster_name}")

    jd = _datetime_to_jd(datetime_utc)
    lon = _apply_precession(info["lon_j2000"], jd)
    sign, degree = _to_zodiac(lon)

    return {
        "name": cluster_name,
        "traditional_name": info["traditional_name"],
        "constellation": info["constellation"],
        "messier": info.get("messier"),
        "longitude": lon,
        "latitude": info["lat_j2000"],
        "meaning": info["meaning"],
        "sign": sign,
        "degree": degree,
        "is_cluster": True,
    }


def calculate_all_clusters(datetime_utc: datetime) -> List[Dict]:
    """Calculate all star clusters"""
    clusters = []
    for name in STAR_CLUSTERS:
        try:
            clusters.append(calculate_cluster(name, datetime_utc))
        except Exception:
            continue
    return clusters


def find_conjunctions_with_planets(
    stars: List[Dict],
    planets: Dict,
    orb: float = 1.0,
) -> List[Dict]:
    """Find conjunctions between fixed stars and planets within given orb"""
    conjunctions = []
    for star in stars:
        star_lon = star["longitude"]
        for planet_name, planet_data in planets.items():
            planet_lon = planet_data.get("longitude")
            if planet_lon is None:
                continue

            diff = abs(star_lon - planet_lon)
            if diff > 180:
                diff = 360 - diff

            if diff <= orb:
                conjunctions.append({
                    "star": star["name"],
                    "star_traditional_name": star.get("traditional_name", star["name"]),
                    "star_constellation": star.get("constellation"),
                    "planet": planet_name,
                    "orb": round(diff, 4),
                    "star_longitude": star_lon,
                    "planet_longitude": planet_lon,
                    "star_meaning": star.get("meaning"),
                    "star_nature": star.get("nature"),
                })
    return conjunctions
