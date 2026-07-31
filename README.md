# Model Context Protocol (MCP) — Learning & Projects

A hands-on repository for learning the **Model Context Protocol (MCP)** — the open standard
that lets AI models call external tools, read data sources, and interact with services
through a unified interface.

The repo is organized as a progressive curriculum (`learning/`) plus real-world example
projects (`examples/`), all sharing a single Python environment managed by **uv**.

```
.
├── learning/                  # Step-by-step MCP tutorials
│   ├── 01-mcp-basics/         # Core client ↔ server over STDIO
│   ├── 02-langchain-adapters/ # Simplify clients with LangChain MCP Adapters
│   ├── 03-multi-server/       # One agent, many servers
│   ├── 04-docker/             # Containerized MCP server
│   └── 05-sse-transport/      # SSE (HTTP) transport
├── examples/                  # Complete MCP server projects
│   ├── weather/               # Multi-tool weather server (no API key)
│   ├── job-search/            # LinkedIn job search + Streamlit UI
│   └── medical-tools/         # Symptom → diagnosis → PubMed pipeline
├── pyproject.toml             # Mono-repo deps (uv)
└── .env.example               # Required API keys
```

---

## Quick Start

### Prerequisites

| Tool | Purpose |
|------|---------|
| **Python ≥ 3.11** | Runtime |
| **[uv](https://docs.astral.sh/uv/)** | Package & environment manager |
| **OpenAI API key** | LLM calls (all clients use GPT-4o-mini) |

### Setup

```bash
# 1. Clone
git clone https://github.com/hsahni55h/Model-Context-Protocol-MCP-.git
cd Model-Context-Protocol-MCP-

# 2. Create .env from template
cp .env.example .env
# Edit .env and add your keys (OPENAI_API_KEY is required for all modules)

# 3. Install core dependencies
uv sync

# 4. Install all optional dependency groups at once
uv sync --all-extras

# Or install only what you need:
# uv sync --extra langchain      # for 02-langchain, 03-multi-server
# uv sync --extra sse            # for 05-sse-transport
# uv sync --extra clinisight     # for examples/medical-tools
# uv sync --extra jobs           # for examples/job-search
```

---

## Learning Path

Work through these modules in order. Each has its own README with architecture
diagrams, code walkthroughs, and run instructions.

| # | Module | What You Learn |
|---|--------|---------------|
| 01 | [**MCP Basics**](learning/01-mcp-basics/) | Build an MCP server (terminal commands) and a raw client using OpenAI function calling over STDIO transport |
| 02 | [**LangChain Adapters**](learning/02-langchain-adapters/) | Replace ~240 lines of boilerplate with ~80 lines using `langchain-mcp-adapters` |
| 03 | [**Multi-Server**](learning/03-multi-server/) | Connect one LangChain agent to multiple MCP servers via a JSON config file |
| 04 | [**Docker**](learning/04-docker/) | Run an MCP server inside a Docker container for isolation and portability |
| 05 | [**SSE Transport**](learning/05-sse-transport/) | Replace STDIO with SSE — run MCP as a persistent HTTP service with Server-Sent Events |

---

## Example Projects

Complete MCP server projects that demonstrate real-world patterns.
Each includes a Streamlit web UI (where applicable) and can be tested with the MCP Inspector.

| Project | Description | APIs Used |
|---------|-------------|-----------|
| [**Weather**](examples/weather/) | Multi-tool server with `check_weather`, `get_forecast`, and a `weather://favorites` resource | [wttr.in](https://wttr.in) (free, no key) |
| [**Job Search**](examples/job-search/) | Resume analysis + LinkedIn job scraping with Streamlit UI | OpenAI, [Apify](https://apify.com) |
| [**Medical Tools**](examples/medical-tools/) | 4-tool pipeline: extract symptoms → diagnose → search PubMed → summarize articles | OpenAI, [PubMed](https://pubmed.ncbi.nlm.nih.gov) (free) |

See the [examples README](examples/README.md) for an overview.

---

## Testing MCP Servers

Every server in this repo can be tested interactively with the **MCP Inspector**:

```bash
# Example: test the weather server
uv run mcp dev examples/weather/server.py

# Example: test the medical-tools server
uv run mcp dev examples/medical-tools/server.py
```

The Inspector opens a browser UI where you can call tools, read resources, and inspect
inputs/outputs — no client code needed.

---

## MCP Concepts

### What is MCP?

**Model Context Protocol** is an open standard that lets AI applications connect to
external systems (APIs, databases, files) through a unified interface.
Think of it as **"USB-C for AI"** — one protocol to connect any model to any tool.

> [Official docs →](https://modelcontextprotocol.io/docs/getting-started/intro)

### Architecture

MCP uses a **client–server** model:

```
┌──────────────────────────────────────────┐
│              MCP Host                    │
│         (AI application)                 │
│                                          │
│  ┌────────────┐    ┌────────────┐        │
│  │ MCP Client │    │ MCP Client │  ...   │
│  └─────┬──────┘    └─────┬──────┘        │
└────────┼─────────────────┼───────────────┘
         │ stdio/SSE       │ stdio/SSE
   ┌─────┴──────┐    ┌─────┴──────┐
   │ MCP Server │    │ MCP Server │
   │  (weather) │    │   (jobs)   │
   └────────────┘    └────────────┘
```

| Component | Role |
|-----------|------|
| **Host** | The AI application (Claude Desktop, Cursor, custom app) that coordinates clients |
| **Client** | Maintains a 1:1 connection to a server; sends tool requests, receives results |
| **Server** | Exposes **tools** (functions), **resources** (read-only data), and **prompts** (templates) |

### Transports

| Transport | How it works | Use case |
|-----------|-------------|----------|
| **STDIO** | Server runs as a subprocess; communicates via stdin/stdout | Local development, single client |
| **SSE** | Server runs as an HTTP service; uses Server-Sent Events for streaming | Remote/multi-client, Docker, production |

> [Architecture docs →](https://modelcontextprotocol.io/docs/learn/architecture)

---

## Tech Stack

- **MCP SDK**: `mcp[cli] >=1.25.0, <2.0.0` (FastMCP)
- **LLM**: OpenAI GPT-4o-mini (via `openai` SDK)
- **Agent framework**: LangChain + LangGraph (modules 02–03)
- **Web UI**: Streamlit (job-search, medical-tools)
- **Package manager**: uv
- **Container**: Docker (module 04, SSE server)

---

## API Keys

| Key | Required for | How to get |
|-----|-------------|------------|
| `OPENAI_API_KEY` | All modules | [platform.openai.com](https://platform.openai.com/api-keys) |
| `APIFY_API_TOKEN` | Job search example | [apify.com](https://console.apify.com/account/integrations) |
| `TAVILY_API_KEY` | (Optional) | [tavily.com](https://tavily.com) |

Add them to your `.env` file (see `.env.example`).

---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

See the [LICENSE](LICENSE) file for the full text and additional disclaimer.
