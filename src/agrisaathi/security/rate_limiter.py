"""
Security: Rate Limiting
=========================
A minimal in-memory sliding-window rate limiter, applied as a
before_agent_callback. Protects against runaway cost (every agent turn can
trigger LLM + tool calls) and basic abuse, e.g. a script hammering the
assistant with requests.

For a real production deployment, swap `_WINDOWS` for a shared store
(Redis, Firestore, etc.) so the limit holds across multiple server
instances. The interface (`allow_request`) stays the same.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from .audit_log import log_event

_WINDOWS: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


class RateLimitExceeded(Exception):
    """Raised when a user has exceeded their allotted request rate."""


def allow_request(user_id: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    """Check and record a request against a per-user sliding window limit.

    Args:
        user_id: Stable identifier for the requester (e.g. session/user id).
        max_requests: Maximum number of requests allowed within the window.
        window_seconds: Window size in seconds.

    Returns:
        True if the request is allowed (and is recorded). False if the
        user has exceeded their limit (request is NOT recorded again).
    """
    now = time.monotonic()
    with _lock:
        window = _WINDOWS[user_id]
        while window and now - window[0] > window_seconds:
            window.popleft()

        if len(window) >= max_requests:
            log_event(
                "guardrail.rate_limit_exceeded",
                {"user_id": user_id, "max_requests": max_requests, "window_seconds": window_seconds},
            )
            return False

        window.append(now)
        return True


def before_agent_rate_limiter(callback_context) -> None:  # type: ignore[no-untyped-def]
    """ADK before_agent_callback wrapper around `allow_request`.

    Raises RateLimitExceeded if the calling session has exceeded its quota.
    The orchestrator catches this and returns a friendly message instead of
    propagating the agent run.
    """
    user_id = getattr(callback_context, "user_id", None) or getattr(
        getattr(callback_context, "invocation_context", None), "user_id", "anonymous"
    )
    if not allow_request(str(user_id)):
        raise RateLimitExceeded(
            "You've sent a lot of requests in a short time. Please wait a "
            "minute before trying again."
        )
