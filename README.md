# Model Context Protocol (MCP) — Toolkit, Learning & Projects

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A complete **MCP ecosystem** — a reusable toolkit you can plug into your projects,
a progressive learning path, and real-world example servers. Built around the
[Model Context Protocol](https://modelcontextprotocol.io/) — the open standard that
lets AI models call external tools, read data sources, and interact with services
through a unified interface.

---

## MCP Toolkit — Plug & Play

> **`mcp-toolkit/`** — Install it, import it, connect any LLM to any MCP server in 3 lines.

```python
from mcp_toolkit.clients import OpenAIMCPClient

async with OpenAIMCPClient(server_script="my_server.py") as client:
    response = await client.chat("What's the weather in Paris?")
```

**What's included:**

| Component | What It Does |
|-----------|-------------|
| `OpenAIMCPClient` | Drop-in OpenAI client with full tool-calling loop |
| `GeminiMCPClient` | Same for Google Gemini |
| `AnthropicMCPClient` | Same for Claude |
| `LangChainMCPClient` | LangChain React agent with auto tool loading |
| `MultiServerClient` | Connect to multiple servers from a config file |
| `mcp_to_openai/gemini/anthropic` | Convert MCP tools to any provider format |
| `connect()` | Transport abstraction — stdio or SSE, one interface |
| `openai_helper` / `load_env` | Server-side utilities for building tools |

```bash
pip install "mcp-toolkit[openai]"     # or [gemini], [anthropic], [langchain], [all]
```

**[→ Full Toolkit Documentation](mcp-toolkit/README.md)**

---

## Why This Repo?

MCP is becoming the standard way AI applications connect to the outside world — used by
Claude Desktop, Cursor, Windsurf, and many other AI tools. But most learning resources
are either too abstract (just docs) or too scattered (random blog posts).

**This repo fixes that.** It provides:

- A **plug-and-play toolkit** (`mcp-toolkit/`) you can install and use immediately
- A **progressive learning path** (5 modules) that builds concepts one at a time
- **Real-world example projects** you can study, run, and extend
- **Every module is tested and working** — not just code snippets, but complete runnable projects
- **Detailed READMEs** in every folder explaining what the code does, how it works, and why

Whether you're an AI engineer exploring MCP for the first time, or a developer who wants
to build tool-using AI agents, this repo gives you everything in one place.

---

## What's Inside

The repo has three main sections:

### `mcp-toolkit/` — Reusable package (install & use)

A standalone Python package with pre-built MCP clients, converters, and utilities.
Fork it, install it, or use it as a dependency in your own projects.

### `learning/` — Step-by-step MCP tutorials

Five modules that progressively teach MCP concepts. Start at 01 and work your way up.
Each module builds on the previous one and introduces exactly one new concept.

### `examples/` — Complete MCP server projects

Three fully working MCP servers that demonstrate real-world patterns — REST API integration,
multi-tool pipelines, web UIs, and more. Use these as reference or starting points for
your own projects.

```
.
├── mcp-toolkit/               # ⭐ Installable package — plug & play
│   ├── src/mcp_toolkit/       # Clients, converters, config, transports
│   ├── examples/              # Quickstart scripts
│   └── tests/                 # Test suite
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

| # | Module | What You Learn | Key Takeaway |
|---|--------|---------------|--------------|
| 01 | [**MCP Basics**](learning/01-mcp-basics/) | Build an MCP server (terminal commands) and a raw client using OpenAI function calling over STDIO transport | Understand the full request/response cycle between client and server |
| 02 | [**LangChain Adapters**](learning/02-langchain-adapters/) | Replace ~240 lines of boilerplate with ~80 lines using `langchain-mcp-adapters` | See how frameworks eliminate manual tool-calling loops |
| 03 | [**Multi-Server**](learning/03-multi-server/) | Connect one LangChain agent to multiple MCP servers via a JSON config file | Learn the pattern real AI apps use (one agent, many tools) |
| 04 | [**Docker**](learning/04-docker/) | Run an MCP server inside a Docker container for isolation and portability | Containerize servers for safe execution and deployment |
| 05 | [**SSE Transport**](learning/05-sse-transport/) | Replace STDIO with SSE — run MCP as a persistent HTTP service | Understand when and why to use network transports over subprocess pipes |

### What each module covers

**Module 01 — MCP Basics:** You build a terminal MCP server that executes shell commands
in a sandboxed workspace, then write a client from scratch using the raw OpenAI SDK.
This teaches you exactly what happens under the hood — tool discovery, function calling,
result parsing — before any framework hides it from you.

**Module 02 — LangChain Adapters:** Same server, but now the client uses
`langchain-mcp-adapters` to handle tool conversion and the agentic loop automatically.
You see the dramatic reduction in code and understand what the adapter does for you.

**Module 03 — Multi-Server:** You connect a single agent to both a terminal server and a
math server simultaneously. The agent decides which server's tools to call based on the
query. This is how production AI apps work — one agent, many capabilities.

**Module 04 — Docker:** You take the terminal server and run it inside a Docker container.
The client communicates with it over STDIO (piped through `docker run`). This teaches
isolation, portability, and the pattern used for untrusted tool execution.

**Module 05 — SSE Transport:** You replace STDIO (subprocess pipes) with SSE (HTTP).
The server runs as a persistent web service, and the client connects over the network.
This is the pattern for remote servers, multi-client setups, and containerized deployments.

---

## Example Projects

Complete MCP server projects that demonstrate real-world patterns.
Each includes a Streamlit web UI (where applicable) and can be tested with the MCP Inspector.

| Project | Description | APIs Used | Complexity |
|---------|-------------|-----------|------------|
| [**Weather**](examples/weather/) | Multi-tool server with `check_weather`, `get_forecast`, and a `weather://favorites` resource | [wttr.in](https://wttr.in) (free, no key) | Beginner |
| [**Job Search**](examples/job-search/) | Resume analysis + LinkedIn job scraping with Streamlit UI | OpenAI, [Apify](https://apify.com) | Intermediate |
| [**Medical Tools**](examples/medical-tools/) | 4-tool pipeline: extract symptoms → diagnose → search PubMed → summarize articles | OpenAI, [PubMed](https://pubmed.ncbi.nlm.nih.gov) (free) | Advanced |

See the [examples README](examples/README.md) for a detailed overview of all three.

### What makes each example interesting

- **Weather** is the simplest — no API keys, two tools, one resource. Start here to see
  the MCP server pattern without any external complexity.
- **Job Search** adds REST API integration (Apify for LinkedIn scraping), PDF parsing
  (resume upload), and a Streamlit web UI as the MCP client.
- **Medical Tools** chains four tools into a pipeline — each tool's output feeds the next.
  It also demonstrates XML parsing (PubMed API), structured NLP (symptom extraction),
  and how to build diagnostic AI workflows.

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

With MCP, an AI model can:
- **Call tools** — execute functions (search the web, query a database, run code)
- **Read resources** — access structured data (files, configs, live data feeds)
- **Use prompts** — invoke reusable prompt templates with parameters

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

| Technology | Role | Where used |
|-----------|------|------------|
| **[MCP SDK](https://github.com/modelcontextprotocol/python-sdk)** (`mcp[cli] >=1.25, <2.0`) | Server & client framework (FastMCP) | All modules |
| **[OpenAI](https://platform.openai.com)** (GPT-4o-mini) | LLM for function calling | All clients |
| **[LangChain](https://python.langchain.com) + [LangGraph](https://langchain-ai.github.io/langgraph/)** | Agent framework with MCP adapters | Modules 02–03 |
| **[Streamlit](https://streamlit.io)** | Web UI for example projects | Job search, medical tools |
| **[Docker](https://www.docker.com)** | Container runtime | Module 04, SSE server |
| **[uv](https://docs.astral.sh/uv/)** | Fast Python package manager | Entire repo |

---

## API Keys

| Key | Required for | How to get |
|-----|-------------|------------|
| `OPENAI_API_KEY` | All modules | [platform.openai.com](https://platform.openai.com/api-keys) |
| `APIFY_API_TOKEN` | Job search example | [apify.com](https://console.apify.com/account/integrations) |
| `TAVILY_API_KEY` | (Optional) | [tavily.com](https://tavily.com) |

Add them to your `.env` file (see `.env.example`).

---

## Acknowledgments

This repository was built as a structured learning resource while studying MCP concepts
and patterns from various courses, tutorials, and the official MCP documentation. The code
has been reorganized, rewritten, and tested to work as a cohesive, progressive curriculum.

Key references:
- [Model Context Protocol — Official Documentation](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)

---

## License

This project is licensed under the [MIT License](LICENSE). You are free to use,
modify, and distribute this code for any purpose.

See the [LICENSE](LICENSE) file for the full text and additional disclaimer.
