import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agrisaathi.skills.price_trend_skill import analyze_price_trend
from agrisaathi.skills.scheme_eligibility_skill import check_scheme_eligibility


def test_price_trend_rising():
    result = analyze_price_trend([100, 101, 105, 110, 112], "wheat", "Sahiwal")
    assert result["trend"] == "rising"
    assert result["percent_change_over_period"] > 4


def test_price_trend_falling():
    result = analyze_price_trend([112, 110, 105, 101, 100], "wheat", "Sahiwal")
    assert result["trend"] == "falling"
    assert result["percent_change_over_period"] < -4


def test_price_trend_stable():
    result = analyze_price_trend([100, 101, 99, 100, 101], "wheat", "Sahiwal")
    assert result["trend"] == "stable"


def test_price_trend_empty_list_returns_error():
    result = analyze_price_trend([], "wheat", "Sahiwal")
    assert "error" in result


def test_scheme_eligibility_filters_by_landholding():
    # 30 acres exceeds the 25-acre cap on the tractor loan scheme (owner-only),
    # but should still leave the crop insurance scheme (cap 50 acres) eligible.
    result = check_scheme_eligibility(crop="wheat", landholding_acres=30, farmer_type="owner")
    names = [s["name"] for s in result["eligible_schemes"]]
    assert "Green Tractor & Machinery Loan Scheme" not in names
    assert "Weather-Indexed Crop Insurance" in names


def test_scheme_eligibility_filters_by_farmer_type():
    # Tractor loan scheme requires farmer_type "owner"; a tenant should not qualify.
    result = check_scheme_eligibility(crop="wheat", landholding_acres=5, farmer_type="tenant")
    names = [s["name"] for s in result["eligible_schemes"]]
    assert "Green Tractor & Machinery Loan Scheme" not in names


def test_scheme_eligibility_smallholder_wheat_qualifies_for_seed_program():
    result = check_scheme_eligibility(crop="wheat", landholding_acres=5, farmer_type="smallholder")
    names = [s["name"] for s in result["eligible_schemes"]]
    assert "Kisan Subsidized Seed Program" in names
