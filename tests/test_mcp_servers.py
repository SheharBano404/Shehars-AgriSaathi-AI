import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agrisaathi.mcp_servers.weather_mcp_server import get_weather_forecast
from agrisaathi.mcp_servers.market_mcp_server import get_mandi_prices


def test_weather_forecast_returns_requested_number_of_days():
    result = get_weather_forecast(location="Multan", days=5)
    assert len(result["forecast"]) == 5
    assert result["location"] == "Multan"


def test_weather_forecast_clamps_days_to_valid_range():
    result = get_weather_forecast(location="Multan", days=100)
    assert len(result["forecast"]) == 14
    result2 = get_weather_forecast(location="Multan", days=0)
    assert len(result2["forecast"]) == 1


def test_weather_forecast_is_deterministic_for_same_inputs():
    result1 = get_weather_forecast(location="Lahore", days=3)
    result2 = get_weather_forecast(location="Lahore", days=3)
    assert result1["forecast"] == result2["forecast"]


def test_weather_forecast_differs_across_locations():
    result1 = get_weather_forecast(location="Lahore", days=3)
    result2 = get_weather_forecast(location="Karachi", days=3)
    assert result1["forecast"] != result2["forecast"]


def test_market_prices_returns_requested_number_of_days():
    result = get_mandi_prices(crop="wheat", market="Sahiwal", days=7)
    assert len(result["price_history"]) == 7
    assert result["crop"] == "wheat"
    assert result["market"] == "Sahiwal"


def test_market_prices_clamps_days_to_valid_range():
    result = get_mandi_prices(crop="wheat", market="Sahiwal", days=999)
    assert len(result["price_history"]) == 30


def test_market_prices_are_positive():
    result = get_mandi_prices(crop="cotton", market="Multan", days=10)
    for record in result["price_history"]:
        assert record["price_pkr_per_40kg"] > 0
