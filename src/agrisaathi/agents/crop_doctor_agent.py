"""
Agent: CropDoctorAgent
========================
Specialist sub-agent that diagnoses crop disease/pest problems from a
farmer's free-text symptom description, using the disease_diagnosis_skill
tool. Designed to be attached as a sub_agent of the root orchestrator.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..skills.disease_diagnosis_skill import diagnose_crop_problem
from ..security.guardrails import after_model_guardrail, before_model_guardrail

DEFAULT_MODEL = "gemini-2.5-flash"


def build_crop_doctor_agent(model: str = DEFAULT_MODEL) -> LlmAgent:
    """Construct the CropDoctorAgent."""
    return LlmAgent(
        name="crop_doctor_agent",
        model=model,
        description=(
            "Diagnoses likely crop diseases or pests from a farmer's "
            "description of symptoms, and gives safe, general remediation "
            "guidance (never specific chemical dosages)."
        ),
        instruction=(
            "You are CropDoctor, an agronomy triage specialist inside the "
            "AgriSaathi assistant. When a farmer describes a problem with "
            "their crop, call the diagnose_crop_problem tool with the crop "
            "name and the symptom description, then explain the result in "
            "warm, simple, non-technical language. Always:\n"
            "1. State your confidence level honestly (this is triage, not a "
            "lab diagnosis).\n"
            "2. Give the safe general advice from the tool result.\n"
            "3. Recommend visiting/contacting a local agriculture extension "
            "officer for severe cases or before applying any chemical "
            "treatment.\n"
            "4. NEVER invent a specific pesticide product name or dosage "
            "yourself, even if asked directly -- explain that this requires "
            "an in-person assessment."
        ),
        tools=[FunctionTool(diagnose_crop_problem)],
        before_model_callback=before_model_guardrail,
        after_model_callback=after_model_guardrail,
    )
