# Architecture

## Overview

AgriSaathi AI is a **multi-agent farming advisory assistant** built with
Google's [Agent Development Kit (ADK)](https://github.com/google/adk-python).
A single root **orchestrator agent** routes each farmer request to one of
four **specialist sub-agents**, each scoped to one domain and equipped with
its own tools -- some local ("agent skills"), some served live over the
**Model Context Protocol (MCP)** by standalone server processes.

```
                         ┌────────────────────────────┐
                         │   AgriSaathiOrchestrator   │   (root LlmAgent)
                         │  routes by farmer intent   │
                         └──────────────┬─────────────┘
            ┌───────────────┬───────────┼───────────────┬───────────────┐
            ▼               ▼           ▼               ▼               
 ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐ ┌───────────────────┐
 │ CropDoctorAgent  │ │WeatherIrrig. │ │MandiPriceAgent │ │SchemeAdvisorAgent │
 │                  │ │   Agent      │ │                │ │                   │
 │ skill:           │ │ MCP tool:    │ │ MCP tool:      │ │ skill:            │
 │ diagnose_crop_   │ │ get_weather_ │ │ get_mandi_     │ │ check_scheme_     │
 │ problem          │ │ forecast     │ │ prices         │ │ eligibility       │
 │                  │ │ skill:       │ │ skill:         │ │                   │
 │                  │ │ calculate_   │ │ analyze_       │ │                   │
 │                  │ │ irrigation_  │ │ price_trend    │ │                   │
 │                  │ │ need         │ │                │ │                   │
 └──────────────────┘ └──────────────┘ └────────────────┘ └───────────────────┘
                              │                │
                              ▼                ▼
                    ┌──────────────────┐ ┌──────────────────┐
                    │ Weather MCP      │ │ Market MCP       │
                    │ Server (stdio)   │ │ Server (stdio)   │
                    └──────────────────┘ └──────────────────┘

   Every agent call passes through the security layer:
   before_model_callback -> prompt-injection guard
   after_model_callback  -> unsafe agrochemical-dosage filter
   before_agent_callback (root) -> per-user rate limiter
   all guardrail triggers + tool calls -> PII-redacted audit log (JSONL)
```

## Why this design

### 1. Multi-agent system (ADK)
A single monolithic agent with one giant prompt and a dozen tools tends to
mix concerns, makes the system prompt huge, and makes per-domain testing
harder. Splitting into one root **router** agent plus four **specialist**
agents (`src/agrisaathi/agents/`) means:
- Each specialist has a short, focused instruction and only the tools it
  needs (least-privilege by construction).
- New domains (e.g. a future "LivestockAgent") can be added without
  touching existing specialists.
- ADK's built-in LLM-driven transfer mechanism (`sub_agents=[...]`) handles
  routing -- no custom intent classifier needed.

### 2. MCP servers
Two domains (weather, mandi prices) depend on **external, frequently
changing data**. Rather than hard-coding an HTTP call inside the agent
process, that logic lives in standalone MCP servers
(`src/agrisaathi/mcp_servers/`), launched as stdio subprocesses and called
over the Model Context Protocol via ADK's `MCPToolset`. This means:
- The data-fetching logic is reusable by *any* MCP client, not just this
  project (e.g. Claude Desktop or another team's agent could attach to the
  same server).
- Swapping the mock data generator for a real weather/mandi API touches
  exactly one file each, with zero changes to agent code.
- Each MCP server can be deployed, scaled, and rate-limited independently
  of the agent process in a real production setup.

### 3. Agent skills
Pure-Python, independently unit-tested functions in
`src/agrisaathi/skills/` (disease triage, irrigation math, price-trend
analysis, scheme eligibility) are wrapped as ADK `FunctionTool`s. They are
intentionally **rules-based / deterministic** rather than another LLM call,
because:
- Agronomic and financial guidance benefits from explainable, auditable
  logic rather than free-form generation.
- They're trivially testable with plain `pytest` (see `tests/`), with no
  LLM or network dependency.

### 4. Security features
See [SECURITY.md](SECURITY.md) for the full threat model. In short:
prompt-injection detection, an unsafe-chemical-dosage output filter, a
per-user sliding-window rate limiter, and a PII-redacting audit logger --
all wired in as ADK callbacks (`before_model_callback`,
`after_model_callback`, `before_agent_callback`).

## Two ways to run it

| Mode | Entry point | Needs API key? | What it exercises |
|---|---|---|---|
| **Offline demo** | `python scripts/demo_offline.py` | No | Every skill, both MCP server tools, and all four security guardrails, called directly -- proves the whole pipeline works without spending any LLM tokens. |
| **Live chat** | `python -m agrisaathi.app` | Yes (`GOOGLE_API_KEY`) | The real ADK multi-agent system: Gemini-powered routing, tool-calling, and natural-language responses. |

## Directory layout

```
agrisaathi-ai/
├── src/agrisaathi/
│   ├── agents/            # Root orchestrator + 4 specialist LlmAgents
│   ├── skills/             # Local, unit-tested FunctionTools
│   ├── mcp_servers/        # Standalone MCP servers (weather, market)
│   ├── security/           # Guardrails, audit log, rate limiter
│   ├── data/                # Mock knowledge bases (disease KB, schemes)
│   └── app.py               # Live CLI chat entrypoint
├── scripts/demo_offline.py  # No-API-key end-to-end walkthrough
├── tests/                    # pytest unit tests (27 tests, no network/LLM)
├── docs/                      # This file, SECURITY.md, DEMO_SCRIPT.md
└── examples/sample_session.md
```
