"""
AgriSaathi CLI application entrypoint.

Live mode (default):
    Requires a Gemini API key (GOOGLE_API_KEY env var, or
    GOOGLE_GENAI_USE_VERTEXAI=1 + Vertex AI credentials -- see ADK docs).
    Runs the full multi-agent ADK system: orchestrator -> specialist
    sub-agents -> local skills / MCP server tools -> Gemini model calls.

Usage:
    export GOOGLE_API_KEY="..."
    python -m agrisaathi.app

For a fully offline walkthrough that doesn't need any API key or network
access, see scripts/demo_offline.py instead, which exercises the same
skills/MCP-tool/security pipeline directly.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agents import build_orchestrator
from .security.rate_limiter import RateLimitExceeded, before_agent_rate_limiter

APP_NAME = "agrisaathi"


def _check_api_key() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY")) or os.environ.get(
        "GOOGLE_GENAI_USE_VERTEXAI"
    ) == "1"


async def _run_chat_loop() -> None:
    if not _check_api_key():
        print(
            "No GOOGLE_API_KEY found in the environment.\n"
            "Set it with:  export GOOGLE_API_KEY='your-gemini-api-key'\n"
            "Get a free key at https://aistudio.google.com/app/apikey\n\n"
            "Alternatively, run `python scripts/demo_offline.py` for a "
            "no-API-key walkthrough of the skills, MCP tools, and security "
            "guardrails.",
            file=sys.stderr,
        )
        sys.exit(1)

    model = os.environ.get("AGRISAATHI_MODEL", "gemini-2.5-flash")
    agent = build_orchestrator(model=model)
    # Attach the rate limiter as a before_agent_callback on the root agent.
    agent.before_agent_callback = before_agent_rate_limiter

    session_service = InMemorySessionService()
    user_id = "cli_user"
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

    print("=" * 60)
    print(" AgriSaathi AI -- your AI farming companion")
    print(" Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 🌾")
            break

        if user_text.lower() in {"quit", "exit"}:
            print("Goodbye! 🌾")
            break
        if not user_text:
            continue

        message = types.Content(role="user", parts=[types.Part(text=user_text)])

        try:
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            print(f"\nAgriSaathi: {part.text}")
        except RateLimitExceeded as e:
            print(f"\nAgriSaathi: {e}")


def main() -> None:
    asyncio.run(_run_chat_loop())


if __name__ == "__main__":
    main()
