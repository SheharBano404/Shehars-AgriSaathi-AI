"""
Agent: MandiPriceAgent
========================
Specialist sub-agent that fetches recent mandi (market) prices via the
Market MCP server (mcp_servers/market_mcp_server.py) and analyzes the
trend with the price_trend_skill to give sell/hold guidance.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from ..skills.price_trend_skill import analyze_price_trend
from ..security.guardrails import after_model_guardrail, before_model_guardrail

DEFAULT_MODEL = "gemini-2.5-flash"

_MARKET_SERVER_MODULE = "agrisaathi.mcp_servers.market_mcp_server"
_REPO_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent)


def _market_mcp_toolset() -> MCPToolset:
    """Build an MCPToolset that launches the market MCP server as a stdio
    subprocess and exposes its tools (get_mandi_prices) to the agent."""
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", _MARKET_SERVER_MODULE],
                env={"PYTHONPATH": _REPO_SRC_DIR},
            ),
            timeout=30,
        )
    )


def build_mandi_price_agent(model: str = DEFAULT_MODEL) -> LlmAgent:
    """Construct the MandiPriceAgent."""
    return LlmAgent(
        name="mandi_price_agent",
        model=model,
        description=(
            "Fetches recent mandi (market) prices via the market MCP server "
            "and advises on sell/hold timing based on the price trend."
        ),
        instruction=(
            "You are MandiPriceAgent inside the AgriSaathi assistant. When "
            "asked about market prices or whether to sell now:\n"
            "1. Call get_mandi_prices (an MCP tool) for the farmer's crop "
            "and market.\n"
            "2. Extract the list of price_pkr_per_40kg values from "
            "price_history (oldest to newest) and call analyze_price_trend "
            "with those prices, the crop, and the market.\n"
            "3. Explain the trend and recommendation in plain language. "
            "Always note this is based on recent data only, not a guarantee "
            "of future prices, and that local mandi prices can vary by "
            "quality grade."
        ),
        tools=[_market_mcp_toolset(), FunctionTool(analyze_price_trend)],
        before_model_callback=before_model_guardrail,
        after_model_callback=after_model_guardrail,
    )
