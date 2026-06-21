"""
Agent: SchemeAdvisorAgent
===========================
Specialist sub-agent that screens a farmer's eligibility for government
agriculture subsidy/loan/insurance/grant schemes using the
scheme_eligibility_skill rules engine.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..skills.scheme_eligibility_skill import check_scheme_eligibility
from ..security.guardrails import after_model_guardrail, before_model_guardrail

DEFAULT_MODEL = "gemini-2.5-flash"


def build_scheme_advisor_agent(model: str = DEFAULT_MODEL) -> LlmAgent:
    """Construct the SchemeAdvisorAgent."""
    return LlmAgent(
        name="scheme_advisor_agent",
        model=model,
        description=(
            "Screens which government agriculture schemes (subsidy, loan, "
            "insurance, grant) a farmer likely qualifies for, given crop, "
            "landholding size, and farmer type."
        ),
        instruction=(
            "You are SchemeAdvisorAgent inside the AgriSaathi assistant. "
            "When a farmer asks about government subsidies, loans, "
            "insurance, or grants:\n"
            "1. If you don't already know the farmer's crop, landholding "
            "size in acres, and whether they are a smallholder/tenant/owner, "
            "ask for the missing details first.\n"
            "2. Call check_scheme_eligibility with those details.\n"
            "3. List the eligible schemes with their benefit and required "
            "documents in simple language.\n"
            "4. Always note that final approval depends on verification by "
            "the relevant government department -- this is an indicative "
            "pre-screening only, not a guarantee."
        ),
        tools=[FunctionTool(check_scheme_eligibility)],
        before_model_callback=before_model_guardrail,
        after_model_callback=after_model_guardrail,
    )
