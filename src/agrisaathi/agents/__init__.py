"""
agrisaathi.agents
===================
The multi-agent system: one root orchestrator (LlmAgent) that routes
farmer requests to four specialist sub-agents, each scoped to one domain
and equipped with its own tools (local skills and/or MCP server tools)
and security guardrails.
"""

from .orchestrator import build_orchestrator

__all__ = ["build_orchestrator"]

root_agent = build_orchestrator()
