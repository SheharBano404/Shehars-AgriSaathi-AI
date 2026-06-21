"""
Security: Guardrails
======================
Defense-in-depth safety layer wired into the ADK agents as callbacks.

Implements three independent guardrails, each addressing a different
production risk for a farmer-facing advisory assistant:

1. PromptInjectionGuard (before_model_callback)
   Detects common prompt-injection / jailbreak patterns in the latest user
   turn before it reaches the LLM, and short-circuits the model call with a
   safe refusal if detected.

2. PIIRedactor (used by security.audit_log)
   Redacts CNIC/Aadhaar-like national ID numbers and phone numbers before
   anything is written to persistent logs, so audit logs don't become a
   PII liability.

3. UnsafeAdviceFilter (after_model_callback / after_tool_callback)
   Scans outgoing model/tool text for specific chemical-dosage style
   phrasing (e.g. "spray X ml of <pesticide>") that the system should never
   originate on its own, since incorrect dosage advice for agrochemicals
   can cause real harm. If detected, the response is replaced with a safe
   fallback that redirects the farmer to a certified extension officer.

These are implemented as plain functions compatible with ADK's
before_model_callback / after_model_callback / before_tool_callback /
after_tool_callback hooks, so they can be attached to any LlmAgent.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .audit_log import log_event

# ---------------------------------------------------------------------------
# 1. Prompt injection guard
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    r"ignore (all |any |the |previous |above )*instructions",
    r"disregard (all |any |the |previous |above )*instructions",
    r"you are now (a|an) ",
    r"system prompt",
    r"reveal your (instructions|prompt|system prompt)",
    r"act as (a|an) (?!agronomist|farmer)",  # allow benign role asks
    r"jailbreak",
    r"do anything now",
    r"\bDAN\b",
    r"forget (you are|your role|everything)",
]

_INJECTION_REGEX = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def detect_prompt_injection(text: str) -> bool:
    """Return True if the text matches a known prompt-injection pattern."""
    return bool(_INJECTION_REGEX.search(text or ""))


def before_model_guardrail(callback_context: Any, llm_request: Any) -> Optional[Any]:
    """ADK before_model_callback: block requests containing injection attempts.

    Returns None to let the request proceed normally, or an LlmResponse-like
    object (here, a simple dict the agent layer turns into a safe message)
    to short-circuit the model call entirely.
    """
    try:
        latest_text = _extract_latest_user_text(llm_request)
    except Exception:
        latest_text = ""

    if detect_prompt_injection(latest_text):
        log_event(
            "guardrail.prompt_injection_blocked",
            {"snippet": latest_text[:120]},
        )
        return {
            "blocked": True,
            "reason": "prompt_injection",
            "safe_message": (
                "I can't follow instructions that try to change my role or "
                "reveal internal configuration. I'm AgriSaathi, your farming "
                "assistant -- happy to help with crop, weather, market, or "
                "scheme questions."
            ),
        }
    return None


def _extract_latest_user_text(llm_request: Any) -> str:
    """Best-effort extraction of the latest user message text from an ADK
    LlmRequest object, tolerant of minor SDK version differences."""
    contents = getattr(llm_request, "contents", None) or []
    for content in reversed(contents):
        role = getattr(content, "role", None)
        if role == "user":
            parts = getattr(content, "parts", []) or []
            texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
            if texts:
                return " ".join(texts)
    return ""


# ---------------------------------------------------------------------------
# 2. PII redaction (used by audit_log, see security/audit_log.py)
# ---------------------------------------------------------------------------

_CNIC_PATTERN = re.compile(r"\b\d{5}-?\d{7}-?\d{1}\b")  # Pakistani CNIC format
_PHONE_PATTERN = re.compile(r"\b(?:\+?92|0)?3\d{2}[-\s]?\d{7}\b")  # PK mobile format


def redact_pii(text: str) -> str:
    """Redact CNIC-like and phone-number-like substrings from text."""
    if not text:
        return text
    text = _CNIC_PATTERN.sub("[REDACTED-CNIC]", text)
    text = _PHONE_PATTERN.sub("[REDACTED-PHONE]", text)
    return text


# ---------------------------------------------------------------------------
# 3. Unsafe agrochemical-dosage advice filter
# ---------------------------------------------------------------------------

_DOSAGE_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s?(ml|mg|g|kg|l|litre|liter)s?\s?(of\s)?\s?"
    r"(pesticide|fungicide|herbicide|insecticide|chemical|spray)\b",
    re.IGNORECASE,
)

_SAFE_FALLBACK_ADVICE = (
    "I'm not able to recommend specific chemical products or dosages -- "
    "incorrect amounts can damage your crop or be unsafe to handle. Please "
    "contact your local agriculture extension officer or a licensed "
    "agro-dealer, who can assess your field in person and recommend a safe, "
    "correct treatment."
)


def contains_unsafe_dosage_advice(text: str) -> bool:
    """Return True if text appears to specify a chemical dosage directly."""
    return bool(_DOSAGE_PATTERN.search(text or ""))


def after_model_guardrail(callback_context: Any, llm_response: Any) -> Optional[Any]:
    """ADK after_model_callback: scrub any response containing unsafe
    pesticide/chemical dosage instructions before it reaches the user."""
    try:
        text = _extract_response_text(llm_response)
    except Exception:
        text = ""

    if contains_unsafe_dosage_advice(text):
        log_event("guardrail.unsafe_dosage_blocked", {"snippet": text[:120]})
        return {
            "blocked": True,
            "reason": "unsafe_dosage_advice",
            "safe_message": _SAFE_FALLBACK_ADVICE,
        }
    return None


def _extract_response_text(llm_response: Any) -> str:
    content = getattr(llm_response, "content", None)
    if content is None:
        return ""
    parts = getattr(content, "parts", []) or []
    texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
    return " ".join(texts)
