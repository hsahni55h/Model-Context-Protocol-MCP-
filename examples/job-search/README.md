# Job Search MCP Server

MCP server demonstrating **REST API integration** — connects to OpenAI for resume analysis and LinkedIn (via Apify) for real job listings.

## MCP features demonstrated

| Feature | What it shows |
|---|---|
| **Multi-tool pipeline** | `analyze_resume` -> `suggest_job_titles` -> `fetch_linkedin_jobs` (tools chain naturally) |
| **External API integration** | OpenAI for AI analysis, Apify for LinkedIn scraping |
| **Resources** | `jobs://supported-locations` — reference data for the LLM |

## Tools

| Tool | Description | API used |
|---|---|---|
| `analyze_resume(resume_text)` | Returns summary, skill gaps, and career roadmap | OpenAI |
| `suggest_job_titles(resume_summary)` | Generates 5-7 job title keywords | OpenAI |
| `fetch_linkedin_jobs(query, location, rows)` | Searches LinkedIn for matching jobs | Apify |

## Resources

| URI | Description |
|---|---|
| `jobs://supported-locations` | List of locations you can search |

## Setup

```bash
# Install dependencies (from repo root)
uv sync --extra jobs

# Required env vars in .env
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...
```

Get an Apify API token at [apify.com](https://apify.com) (free tier available).

## Running

### Test with MCP Inspector

```bash
uv run mcp dev examples/job-search/server.py
```

### Run the Streamlit app

The Streamlit app provides a visual UI for uploading a PDF resume and getting job recommendations:

```bash
uv run streamlit run examples/job-search/app.py
```

## Example tool output

```
> analyze_resume("Himanshu Sahni... Master's in Robotics... Python, ML...")
{
  "summary": "Software engineer with Master's in Robotics from Chalmers...",
  "skill_gaps": "Missing cloud certifications, limited production ML experience...",
  "career_roadmap": "1. Get AWS/GCP certification  2. Build production ML pipeline..."
}

> suggest_job_titles("Software engineer with Master's in Robotics...")
Machine Learning Engineer, Robotics Software Engineer, Data Scientist,
AI Researcher, Autonomous Systems Engineer

> fetch_linkedin_jobs("Machine Learning Engineer", location="Sweden", rows=5)
{
  "jobs": [
    {"title": "ML Engineer", "company": "Volvo", "location": "Gothenburg", "link": "..."},
    ...
  ],
  "count": 5
}
```

## File structure

```
job-search/
  server.py           <- MCP server with 3 tools + resource
  app.py              <- Streamlit web UI (standalone, calls APIs directly)
  src/
    helper.py         <- PDF extraction + OpenAI helpers (used by app.py)
    job_api.py        <- Apify LinkedIn scraper (used by app.py)
  test-data/          <- Put your resume PDF here (gitignored)
```
