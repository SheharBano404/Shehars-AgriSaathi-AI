"""
Skill: Mandi (Market) Price Trend Analysis
---------------------------------------------
Pure analytics skill that takes a list of recent price observations
(typically fetched from the Market MCP server) and produces a trend
summary and a plain-language sell/hold suggestion.

Kept separate from the MCP data-fetching tool itself so the analytics
logic is independently unit-testable and reusable regardless of where the
price data comes from (mock server today, real mandi API tomorrow).
"""

from __future__ import annotations

import statistics
from typing import Any


def analyze_price_trend(prices: list[float], crop: str, market: str) -> dict[str, Any]:
    """Analyze a series of recent daily mandi prices and suggest sell timing.

    Args:
        prices: List of recent daily prices (PKR per 40kg / maund or per
            quintal, consistent unit), ordered oldest to newest.
        crop: Crop name, for labeling the response.
        market: Market/mandi name, for labeling the response.

    Returns:
        Dictionary with latest price, period average, percent change over
        the period, simple trend label ("rising"/"falling"/"stable"), and
        a plain-language recommendation.
    """
    if not prices:
        return {
            "crop": crop,
            "market": market,
            "error": "No price data provided.",
        }

    latest = prices[-1]
    average = statistics.mean(prices)
    first = prices[0]
    pct_change = ((latest - first) / first) * 100 if first else 0.0

    if pct_change > 4:
        trend = "rising"
        recommendation = (
            "Prices have been rising. If you can afford to wait a few more "
            "days and have proper storage, holding may fetch a better price. "
            "If storage is limited or quality may degrade, selling a portion "
            "now still locks in the current gain."
        )
    elif pct_change < -4:
        trend = "falling"
        recommendation = (
            "Prices have been falling. If storage costs or spoilage risk are "
            "high, consider selling soon rather than waiting for a rebound."
        )
    else:
        trend = "stable"
        recommendation = (
            "Prices have been relatively stable. Selling now or holding a "
            "few more days should not make a large difference financially."
        )

    return {
        "crop": crop,
        "market": market,
        "latest_price": round(latest, 2),
        "period_average_price": round(average, 2),
        "percent_change_over_period": round(pct_change, 1),
        "trend": trend,
        "recommendation": recommendation,
        "disclaimer": "Based on recent observed prices only; not a guarantee of future prices.",
    }
