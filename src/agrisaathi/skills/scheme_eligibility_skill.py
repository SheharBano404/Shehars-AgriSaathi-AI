"""
Skill: Government Scheme Eligibility Checker
----------------------------------------------
Rules-based eligibility matcher against a curated knowledge base of
agricultural subsidy/loan/insurance/grant schemes (data/agri_schemes.json).

Kept rules-based (rather than LLM free-text generation) so that eligibility
decisions are deterministic, explainable, and auditable -- important for
anything touching financial/government program guidance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "agri_schemes.json"


def _load_schemes() -> list[dict[str, Any]]:
    with open(_SCHEMES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_scheme_eligibility(
    crop: str,
    landholding_acres: float,
    farmer_type: str = "smallholder",
) -> dict[str, Any]:
    """Check which government agriculture schemes a farmer likely qualifies for.

    Args:
        crop: Primary crop grown, e.g. "wheat", "rice", "cotton". Use "any"
            if the farmer grows multiple/other crops.
        landholding_acres: Total land area farmed, in acres.
        farmer_type: One of "smallholder", "tenant", or "owner".

    Returns:
        Dictionary with "eligible_schemes" (list of scheme summaries with
        scheme_id, name, category, benefit, and documents_required) and
        "not_eligible_count" for transparency on how many were filtered out.
    """
    schemes = _load_schemes()
    crop_key = crop.strip().lower()
    farmer_type_key = farmer_type.strip().lower()

    eligible = []
    for scheme in schemes:
        elig = scheme["eligibility"]
        crop_ok = "any" in elig["crops"] or crop_key in elig["crops"] or crop_key == "any"
        land_ok = landholding_acres <= elig["max_landholding_acres"]
        type_ok = farmer_type_key in elig["farmer_type"]

        if crop_ok and land_ok and type_ok:
            eligible.append(
                {
                    "scheme_id": scheme["scheme_id"],
                    "name": scheme["name"],
                    "category": scheme["category"],
                    "description": scheme["description"],
                    "benefit": scheme["benefit"],
                    "documents_required": scheme["documents_required"],
                }
            )

    return {
        "crop": crop_key,
        "landholding_acres": landholding_acres,
        "farmer_type": farmer_type_key,
        "eligible_schemes": eligible,
        "not_eligible_count": len(schemes) - len(eligible),
        "disclaimer": (
            "Final approval depends on verification by the relevant "
            "government department. This is an indicative pre-screening only."
        ),
    }
