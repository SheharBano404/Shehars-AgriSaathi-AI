# Security

AgriSaathi gives advice that can affect a farmer's crop, money, and safety
(chemical handling, government scheme applications). The security layer
(`src/agrisaathi/security/`) is designed around that reality, with
defense-in-depth: no single guardrail is trusted alone.

## Threat model & mitigations

| # | Risk | Mitigation | Where |
|---|---|---|---|
| 1 | **Prompt injection** -- a user tries to override the system instruction, exfiltrate the system prompt, or make the assistant impersonate a different identity/policy. | Regex-based pattern detection on the latest user turn, run as an ADK `before_model_callback`. Matches are blocked before reaching the model, with a polite refusal returned instead. | `guardrails.py::before_model_guardrail` |
| 2 | **Unsafe agrochemical advice** -- the assistant (or a manipulated model response) states a specific pesticide/fungicide product name and dosage, which could cause real crop or human harm if wrong. | Output-side pattern filter on every model response (`after_model_callback`), independent of what the disease-diagnosis skill itself returns (which is also written to never include this). Any match is replaced with a safe fallback redirecting to a certified extension officer. | `guardrails.py::after_model_guardrail`, enforced again at the prompt level in `agents/crop_doctor_agent.py` |
| 3 | **PII leakage into logs** -- a farmer might paste their CNIC or phone number into a message; this should never persist in plaintext in audit/debug logs. | All audit log payloads pass through `redact_pii()` before being written to disk. CNIC (Pakistani national ID) and mobile-number patterns are redacted. | `audit_log.py::log_event` (calls `guardrails.redact_pii`) |
| 4 | **Abuse / cost runaway** -- a script or malicious user spamming requests, each of which can trigger multiple LLM + tool calls. | Per-user sliding-window rate limiter (default: 20 requests / 60 seconds), enforced as an ADK `before_agent_callback` on the root agent. Exceeding the limit raises `RateLimitExceeded`, caught by the CLI app and returned as a friendly message -- no agent/LLM call is made. | `rate_limiter.py` |
| 5 | **Untraceable incidents** -- without a record of what happened, debugging a bad response or proving a guardrail fired is impossible. | Every guardrail trigger is written to a structured, append-only JSONL audit log with a timestamp and (redacted) payload. | `audit_log.py` |
| 6 | **Over-broad agent permissions** -- a single agent with every tool increases blast radius if compromised or confused. | Each specialist sub-agent only has the tools relevant to its domain (least privilege by construction of the multi-agent design -- see ARCHITECTURE.md). | `agents/*.py` |
| 7 | **Untrusted external data via MCP** -- a compromised or malicious MCP server could return adversarial tool output (e.g. embedding fresh injection text inside a "weather forecast"). | MCP servers are spawned by this project itself as local stdio subprocesses (not arbitrary remote servers), and their outputs still pass through the same `after_model_callback` output filter before reaching the user, alongside the input-side guard for the *next* turn. | `agents/weather_irrigation_agent.py`, `agents/market_price_agent.py`, `guardrails.py` |

## What this is *not*

This is a capstone-project-scale implementation of these controls, meant to
demonstrate the patterns clearly and be genuinely testable -- not a
substitute for a full production security review. For a real deployment,
you would additionally want:
- A maintained, regularly updated injection-pattern classifier (e.g. a
  small fine-tuned model or a vendor guardrail service) rather than static
  regexes.
- Rate limiting backed by a shared store (Redis/Firestore) instead of
  in-process memory, so limits hold across multiple server instances.
- Structured authentication/authorization if this were exposed as a public
  API rather than a local CLI.
- Encryption at rest for the audit log if it may ever contain sensitive
  agricultural-business data.

## Verifying the guardrails yourself

Every guardrail has a corresponding unit test in `tests/test_security.py`,
and `scripts/demo_offline.py` exercises all four guardrails end-to-end with
no API key required:

```bash
python scripts/demo_offline.py    # see section 5, "Security guardrails"
python -m pytest tests/test_security.py -v
```
