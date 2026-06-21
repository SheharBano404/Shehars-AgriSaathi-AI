# 🌾 AgriSaathi AI

**A multi-agent AI farming companion for smallholder farmers** -- built for the
*Kaggle 5-Day AI Agents Intensive Vibe Coding Course With Google* capstone
project, **Agents for Good** track.

> *Saathi* means "companion" in Urdu. AgriSaathi is designed to be a
> trustworthy companion for smallholder farmers in Pakistan and South Asia,
> helping with crop health, irrigation planning, market timing, and
> government scheme eligibility -- in plain language, with safety
> guardrails baked in.

[![Tests](https://img.shields.io/badge/tests-27%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)]()
[![Built with Google ADK](https://img.shields.io/badge/built%20with-Google%20ADK-orange)]()
[![MCP](https://img.shields.io/badge/protocol-MCP-purple)]()

---

## Why this project

Smallholder farmers face four recurring, high-stakes questions every
season: *Is my crop sick? Should I irrigate this week? Should I sell my
harvest now or wait? Am I eligible for any government support?* Getting
these wrong costs money, water, or a whole season's yield. Most existing
"AI farming chatbots" answer with a single generic LLM call and no
safety net around chemical advice. AgriSaathi instead routes each question
to a focused specialist agent backed by deterministic, testable logic and
live (MCP-served) data, with explicit guardrails around the riskiest kind
of advice (chemical dosages).

## Capstone requirements -- how this project demonstrates them

| Required concept | Implementation |
|---|---|
| **Multi-agent systems built with ADK** | One root `LlmAgent` (`agrisaathi_orchestrator`) routes to 4 specialist `LlmAgent` sub-agents (`crop_doctor_agent`, `weather_irrigation_agent`, `mandi_price_agent`, `scheme_advisor_agent`) using ADK's native sub-agent transfer mechanism. See [`src/agrisaathi/agents/`](src/agrisaathi/agents/). |
| **MCP servers** | Two standalone MCP servers (`weather_mcp_server.py`, `market_mcp_server.py`), built with the official `mcp` Python SDK's `FastMCP`, run as stdio subprocesses and consumed via ADK's `MCPToolset`. See [`src/agrisaathi/mcp_servers/`](src/agrisaathi/mcp_servers/). |
| **Agent skills** | Four independently unit-tested, deterministic Python "skills" (disease triage, irrigation calculator, price-trend analysis, scheme eligibility) wrapped as ADK `FunctionTool`s. See [`src/agrisaathi/skills/`](src/agrisaathi/skills/). |
| **Security features** | Prompt-injection detection, an unsafe-chemical-dosage output filter, a per-user rate limiter, and a PII-redacting audit logger, wired in as ADK `before_model_callback` / `after_model_callback` / `before_agent_callback` hooks. See [`src/agrisaathi/security/`](src/agrisaathi/security/) and [`docs/SECURITY.md`](docs/SECURITY.md). |

All four concepts are demonstrated (the brief requires at least three).

## Architecture at a glance

```
   Farmer query
        │
        ▼
┌───────────────────────┐
│ AgriSaathiOrchestrator│  (root agent -- routes by intent)
└─────────┬─────────────┘
   ┌──────┼──────┬──────────────┐
   ▼      ▼      ▼              ▼
CropDoctor  WeatherIrrigation  MandiPrice   SchemeAdvisor
   │             │                │              │
   ▼             ▼                ▼              ▼
local skill   Weather MCP      Market MCP     local skill
              server + skill   server + skill
```

Full diagram and design rationale: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quick start

### Option A -- offline demo (no API key, 10 seconds)

Proves every skill, both MCP server tools, and all four security
guardrails work, without spending any LLM tokens or needing network access:

```bash
git clone https://github.com/SheharBano404/Shehars-AgriSaathi-AI.git
cd shehars-agrisaathi-ai
pip install -r requirements.txt
python scripts/demo_offline.py
```

See a real captured run in [`examples/sample_session.md`](examples/sample_session.md).

### Option B -- full live multi-agent chat (needs a free Gemini API key)

```bash
pip install -r requirements.txt
cp .env.example .env        # then edit .env and add your GOOGLE_API_KEY
export GOOGLE_API_KEY="your-gemini-api-key"   # or: export $(cat .env | xargs)
adk web .
```

Get a free key at https://aistudio.google.com/app/apikey. Example
questions to try are in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

### Run the test suite

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

27 tests, all passing, covering every skill, both MCP server tools, and
every security guardrail -- no network or API key required.

## Project structure

```
agrisaathi-ai/
├── README.md                   <- you are here
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md         # full design rationale
│   ├── SECURITY.md             # threat model & mitigations
│   └── DEMO_SCRIPT.md          # suggested live-demo walkthrough
├── examples/
│   └── sample_session.md       # real captured offline-demo output
├── scripts/
│   └── demo_offline.py         # no-API-key end-to-end walkthrough
├── src/agrisaathi/
│   ├── app.py                  # live CLI chat entrypoint (ADK Runner)
│   ├── agents/                 # root orchestrator + 4 specialist agents
│   ├── skills/                 # local FunctionTools (rules-based, tested)
│   ├── mcp_servers/            # 2 standalone MCP servers (weather, market)
│   ├── security/               # guardrails, audit log, rate limiter
│   └── data/                   # mock knowledge bases (disease KB, schemes)
└── tests/                      # pytest unit tests (27 tests)
```

## Design choices worth highlighting

- **Deterministic mock data, swappable for real APIs in one file each.**
  Both MCP servers generate plausible, *seeded/deterministic* weather and
  mandi-price data so every demo run is reproducible without needing a
  weather API key or live network access during judging. Each server's
  mock generator is isolated behind the same function signature a real API
  call would use, so swapping in OpenWeatherMap / a real mandi price feed
  later is a one-file change (clearly marked with `MOCK_DATA` comments).
- **Rules-based skills, not another LLM call, for high-stakes logic.**
  Disease triage, irrigation math, price-trend direction, and scheme
  eligibility are all deterministic Python functions, not free-form
  generation -- so they're explainable, auditable, and unit-testable
  without any LLM in the loop.
- **The system is structurally unable to originate pesticide dosages.**
  The disease-diagnosis knowledge base never contains a specific chemical
  name/dose, the agent instructions explicitly forbid inventing one, *and*
  an independent output filter (`after_model_callback`) blocks any
  dosage-shaped text regardless of where it came from -- three
  independent layers, not one.
- **Roman Urdu / Urdu / English friendly.** The orchestrator's instruction
  explicitly asks it to reply in whatever language/script mix the farmer
  used, since that's how target users actually write (see the Kaggle
  email that kicked this project off!).

## License

MIT -- see [LICENSE](LICENSE).

## Acknowledgements

Built by **Shehar Bano** for the Kaggle **5-Day AI Agents: Intensive Vibe Coding Course With
Google** capstone project (Agents for Good track), using Google's
[Agent Development Kit](https://google.github.io/adk-docs/) and the
[Model Context Protocol](https://modelcontextprotocol.io/) Python SDK.
