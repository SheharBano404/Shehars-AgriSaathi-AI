"""
Skill: Irrigation Calculator
-----------------------------
Computes a simple, transparent crop water requirement estimate using the
classic crop-coefficient (Kc) x reference evapotranspiration (ET0) method,
combined with recent/forecast rainfall (supplied by the Weather MCP server)
to produce a net irrigation recommendation.

This is intentionally a simplified, explainable model suitable for advisory
use -- not a replacement for a certified agronomist's field-level water
budget, which the tool states explicitly in its output.
"""

from __future__ import annotations

from typing import Any

# Approximate crop coefficients (Kc, mid-season stage) -- illustrative values
# commonly used in FAO-56 style irrigation scheduling guides.
_CROP_KC = {
    "wheat": 1.15,
    "rice": 1.20,
    "cotton": 1.15,
    "tomato": 1.05,
    "sugarcane": 1.25,
    "maize": 1.20,
}

_DEFAULT_KC = 1.0


def calculate_irrigation_need(
    crop: str,
    field_area_acres: float,
    reference_et0_mm_per_day: float,
    expected_rainfall_mm: float,
    days_until_next_irrigation: int = 7,
) -> dict[str, Any]:
    """Estimate net irrigation water requirement for a field over a period.

    Uses crop water requirement = Kc x ET0 x days, then subtracts expected
    rainfall to get a net irrigation depth, and converts that depth to an
    approximate water volume for the given field area.

    Args:
        crop: Crop name, e.g. "wheat", "rice", "cotton".
        field_area_acres: Field size in acres.
        reference_et0_mm_per_day: Reference evapotranspiration in mm/day
            for the period (typically obtained from the weather MCP tool).
        expected_rainfall_mm: Expected/forecast rainfall in mm over the
            same period (typically obtained from the weather MCP tool).
        days_until_next_irrigation: Number of days this estimate should
            cover (default 7, i.e. a weekly irrigation plan).

    Returns:
        Dictionary with crop water requirement (mm), net irrigation depth
        (mm), approximate volume needed in liters and in cubic meters, and
        a human-readable recommendation string.
    """
    kc = _CROP_KC.get(crop.strip().lower(), _DEFAULT_KC)

    crop_water_requirement_mm = kc * reference_et0_mm_per_day * days_until_next_irrigation
    net_irrigation_mm = max(0.0, crop_water_requirement_mm - expected_rainfall_mm)

    # 1 acre = 4046.86 m^2; 1mm depth over 1 m^2 = 1 liter
    area_m2 = field_area_acres * 4046.86
    volume_liters = net_irrigation_mm * area_m2
    volume_m3 = volume_liters / 1000.0

    if net_irrigation_mm <= 2:
        recommendation = (
            "Expected rainfall should cover most crop water needs. "
            "Irrigation can likely be skipped or minimal for this period."
        )
    elif net_irrigation_mm <= 15:
        recommendation = "Light irrigation recommended for this period."
    else:
        recommendation = (
            "Significant irrigation needed -- plan watering in 2 sessions "
            "to reduce runoff and improve absorption."
        )

    return {
        "crop": crop.strip().lower(),
        "crop_coefficient_used": kc,
        "period_days": days_until_next_irrigation,
        "crop_water_requirement_mm": round(crop_water_requirement_mm, 1),
        "expected_rainfall_mm": round(expected_rainfall_mm, 1),
        "net_irrigation_depth_mm": round(net_irrigation_mm, 1),
        "estimated_volume_liters": round(volume_liters, 0),
        "estimated_volume_cubic_meters": round(volume_m3, 2),
        "recommendation": recommendation,
        "disclaimer": (
            "This is a simplified planning estimate. Adjust for soil type, "
            "field slope, and irrigation system efficiency."
        ),
    }
