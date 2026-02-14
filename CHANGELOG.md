# Changelog

All notable changes to XiNiS Engine will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-14

Initial public release.

### Features

- Natal chart calculation with automatic timezone resolution from coordinates
- Transit calculations against natal chart
- Secondary progressions (1 day = 1 year)
- Solar return chart for a given year
- Lunar return chart near a given date
- Fixed stars positions with planet conjunction detection
- 10 house systems (Placidus, Whole Sign, Koch, Equal, Campanus, Regiomontanus, Porphyry, Morinus, Topocentric, Alcabitius)
- 28+ celestial bodies (planets, nodes, asteroids, extended objects, calculated points)
- 11 aspect types with configurable orbs and per-planet multipliers
- 7 aspect pattern detection (Grand Trine, T-Square, Grand Cross, Yod, Kite, Stellium, Mystic Rectangle)
- Export to JSON, Markdown, and AI-optimized prompt formats
- Multi-house system calculation (pass "all" to get all 10 systems at once)
- Health check endpoint with service verification
- Configuration endpoint exposing available bodies, aspects, and house systems
