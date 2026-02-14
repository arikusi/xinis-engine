# XiNiS Engine

Professional astrology calculation API powered by Swiss Ephemeris. Natal charts, transits, progressions, and solar/lunar returns with arc-second precision across 10 house systems.

Free and open source under GPL v2.0.

## Features

- Swiss Ephemeris precision (arc-second accuracy)
- 10 house systems (Placidus, Whole Sign, Koch, Equal, and 6 more)
- 28+ celestial bodies (planets, nodes, asteroids, calculated points)
- 11 aspect types with configurable orbs
- 7 aspect patterns (Grand Trine, T-Square, Yod, Stellium, etc.)
- Automatic timezone resolution from coordinates
- Fixed stars with conjunction detection
- Export as JSON, Markdown, or AI-optimized prompt

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
docker compose up -d
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/natal-chart` | Natal chart (accepts local datetime) |
| POST | `/transits` | Transits to natal chart |
| POST | `/progressions` | Secondary progressions |
| POST | `/solar-return` | Solar return chart |
| POST | `/lunar-return` | Lunar return chart |
| POST | `/fixed-stars` | Fixed stars and conjunctions |
| POST | `/export` | Export chart (JSON/Markdown/AI) |
| GET | `/config` | Available configuration |
| GET | `/health` | Health check |

### Example

```bash
curl -X POST http://localhost:8000/natal-chart \
  -H "Content-Type: application/json" \
  -d '{
    "local_datetime": "1990-06-15T14:30:00",
    "latitude": 41.0082,
    "longitude": 28.9784,
    "location_name": "Istanbul, Turkey"
  }'
```

The API accepts local datetime and resolves the timezone from coordinates automatically.

Full API documentation: [llms-full.txt](llms-full.txt) | Interactive docs: `/docs` (Swagger UI)

## Tech Stack

- Python 3.11+ / FastAPI
- Swiss Ephemeris via pyswisseph
- Pydantic for validation
- TimezoneFinder for timezone resolution
- Docker for deployment

## Swiss Ephemeris Notice

This project uses the Swiss Ephemeris library by Astrodienst AG. The backend is distributed under GPL v2.0 in compliance with Swiss Ephemeris copyleft requirements. See [astro.com/swisseph](https://www.astro.com/swisseph/) for details.

## License

[GPL v2.0](LICENSE)
