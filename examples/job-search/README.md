# Job Search MCP Server

MCP server demonstrating **REST API integration** — connects to OpenAI for AI-powered resume analysis and LinkedIn (via Apify) for real job listings. Includes a Streamlit web app that acts as the MCP client.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Streamlit App (app.py)                             │
│                                                                           │
│  ┌─────────────┐    ┌──────────────────┐    ┌──────────────────────┐     │
│  │ Upload PDF  │───►│ Extract text     │───►│ Call MCP tools       │     │
│  │ (PyMuPDF)   │    │ (fitz)           │    │ (stdio_client)       │     │
│  └─────────────┘    └──────────────────┘    └──────────┬───────────┘     │
└─────────────────────────────────────────────────────────┼─────────────────┘
                                                          │ stdio (JSON-RPC)
                                                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         MCP Server (server.py)                             │
│                                                                           │
│  ┌──────────────────┐  ┌────────────────────┐  ┌───────────────────┐    │
│  │ analyze_resume   │  │ suggest_job_titles  │  │ fetch_linkedin_   │    │
│  │                  │  │                     │  │ jobs              │    │
│  │ (OpenAI API)     │  │ (OpenAI API)        │  │ (Apify API)       │    │
│  └──────────────────┘  └────────────────────┘  └───────────────────┘    │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Resource: jobs://supported-locations                              │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

**Server (`server.py`):** An MCP server with 3 tools + 1 resource. Each tool wraps an external API call (OpenAI or Apify). The server loads API keys from `.env` and exposes the tools over stdio.

**Client (`app.py`):** A Streamlit web application that acts as the MCP client. It spawns the server as a subprocess, connects over stdio, and calls tools sequentially. The UI guides the user through the pipeline: upload resume → analyze → suggest titles → search jobs.

---

## How MCP works here

1. User opens the Streamlit app and uploads a PDF resume
2. The app extracts text from the PDF using PyMuPDF
3. When the user clicks "Analyze Resume", the app:
   - Spawns `server.py` as a subprocess
   - Connects via `stdio_client` (MCP SDK)
   - Sends a `CallToolRequest` for `analyze_resume` with the extracted text
   - Receives structured JSON back (summary, skill gaps, career roadmap)
4. Results are stored in `st.session_state` and passed to the next tool
5. Each subsequent button click opens a new MCP connection and calls the next tool
6. The server is stateless — all context is passed explicitly by the client

**Key pattern:** The Streamlit app is the **orchestrator** — it decides which tool to call and passes context between them. The MCP server just exposes atomic capabilities.

---

## MCP features demonstrated

| Feature | What it shows |
|---|---|
| **Multi-tool pipeline** | `analyze_resume` → `suggest_job_titles` → `fetch_linkedin_jobs` (tools chain naturally) |
| **External API integration** | OpenAI for AI analysis, Apify for LinkedIn job scraping |
| **Resources** | `jobs://supported-locations` — reference data that informs search |
| **Streamlit as MCP client** | Web UI connecting to an MCP server over stdio |
| **Env var handling** | `Path(__file__)` resolves `.env` from repo root regardless of cwd |

---

## Tools

| Tool | Parameters | Returns | API used |
|---|---|---|---|
| `analyze_resume` | `resume_text: str` | JSON: `{summary, skill_gaps, career_roadmap}` | OpenAI |
| `suggest_job_titles` | `resume_summary: str` | Comma-separated job title keywords | OpenAI |
| `fetch_linkedin_jobs` | `search_query: str`, `location: str`, `rows: int = 10` | JSON: `{jobs: [...], count: N}` | Apify |

## Resources

| URI | Description |
|---|---|
| `jobs://supported-locations` | List of valid locations for job search (Sweden, Germany, USA, etc.) |

---

## Setup

```bash
# Install dependencies (from repo root)
uv sync --extra jobs

# Required env vars in .env (at repo root)
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...
```

Get an Apify API token at [apify.com](https://apify.com) (free tier includes 1000 results/month).

---

## Running

### Streamlit app (recommended)

The full pipeline through a visual UI:

```bash
# From repo root
uv run streamlit run examples/job-search/app.py
```

1. Upload your resume PDF
2. Click **Analyze Resume** → see summary, skill gaps, career roadmap
3. Click **Suggest Job Titles** → get AI-generated search keywords
4. Enter location → click **Fetch LinkedIn Jobs** → see real listings with links

### MCP Inspector

Test individual tools directly without the web UI:

```bash
uv run mcp dev examples/job-search/server.py
```

### Programmatic client (Python)

```python
import asyncio, os, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv", args=["run", "python", "examples/job-search/server.py"],
        env={**os.environ}  # Required for API key access
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Analyze a resume
            result = await session.call_tool("analyze_resume", {
                "resume_text": "Himanshu Sahni, Master's in Robotics..."
            })
            data = json.loads(result.content[0].text)
            print(data["summary"])

            # Suggest job titles based on the summary
            result = await session.call_tool("suggest_job_titles", {
                "resume_summary": data["summary"]
            })
            print(result.content[0].text)

asyncio.run(main())
```

---

## Example tool output

```
> analyze_resume("Himanshu Sahni... Master's in Robotics... Python, ML, ROS...")
{
  "summary": "Software engineer with Master's in Robotics from Chalmers University.
              Strong Python/ML background with ROS experience...",
  "skill_gaps": "Missing cloud certifications (AWS/GCP), limited production ML
                 deployment experience, no Kubernetes...",
  "career_roadmap": "1. Get AWS/GCP ML certification\n2. Build production ML
                     pipeline project\n3. Contribute to open-source robotics..."
}

> suggest_job_titles("Software engineer with Master's in Robotics...")
Machine Learning Engineer, Robotics Software Engineer, Data Scientist,
AI Researcher, Autonomous Systems Engineer, Computer Vision Engineer

> fetch_linkedin_jobs("Machine Learning Engineer", location="Sweden", rows=3)
{
  "jobs": [
    {"title": "ML Engineer", "company": "Volvo", "location": "Gothenburg", "link": "https://..."},
    {"title": "Senior ML Engineer", "company": "Spotify", "location": "Stockholm", "link": "https://..."},
    {"title": "AI/ML Specialist", "company": "Ericsson", "location": "Lund", "link": "https://..."}
  ],
  "count": 3
}
```

---

## File structure

```
job-search/
  server.py      ← MCP server with 3 tools + 1 resource
  app.py         ← Streamlit web UI (MCP client)
  README.md
  test-data/     ← Put your resume PDF here (gitignored)
```

---

## Key takeaways

- **Separation of concerns:** The server only exposes tools — the client (Streamlit app) handles UI and orchestration
- **`env={**os.environ}`** is critical when spawning MCP servers as subprocesses — without it the child process can't reach external APIs
- **`Path(__file__)`** resolves the `.env` path relative to the script, so it works from any working directory (MCP Inspector, Streamlit, tests)
- **Stateless tools:** Each tool call is independent. The client stores context in `st.session_state` and passes it explicitly to the next tool
- **Real APIs:** This example calls real external services (OpenAI, Apify/LinkedIn) — you'll see actual results
