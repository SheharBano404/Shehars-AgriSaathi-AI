import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agrisaathi.skills.disease_diagnosis_skill import diagnose_crop_problem
from agrisaathi.skills.irrigation_calculator_skill import calculate_irrigation_need


def test_diagnose_known_disease_matches():
    result = diagnose_crop_problem("wheat", "I see yellow stripes on the leaves")
    assert result["crop"] == "wheat"
    assert len(result["matches"]) >= 1
    assert result["matches"][0]["disease"] == "Yellow Rust (Stripe Rust)"


def test_diagnose_unknown_crop_returns_empty_matches():
    result = diagnose_crop_problem("dragonfruit", "spots everywhere")
    assert result["matches"] == []
    assert "note" in result


def test_diagnose_never_includes_dosage_language():
    result = diagnose_crop_problem("cotton", "leaf curling and thickened veins")
    for match in result["matches"]:
        assert "ml of" not in match["advice"].lower()
        assert "mg of" not in match["advice"].lower()


def test_irrigation_zero_need_when_rainfall_exceeds_requirement():
    result = calculate_irrigation_need(
        crop="wheat",
        field_area_acres=5,
        reference_et0_mm_per_day=2.0,
        expected_rainfall_mm=999,
        days_until_next_irrigation=7,
    )
    assert result["net_irrigation_depth_mm"] == 0.0
    assert result["estimated_volume_liters"] == 0.0


def test_irrigation_unknown_crop_uses_default_coefficient():
    result = calculate_irrigation_need(
        crop="dragonfruit",
        field_area_acres=1,
        reference_et0_mm_per_day=5.0,
        expected_rainfall_mm=0,
        days_until_next_irrigation=1,
    )
    assert result["crop_coefficient_used"] == 1.0


def test_irrigation_volume_calculation_is_consistent():
    result = calculate_irrigation_need(
        crop="wheat",
        field_area_acres=1,
        reference_et0_mm_per_day=4.0,
        expected_rainfall_mm=0,
        days_until_next_irrigation=1,
    )
    expected_mm = 1.15 * 4.0 * 1
    assert result["crop_water_requirement_mm"] == round(expected_mm, 1)
    expected_liters = expected_mm * 4046.86
    assert abs(result["estimated_volume_liters"] - round(expected_liters, 0)) < 1
