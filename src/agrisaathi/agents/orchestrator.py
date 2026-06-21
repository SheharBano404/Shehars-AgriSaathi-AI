"""
Agent: AgriSaathiOrchestrator (root agent)
=============================================
The root LlmAgent of the multi-agent system. It does not try to answer
specialist questions itself -- instead it routes the farmer's request to
the correct specialist sub_agent (ADK's built-in LLM-driven transfer
mechanism), and handles small talk / greeting / out-of-scope requests
directly.

This is the primary place the "multi-agent system built with ADK" course
concept is demonstrated: one root agent + four specialist sub-agents,
each with its own tools, instructions, and guardrails.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .crop_doctor_agent import build_crop_doctor_agent
from .market_price_agent import build_mandi_price_agent
from .scheme_advisor_agent import build_scheme_advisor_agent
from .weather_irrigation_agent import build_weather_irrigation_agent
from ..security.guardrails import after_model_guardrail, before_model_guardrail

DEFAULT_MODEL = "gemini-2.5-flash"

ROOT_INSTRUCTION = """\
You are AgriSaathi, a friendly AI farming companion for smallholder farmers.
You help with four kinds of requests, each handled by a specialist on your
team:

- crop_doctor_agent: crop disease/pest symptom diagnosis and general
  remediation advice.
- weather_irrigation_agent: weather forecasts and irrigation planning.
- mandi_price_agent: mandi/market price trends and sell/hold advice.
- scheme_advisor_agent: government subsidy/loan/insurance/grant eligibility.

Greet the farmer warmly on first contact and ask what they need help with
if it isn't already clear. For any specific request matching one of the
specialists above, transfer to that specialist rather than answering
yourself. For general chit-chat or questions clearly outside farming (e.g.
politics, personal medical advice, coding help), politely explain you are
a farming assistant and can't help with that topic.

Always communicate in simple, respectful, encouraging language suitable
for a farmer who may not be technical. If the farmer writes in Urdu/Hindi
(or a mix with English, i.e. Roman Urdu), reply in the same style they used.
"""


def build_orchestrator(model: str = DEFAULT_MODEL) -> LlmAgent:
    """Construct the root AgriSaathiOrchestrator agent with all sub-agents.

    Args:
        model: Gemini model id to use for every agent in the system. Can be
            overridden via the AGRISAATHI_MODEL environment variable in
            app.py.
    """
    return LlmAgent(
        name="agrisaathi_orchestrator",
        model=model,
        description="Root routing agent for the AgriSaathi farming assistant.",
        instruction=ROOT_INSTRUCTION,
        sub_agents=[
            build_crop_doctor_agent(model),
            build_weather_irrigation_agent(model),
            build_mandi_price_agent(model),
            build_scheme_advisor_agent(model),
        ],
        before_model_callback=before_model_guardrail,
        after_model_callback=after_model_guardrail,
    )
