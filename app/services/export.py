"""
Export Service
Export charts to JSON, Markdown, and AI-ready prompt formats.
"""

import json
from typing import Dict, Any, Union
from app.models.chart import (
    NatalChart, TransitChart, MultiHouseNatalChart,
    ProgressedChart, SolarReturnChart
)
from app.core.config_loader import config_loader


def to_json(chart: Union[NatalChart, MultiHouseNatalChart, TransitChart, ProgressedChart, SolarReturnChart]) -> str:
    """Export chart to JSON string"""
    export_config = config_loader.load().get("export", {}).get("json", {})
    indent = export_config.get("indent", 2) if export_config.get("pretty_print", True) else None
    return json.dumps(chart.model_dump(), indent=indent, default=str)


def _format_position(degree: float) -> str:
    """Format degree as Xd MM'"""
    d = int(degree)
    m = int((degree - d) * 60)
    return f"{d}d{m:02d}'"


def _motion_label(planet) -> str:
    if planet.retrograde:
        return "R"
    if abs(planet.speed) < 0.01:
        return "S"
    return "D"


def to_markdown(chart: Union[NatalChart, MultiHouseNatalChart]) -> str:
    """Export natal chart to structured Markdown"""
    from app.core.celestial_bodies import longitude_to_sign, get_sign_element, get_sign_modality

    is_multi = isinstance(chart, MultiHouseNatalChart)
    lines = []

    # Birth data
    lines.append("# Natal Chart Report\n")
    lines.append(f"- **Date/Time (UTC):** {chart.birth_data.datetime_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    if chart.birth_data.timezone_str:
        lines.append(f"- **Timezone:** {chart.birth_data.timezone_str}")
    if chart.birth_data.local_datetime:
        lines.append(f"- **Local Time:** {chart.birth_data.local_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Location:** {chart.birth_data.location.name or 'Unknown'}")
    lines.append(f"- **Coordinates:** {chart.birth_data.location.latitude:.4f}, {chart.birth_data.location.longitude:.4f}")
    if is_multi:
        lines.append("- **House Systems:** All (multi-system comparison)")
    else:
        lines.append(f"- **House System:** {chart.houses.system}")
    lines.append(f"- **Julian Day:** {chart.birth_data.julian_day:.6f}")
    lines.append("")

    # Planetary positions table
    lines.append("## Planetary Positions\n")
    lines.append("| Planet | Sign | Position | House | Motion | Speed |")
    lines.append("|--------|------|----------|-------|--------|-------|")
    for name, p in chart.planets.items():
        lines.append(
            f"| {p.name} | {p.sign_symbol} {p.sign} | {_format_position(p.degree)} "
            f"| {p.house} | {_motion_label(p)} | {p.speed:.4f} |"
        )
    lines.append("")

    # Element distribution
    elements = {"Fire": [], "Earth": [], "Air": [], "Water": []}
    for name, p in chart.planets.items():
        el = get_sign_element(p.sign)
        if el in elements:
            elements[el].append(name)

    lines.append("### Element Distribution\n")
    for el, planets_list in elements.items():
        if planets_list:
            lines.append(f"- **{el}:** {', '.join(planets_list)}")
    lines.append("")

    # Aspects
    lines.append("## Aspects\n")
    if chart.aspects:
        lines.append(f"Total: {len(chart.aspects)}\n")
        lines.append("| Planet 1 | Aspect | Planet 2 | Orb | Status | Strength | Nature |")
        lines.append("|----------|--------|----------|-----|--------|----------|--------|")
        for ap in sorted(chart.aspects, key=lambda x: x.aspect.strength, reverse=True):
            a = ap.aspect
            status = "Applying" if a.applying else "Separating"
            lines.append(
                f"| {ap.planet1} | {a.symbol} {a.aspect_type} | {ap.planet2} "
                f"| {a.orb:.2f} | {status} | {a.strength:.0f}% | {a.nature} |"
            )
        lines.append("")
    else:
        lines.append("No major aspects found within orb.\n")

    # Patterns
    if chart.patterns:
        lines.append("## Aspect Patterns\n")
        for pat in chart.patterns:
            planets_str = ", ".join(pat.planets)
            el_str = f" ({pat.element})" if pat.element else ""
            lines.append(f"- **{pat.pattern_type}**: {planets_str}{el_str} - {pat.strength:.0f}%")
        lines.append("")

    # Houses
    if is_multi:
        lines.append("## House Systems Comparison\n")
        for sys_name, hd in chart.all_houses.items():
            lines.append(f"### {sys_name}\n")
            lines.append(f"ASC: {hd.ascendant:.2f} | MC: {hd.mc:.2f} | Vertex: {hd.vertex:.2f}\n")
            lines.append("| House | Cusp |")
            lines.append("|-------|------|")
            for i, cusp in enumerate(hd.cusps, 1):
                sign, sym, deg = longitude_to_sign(cusp)
                lines.append(f"| {i} | {cusp:.2f} ({sym} {sign}) |")
            lines.append("")
    else:
        lines.append("## House Cusps\n")
        lines.append("| House | Degree | Sign |")
        lines.append("|-------|--------|------|")
        for i, cusp in enumerate(chart.houses.cusps, 1):
            sign, sym, deg = longitude_to_sign(cusp)
            lines.append(f"| {i} | {cusp:.2f} | {sym} {sign} |")
        lines.append("")
        lines.append(f"ASC: {chart.houses.ascendant:.2f} | MC: {chart.houses.mc:.2f} | Vertex: {chart.houses.vertex:.2f}")
        lines.append("")

    # Summary statistics
    lines.append("## Summary\n")
    element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modality_count = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    for name, p in chart.planets.items():
        if name in ("Part_of_Fortune", "South_Node", "Vertex"):
            continue
        el = get_sign_element(p.sign)
        if el in element_count:
            element_count[el] += 1
        mod = get_sign_modality(p.sign)
        if mod in modality_count:
            modality_count[mod] += 1

    total_el = sum(element_count.values()) or 1
    total_mod = sum(modality_count.values()) or 1

    for el, cnt in element_count.items():
        lines.append(f"- {el}: {cnt} ({cnt / total_el * 100:.0f}%)")
    lines.append(f"- Dominant element: {max(element_count, key=element_count.get)}\n")

    for mod, cnt in modality_count.items():
        lines.append(f"- {mod}: {cnt} ({cnt / total_mod * 100:.0f}%)")
    lines.append(f"- Dominant modality: {max(modality_count, key=modality_count.get)}")

    retrogrades = [p.name for p in chart.planets.values() if p.retrograde]
    if retrogrades:
        lines.append(f"\nRetrograde: {', '.join(retrogrades)}")

    return "\n".join(lines)


def to_transit_markdown(transit_chart: TransitChart) -> str:
    """Export transit chart to Markdown"""
    lines = [
        "# Transit Chart Report\n",
        f"**Transit Date:** {transit_chart.transit_data.transit_date.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        "## Transit-to-Natal Aspects\n",
    ]
    if transit_chart.transit_data.transit_to_natal_aspects:
        lines.append("| Transit | Natal | Aspect | Orb | Status |")
        lines.append("|---------|-------|--------|-----|--------|")
        for ap in transit_chart.transit_data.transit_to_natal_aspects:
            a = ap.aspect
            lines.append(
                f"| {ap.planet1} | {ap.planet2} | {a.aspect_type} {a.symbol} "
                f"| {a.orb:.2f} | {'Applying' if a.applying else 'Separating'} |"
            )
    else:
        lines.append("No significant transit aspects found.")
    return "\n".join(lines)


def to_progression_markdown(progressed_chart: ProgressedChart) -> str:
    """Export progressed chart to Markdown"""
    birth_dt = progressed_chart.natal_chart.birth_data.datetime_utc
    years = (progressed_chart.progressed_date - birth_dt).days / 365.25

    lines = [
        "# Secondary Progression Report\n",
        f"**Progression Date:** {progressed_chart.progressed_date.strftime('%Y-%m-%d')}",
        f"**Years from birth:** {years:.1f}\n",
        "## Progressed Positions\n",
        "| Planet | Natal | Progressed | Movement | Sign |",
        "|--------|-------|------------|----------|------|",
    ]
    for name, prog in progressed_chart.progressed_planets.items():
        if name in progressed_chart.natal_chart.planets:
            natal = progressed_chart.natal_chart.planets[name]
            movement = prog.longitude - natal.longitude
            if movement > 180:
                movement -= 360
            elif movement < -180:
                movement += 360
            lines.append(
                f"| {name} | {natal.longitude:.2f} | {prog.longitude:.2f} "
                f"| {movement:+.2f} | {prog.sign_symbol} {prog.sign} |"
            )

    lines.append("\n## Progressed-to-Natal Aspects\n")
    if progressed_chart.progressed_to_natal_aspects:
        lines.append("| Progressed | Natal | Aspect | Orb | Status |")
        lines.append("|------------|-------|--------|-----|--------|")
        for ap in progressed_chart.progressed_to_natal_aspects:
            a = ap.aspect
            lines.append(
                f"| {ap.planet1} | {ap.planet2} | {a.aspect_type} {a.symbol} "
                f"| {a.orb:.2f} | {'Applying' if a.applying else 'Separating'} |"
            )
    else:
        lines.append("No significant progressed aspects found.")
    return "\n".join(lines)


def to_solar_return_markdown(solar_return: SolarReturnChart) -> str:
    """Export Solar/Lunar Return chart to Markdown"""
    days_diff = abs((solar_return.return_datetime - solar_return.natal_chart.birth_data.datetime_utc).days)
    years_diff = days_diff / 365.25
    is_lunar = abs(years_diff - round(years_diff)) >= 0.1
    chart_type = "Lunar" if is_lunar else "Solar"

    lines = [
        f"# {chart_type} Return Chart Report\n",
        f"**Year:** {solar_return.return_year}",
        f"**Exact Return:** {solar_return.return_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Location:** {solar_return.return_location.name or 'Coordinates provided'}\n",
        "## Return Chart Planets\n",
        "| Planet | Position | Sign | House |",
        "|--------|----------|------|-------|",
    ]
    for name, p in solar_return.return_planets.items():
        lines.append(
            f"| {p.name} | {_format_position(p.degree)} | {p.sign_symbol} {p.sign} | {p.house} |"
        )

    lines.append(f"\n**ASC:** {solar_return.return_houses.ascendant:.2f} | **MC:** {solar_return.return_houses.mc:.2f}")
    return "\n".join(lines)


def to_ai_prompt(chart: Union[NatalChart, MultiHouseNatalChart]) -> str:
    """Generate AI analysis prompt from chart data"""
    is_multi = isinstance(chart, MultiHouseNatalChart)
    parts = [
        "You are a professional astrologer. Analyze this natal chart:\n",
        f"- Date/Time: {chart.birth_data.datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- Location: {chart.birth_data.location.name or 'Coordinates provided'}",
    ]
    if is_multi:
        parts.append("- House Systems: All (multi-system comparison)\n")
    else:
        parts.append(f"- House System: {chart.houses.system}\n")

    parts.append("Key Planetary Positions:")
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        if name in chart.planets:
            p = chart.planets[name]
            retro = " (R)" if p.retrograde else ""
            parts.append(f"- {name}: {p.degree:.1f} {p.sign}, House {p.house}{retro}")

    parts.append("\nMajor Aspects:")
    for ap in chart.aspects[:10]:
        a = ap.aspect
        parts.append(f"- {ap.planet1} {a.aspect_type} {ap.planet2} (orb {a.orb:.1f})")

    if chart.patterns:
        parts.append("\nAspect Patterns:")
        for pat in chart.patterns:
            parts.append(f"- {pat.pattern_type}: {', '.join(pat.planets)}")

    parts.append("\nProvide: 1) Personality assessment 2) Strengths/challenges 3) Life themes 4) Relationships 5) Career")
    return "\n".join(parts)


def to_transit_ai_prompt(transit_chart: TransitChart) -> str:
    """Generate AI analysis prompt for transit chart"""
    parts = [
        "Analyze CURRENT TRANSITS to this natal chart:\n",
        f"Transit Date: {transit_chart.transit_data.transit_date.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Birth Date: {transit_chart.natal_chart.birth_data.datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        "Transit-to-Natal Aspects:",
    ]
    for ap in transit_chart.transit_data.transit_to_natal_aspects[:15]:
        a = ap.aspect
        status = "applying" if a.applying else "separating"
        parts.append(f"- {ap.planet1} {a.aspect_type} {ap.planet2} (orb {a.orb:.1f}, {status}, {a.strength:.0f}%)")

    parts.append("\nAnalyze: 1) Current themes 2) Transit-natal dynamics 3) Key activations 4) Opportunities/challenges 5) Timing")
    return "\n".join(parts)


def to_progression_ai_prompt(progressed_chart: ProgressedChart) -> str:
    """Generate AI analysis prompt for progressed chart"""
    birth_dt = progressed_chart.natal_chart.birth_data.datetime_utc
    years = (progressed_chart.progressed_date - birth_dt).days / 365.25

    parts = [
        "Analyze SECONDARY PROGRESSIONS:\n",
        f"Progression Date: {progressed_chart.progressed_date.strftime('%Y-%m-%d')}",
        f"Age: {years:.1f} years\n",
        "Natal vs Progressed:",
    ]
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars"):
        if name in progressed_chart.progressed_planets and name in progressed_chart.natal_chart.planets:
            prog = progressed_chart.progressed_planets[name]
            natal = progressed_chart.natal_chart.planets[name]
            sign_change = " NEW SIGN" if prog.sign != natal.sign else ""
            parts.append(f"- {name}: {natal.degree:.1f} {natal.sign} -> {prog.degree:.1f} {prog.sign}{sign_change}")

    parts.append("\nAnalyze: 1) Internal development 2) Sign changes 3) Long-term themes 4) Maturation")
    return "\n".join(parts)


def to_solar_return_ai_prompt(solar_return: SolarReturnChart) -> str:
    """Generate AI analysis prompt for Solar/Lunar Return"""
    days_diff = abs((solar_return.return_datetime - solar_return.natal_chart.birth_data.datetime_utc).days)
    years_diff = days_diff / 365.25
    is_lunar = abs(years_diff - round(years_diff)) >= 0.1
    chart_type = "LUNAR" if is_lunar else "SOLAR"
    period = "month" if is_lunar else "year"

    parts = [
        f"Analyze this {chart_type} RETURN chart for the {period} ahead:\n",
        f"Return Time: {solar_return.return_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"ASC: {solar_return.return_houses.ascendant:.1f} | MC: {solar_return.return_houses.mc:.1f}\n",
        "Return Planets:",
    ]
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        if name in solar_return.return_planets:
            p = solar_return.return_planets[name]
            retro = " (R)" if p.retrograde else ""
            parts.append(f"- {name}: {p.degree:.1f} {p.sign}, House {p.house}{retro}")

    angular = [f"{n} (H{p.house})" for n, p in solar_return.return_planets.items() if p.house in (1, 4, 7, 10)]
    if angular:
        parts.append(f"\nAngular planets: {', '.join(angular)}")

    parts.append(f"\nAnalyze themes for the {period} ahead.")
    return "\n".join(parts)


def to_fixed_stars_json(fixed_stars_data: Dict[str, Any]) -> str:
    """Export fixed stars data to JSON"""
    export_config = config_loader.load().get("export", {}).get("json", {})
    indent = export_config.get("indent", 2) if export_config.get("pretty_print", True) else None
    return json.dumps(fixed_stars_data, indent=indent, default=str)


def to_fixed_stars_markdown(fixed_stars_data: Dict[str, Any]) -> str:
    """Export fixed stars data to Markdown"""
    lines = ["# Fixed Stars Report\n"]

    if "calculation_date" in fixed_stars_data:
        lines.append(f"**Calculation Date:** {fixed_stars_data['calculation_date']}\n")

    stars = fixed_stars_data.get("stars", [])
    if stars:
        lines.append(f"## Major Fixed Stars ({len(stars)})\n")
        lines.append("| Name | Constellation | Position | Magnitude | Nature | Meaning |")
        lines.append("|------|---------------|----------|-----------|--------|---------|")
        for s in stars:
            lines.append(
                f"| {s['traditional_name']} | {s['constellation']} | {s['sign']} {s['degree']:.2f} "
                f"| {s['magnitude']} | {s['nature']} | {s['meaning']} |"
            )
        lines.append("")

    clusters = fixed_stars_data.get("clusters", [])
    if clusters:
        lines.append(f"## Star Clusters ({len(clusters)})\n")
        lines.append("| Name | Position | Meaning |")
        lines.append("|------|----------|---------|")
        for c in clusters:
            lines.append(f"| {c['name']} | {c['sign']} {c['degree']:.2f} | {c['meaning']} |")
        lines.append("")

    conjunctions = fixed_stars_data.get("conjunctions", [])
    if conjunctions:
        lines.append(f"## Star-Planet Conjunctions ({len(conjunctions)})\n")
        lines.append("| Planet | Star | Orb | Nature | Meaning |")
        lines.append("|--------|------|-----|--------|---------|")
        for c in conjunctions:
            lines.append(
                f"| {c['planet']} | {c['star_traditional_name']} | {c['orb']:.2f} "
                f"| {c['star_nature']} | {c['star_meaning']} |"
            )
    else:
        lines.append("## Star-Planet Conjunctions\n\nNo significant conjunctions within orb.")

    return "\n".join(lines)


def to_fixed_stars_ai_prompt(fixed_stars_data: Dict[str, Any]) -> str:
    """Generate AI analysis prompt for fixed stars"""
    parts = ["Analyze FIXED STARS in this natal chart:\n"]

    conjunctions = fixed_stars_data.get("conjunctions", [])
    if conjunctions:
        parts.append(f"Star-Planet Conjunctions ({len(conjunctions)}):")
        for c in conjunctions:
            parts.append(
                f"- {c['planet']} conjunct {c['star_traditional_name']} "
                f"({c['star_constellation']}, orb {c['orb']:.2f}, nature: {c['star_nature']})"
            )
            parts.append(f"  Meaning: {c['star_meaning']}")
    else:
        parts.append("No significant star-planet conjunctions found.")

    parts.append("\nAnalyze: 1) Destiny/fate themes 2) Karmic patterns 3) Life path impact")
    return "\n".join(parts)
