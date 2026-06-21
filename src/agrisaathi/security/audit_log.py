"""
Security: Audit Logging
=========================
Structured, append-only JSONL audit log for every guardrail trigger and
every tool invocation made by the agent system. This gives a production
deployment a traceable record for debugging, compliance, and incident
review -- a baseline requirement for any agent system that takes real-world
actions or gives advice with real-world consequences.

All event payloads pass through `redact_pii` before being written, so raw
CNIC numbers / phone numbers never land in the log file even if a user
includes them in a message.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_DIR = Path(os.environ.get("AGRISAATHI_LOG_DIR", Path(__file__).resolve().parent.parent.parent.parent / "logs"))
_LOG_FILE = _LOG_DIR / "audit_log.jsonl"
_lock = threading.Lock()


def _redact_recursive(value: Any) -> Any:
    # Local import to avoid a circular import at module load time.
    from .guardrails import redact_pii

    if isinstance(value, str):
        return redact_pii(value)
    if isinstance(value, dict):
        return {k: _redact_recursive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_recursive(v) for v in value]
    return value


def log_event(event_type: str, payload: dict[str, Any]) -> None:
    """Append a single structured, PII-redacted event to the audit log.

    Args:
        event_type: Dotted event name, e.g. "tool.invoked",
            "guardrail.prompt_injection_blocked".
        payload: Arbitrary JSON-serializable event details.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": _redact_recursive(payload),
    }

    with _lock:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_recent_events(limit: int = 50) -> list[dict[str, Any]]:
    """Read the most recent `limit` audit log events (for debugging/demo)."""
    if not _LOG_FILE.exists():
        return []
    with open(_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-limit:]]
