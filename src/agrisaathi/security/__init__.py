"""
agrisaathi.security
=====================
Defense-in-depth security/safety layer: prompt-injection detection, unsafe
agrochemical-advice filtering, PII-redacted audit logging, and per-user
rate limiting. See docs/SECURITY.md for the full threat model.
"""

from .audit_log import log_event, read_recent_events
from .guardrails import (
    after_model_guardrail,
    before_model_guardrail,
    contains_unsafe_dosage_advice,
    detect_prompt_injection,
    redact_pii,
)
from .rate_limiter import RateLimitExceeded, allow_request, before_agent_rate_limiter

__all__ = [
    "log_event",
    "read_recent_events",
    "before_model_guardrail",
    "after_model_guardrail",
    "detect_prompt_injection",
    "contains_unsafe_dosage_advice",
    "redact_pii",
    "allow_request",
    "before_agent_rate_limiter",
    "RateLimitExceeded",
]
