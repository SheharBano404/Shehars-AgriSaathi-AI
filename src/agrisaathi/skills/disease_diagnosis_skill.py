"""
Skill: Crop Disease & Pest Diagnosis
-------------------------------------
A self-contained "agent skill" that performs rule-based triage of crop health
problems from a farmer's free-text description of symptoms. It is registered
as an ADK FunctionTool on CropDoctorAgent (see agents/crop_doctor_agent.py).

Design notes (production considerations):
- Deterministic & explainable: matches against a curated knowledge base
  (data/crop_disease_kb.json) instead of relying purely on LLM guesswork,
  which matters for high-stakes agricultural advice.
- Never recommends a specific chemical/pesticide product or dosage -- this
  is enforced again, independently, by the security.guardrails module as a
  defense-in-depth measure (see docs/SECURITY.md).
- Pure function, fully unit-testable without any network or LLM call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "crop_disease_kb.json"


def _load_kb() -> dict[str, list[dict[str, Any]]]:
    with open(_KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def diagnose_crop_problem(crop: str, symptoms: str) -> dict[str, Any]:
    """Diagnose a likely crop disease or pest problem from symptoms.

    Matches the farmer-described symptoms against a curated agronomy
    knowledge base for the given crop and returns the most likely matches
    ranked by how many symptom keywords overlap, along with safe, generic
    remediation advice. This tool never prescribes specific pesticide
    products or dosages -- it always recommends confirming with a local
    agriculture extension officer for chemical treatment decisions.

    Args:
        crop: The crop name, e.g. "wheat", "rice", "cotton", "tomato".
        symptoms: Free-text description of what the farmer is observing,
            e.g. "yellow stripes on the leaves and stunted growth".

    Returns:
        A dictionary with keys:
        - "crop": normalized crop name
        - "matches": list of {disease, severity, confidence, advice,
          recommended_action} sorted by confidence (highest first)
        - "disclaimer": a safety disclaimer string
        If the crop is not in the knowledge base, "matches" is empty and
        "note" explains that a human expert should be consulted directly.
    """
    kb = _load_kb()
    crop_key = crop.strip().lower()
    entries = kb.get(crop_key)

    result: dict[str, Any] = {
        "crop": crop_key,
        "matches": [],
        "disclaimer": (
            "This is general agronomic guidance, not a substitute for an "
            "on-site visit by a certified agriculture extension officer, "
            "especially before applying any chemical treatment."
        ),
    }

    if not entries:
        result["note"] = (
            f"No knowledge base entry for crop '{crop}'. Please consult your "
            "local agriculture extension office directly for this crop."
        )
        return result

    symptom_text = symptoms.lower()
    scored = []
    for entry in entries:
        hits = sum(1 for kw in entry["symptoms"] if kw in symptom_text)
        if hits > 0:
            confidence = round(hits / len(entry["symptoms"]), 2)
            scored.append((confidence, hits, entry))

    scored.sort(key=lambda x: (x[1], x[0]), reverse=True)

    for confidence, _hits, entry in scored[:3]:
        result["matches"].append(
            {
                "disease": entry["disease"],
                "severity": entry["severity"],
                "confidence": confidence,
                "advice": entry["advice"],
                "recommended_action": entry["recommended_action"],
            }
        )

    if not result["matches"]:
        result["note"] = (
            "No close match found for the described symptoms. Please share "
            "more specific details (leaf color, spot shape, affected part) "
            "or consult your local extension officer."
        )

    return result
