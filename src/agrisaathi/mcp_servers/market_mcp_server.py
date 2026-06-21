"""
MCP Server: Mandi (Market) Price Data
========================================
Standalone MCP server exposing recent crop price history for a given
crop/market combination. Mirrors the design rationale in
weather_mcp_server.py: mock data generation is deterministic for reliable
demos, isolated in this single file so a real mandi-price API (e.g. a
state agriculture marketing board feed) can be swapped in later without
touching any agent code.

Run standalone for manual testing:
    python -m agrisaathi.mcp_servers.market_mcp_server
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="agrisaathi-market",
    instructions=(
        "Provides recent daily mandi (wholesale market) price history for "
        "a given crop and market, for use in sell/hold price-trend advice."
    ),
)

# Baseline prices (PKR per 40kg) used as the anchor for the mock random walk.
_BASE_PRICES = {
    "wheat": 3200,
    "rice": 4800,
    "cotton": 8800,
    "tomato": 2600,
    "sugarcane": 850,
    "maize": 2400,
}
_DEFAULT_BASE_PRICE = 3000


def _seeded_rng(crop: str, market: str, day_offset: int) -> random.Random:
    seed_str = f"{crop.strip().lower()}-{market.strip().lower()}-{date.today().isoformat()}-{day_offset}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**31)
    return random.Random(seed)


def _mock_price_series(crop: str, market: str, days: int) -> list[dict[str, Any]]:
    base = _BASE_PRICES.get(crop.strip().lower(), _DEFAULT_BASE_PRICE)
    series = []
    price = base
    for i in range(days):
        rng = _seeded_rng(crop, market, i)
        # Small daily random-walk step, biased slightly by a deterministic
        # "seasonal" sine-like wobble so trends look plausible across runs.
        step_pct = rng.uniform(-0.025, 0.03)
        price = max(1.0, price * (1 + step_pct))
        day = date.today() - timedelta(days=(days - 1 - i))
        series.append({"date": day.isoformat(), "price_pkr_per_40kg": round(price, 0)})
    return series


@mcp.tool()
def get_mandi_prices(crop: str, market: str, days: int = 10) -> dict[str, Any]:
    """Get recent daily mandi (market) prices for a crop at a given market.

    Args:
        crop: Crop name, e.g. "wheat", "rice", "cotton", "tomato".
        market: Mandi/market name, e.g. "Sahiwal", "Multan", "Faisalabad".
        days: Number of most recent days of price history to return (1-30).

    Returns:
        Dictionary with "crop", "market", "currency_unit" (PKR per 40kg),
        and "price_history" (list of {date, price_pkr_per_40kg}, oldest to
        newest).
    """
    days = max(1, min(days, 30))
    history = _mock_price_series(crop, market, days)
    return {
        "crop": crop,
        "market": market,
        "currency_unit": "PKR per 40kg",
        "price_history": history,
        "source": "MOCK_DATA -- replace with a real mandi price feed for production use",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
