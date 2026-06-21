"""
agrisaathi.skills
==================
Modular "agent skills": small, independently testable, pure-Python
capabilities that are wrapped as ADK FunctionTools and attached to one or
more agents. Each skill lives in its own file so it can be developed,
tested, and reused independently of any specific agent.
"""

from .disease_diagnosis_skill import diagnose_crop_problem
from .irrigation_calculator_skill import calculate_irrigation_need
from .price_trend_skill import analyze_price_trend
from .scheme_eligibility_skill import check_scheme_eligibility

__all__ = [
    "diagnose_crop_problem",
    "calculate_irrigation_need",
    "analyze_price_trend",
    "check_scheme_eligibility",
]
