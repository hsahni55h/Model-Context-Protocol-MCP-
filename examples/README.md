# Examples

Practical MCP integration examples — each demonstrates a different pattern for building tool servers.

| Example | Pattern | MCP Tools | Stack |
|---|---|---|---|
| [`weather/`](weather/) | Minimal single-tool server | `check_weather` | wttr.in API |
| [`job-search/`](job-search/) | MCP + REST API integration | `fetch_linkedin_jobs_tool` | Streamlit, Apify, OpenAI |
| [`medical-tools/`](medical-tools/) | Multi-tool pipeline (chaining) | `clinisight_ai` | FastAPI, PubMed, OpenAI |
| [`story-generator/`](story-generator/) | MCP + external services | `get_realtime_info_mcp`, `generate_video_transcription_mcp` | Streamlit, Tavily, OpenAI |

## Progression

Start with **weather** (simplest possible MCP server) and work up:

1. **weather** — Single tool, no auth, one external API call
2. **job-search** — REST API integration with API keys, Streamlit UI
3. **medical-tools** — Multi-step pipeline (extract → diagnose → fetch articles → summarize)
4. **story-generator** — Multiple tools, real-time web search, content generation

## Running

Each example has its own README with setup instructions. General pattern:

```bash
# Install deps (from repo root)
uv sync --extra <group>

# Run the MCP server with Inspector
uv run mcp dev examples/<name>/server.py

# Or run the web app (if it has one)
uv run streamlit run examples/<name>/app.py
```

## Required API keys

Add to your `.env` file at the repo root:

| Example | Keys needed |
|---|---|
| weather | None |
| job-search | `OPENAI_API_KEY`, `APIFY_API_TOKEN` |
| medical-tools | `OPENAI_API_KEY` |
| story-generator | `OPENAI_API_KEY`, `TAVILY_API_KEY` |
