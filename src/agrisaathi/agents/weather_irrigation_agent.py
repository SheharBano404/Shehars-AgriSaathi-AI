"""
Agent: WeatherIrrigationAgent
================================
Specialist sub-agent combining a live MCP tool (weather forecast, served by
mcp_servers/weather_mcp_server.py over stdio) with the in-process
irrigation_calculator_skill, to give farmers a weekly irrigation plan.

This is the agent that most directly demonstrates the "MCP servers" course
concept: get_weather_forecast is NOT a local FunctionTool, it is fetched
live over the Model Context Protocol from a separate server process.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from ..skills.irrigation_calculator_skill import calculate_irrigation_need
from ..security.guardrails import after_model_guardrail, before_model_guardrail

DEFAULT_MODEL = "gemini-2.5-flash"

_WEATHER_SERVER_MODULE = "agrisaathi.mcp_servers.weather_mcp_server"
_REPO_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent)


def _weather_mcp_toolset() -> MCPToolset:
    """Build an MCPToolset that launches the weather MCP server as a stdio
    subprocess and exposes its tools (get_weather_forecast) to the agent."""
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", _WEATHER_SERVER_MODULE],
                env={"PYTHONPATH": _REPO_SRC_DIR},
            ),
            timeout=30,
        )
    )


def build_weather_irrigation_agent(model: str = DEFAULT_MODEL) -> LlmAgent:
    """Construct the WeatherIrrigationAgent."""
    return LlmAgent(
        name="weather_irrigation_agent",
        model=model,
        description=(
            "Provides weather forecasts (via the weather MCP server) and "
            "calculates a weekly irrigation plan for a given crop and field "
            "size."
        ),
        instruction=(
            "You are WeatherIrrigationAgent inside the AgriSaathi assistant. "
            "When asked about weather or irrigation:\n"
            "1. Call get_weather_forecast (an MCP tool) for the farmer's "
            "location to get rainfall and reference ET0 data.\n"
            "2. If the farmer also wants an irrigation plan, call "
            "calculate_irrigation_need using the crop, field size, the "
            "average_et0_mm_per_day and total_expected_rainfall_mm from the "
            "forecast.\n"
            "3. Summarize clearly: expected weather for the week, and (if "
            "asked) how much and when to irrigate. Mention this is a "
            "planning estimate, not an exact guarantee."
        ),
        tools=[_weather_mcp_toolset(), FunctionTool(calculate_irrigation_need)],
        before_model_callback=before_model_guardrail,
        after_model_callback=after_model_guardrail,
    )
