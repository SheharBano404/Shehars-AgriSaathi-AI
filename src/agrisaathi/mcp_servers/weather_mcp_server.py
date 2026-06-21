"""
MCP Server: Weather & Irrigation Data
========================================
A standalone MCP (Model Context Protocol) server, run as a separate stdio
subprocess, exposing weather-forecast data as a tool that any MCP-compatible
agent (including our WeatherIrrigationAgent) can call.

Why a separate MCP server instead of a plain in-process function?
- Decouples the data source from the agent process: swapping the mock
  generator below for a real provider (OpenWeatherMap, Open-Meteo,
  Pakistan Meteorological Department feed, etc.) requires changing only
  this one file -- no agent code changes.
- Demonstrates the MCP server pattern required by the capstone: this
  process can be reused by *any* MCP client, not just this project's ADK
  agents (e.g. a different team's agent, or Claude Desktop, could attach
  to it too).

Mock data generation is deterministic (seeded by location+date) so demo
runs are reproducible without needing a live API key or network access.
Swap `_mock_forecast` for a real HTTP call when a weather API key is
available -- the function signature and return shape should stay the same.

Run standalone for manual testing:
    python -m agrisaathi.mcp_servers.weather_mcp_server
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="agrisaathi-weather",
    instructions=(
        "Provides short-range weather forecast data (temperature, rainfall, "
        "humidity, reference evapotranspiration) for a given location, for "
        "use in irrigation planning."
    ),
)


def _seeded_rng(location: str, day_offset: int) -> random.Random:
    seed_str = f"{location.strip().lower()}-{date.today().isoformat()}-{day_offset}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**31)
    return random.Random(seed)


def _mock_forecast_day(location: str, day_offset: int) -> dict[str, Any]:
    """Deterministically generate a plausible-looking daily forecast.

    Replace this with a real API call (e.g. requests.get to a weather
    provider) when network access and an API key are available. Keep the
    return dict shape identical so downstream tools/skills don't need
    changes.
    """
    rng = _seeded_rng(location, day_offset)
    target_date = date.today() + timedelta(days=day_offset)

    temp_c = round(rng.uniform(22, 41), 1)
    humidity_pct = round(rng.uniform(20, 80), 0)
    rainfall_mm = round(max(0.0, rng.gauss(2, 4)), 1)
    # Reference ET0 rises with temperature, falls with humidity -- a crude
    # but directionally sensible mock relationship.
    et0_mm = round(max(2.0, (temp_c - 15) * 0.22 - (humidity_pct - 50) * 0.02), 1)

    return {
        "date": target_date.isoformat(),
        "temperature_celsius": temp_c,
        "humidity_percent": humidity_pct,
        "rainfall_mm": rainfall_mm,
        "reference_et0_mm_per_day": et0_mm,
    }


@mcp.tool()
def get_weather_forecast(location: str, days: int = 7) -> dict[str, Any]:
    """Get a short-range daily weather forecast for a farming location.

    Args:
        location: Town/district/tehsil name, e.g. "Multan", "Sahiwal".
        days: Number of forecast days to return (1-14).

    Returns:
        Dictionary with "location", "forecast" (list of per-day records with
        date, temperature_celsius, humidity_percent, rainfall_mm, and
        reference_et0_mm_per_day), and "total_expected_rainfall_mm" /
        "average_et0_mm_per_day" summary fields useful for irrigation
        planning.
    """
    days = max(1, min(days, 14))
    forecast = [_mock_forecast_day(location, i) for i in range(days)]
    total_rain = round(sum(d["rainfall_mm"] for d in forecast), 1)
    avg_et0 = round(sum(d["reference_et0_mm_per_day"] for d in forecast) / len(forecast), 2)

    return {
        "location": location,
        "forecast": forecast,
        "total_expected_rainfall_mm": total_rain,
        "average_et0_mm_per_day": avg_et0,
        "source": "MOCK_DATA -- replace with a real weather provider for production use",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
