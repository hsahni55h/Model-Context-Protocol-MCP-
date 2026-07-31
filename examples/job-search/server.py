"""
Job Search MCP Server

Demonstrates MCP with REST API integration (LinkedIn via Apify) and OpenAI.

Tools:
  - analyze_resume: Extract skills and experience from resume text
  - suggest_job_titles: Generate job search keywords from a resume summary
  - fetch_linkedin_jobs: Search LinkedIn for jobs via Apify

Resources:
  - jobs://supported-locations: List of locations you can search

Required env vars:
  - OPENAI_API_KEY
  - APIFY_API_TOKEN
"""

import os
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from apify_client import ApifyClient

# Resolve .env from repo root (2 levels up from examples/job-search/)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

mcp = FastMCP("job-search")

# --- Clients ---

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_apify = ApifyClient(os.getenv("APIFY_API_TOKEN"))


def _ask_openai(prompt: str, max_tokens: int = 500) -> str:
    """Send a prompt to OpenAI and return the response text."""
    response = _openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# --- Tools ---

@mcp.tool()
def analyze_resume(resume_text: str) -> dict[str, str]:
    """Analyze resume text and return a summary, skill gaps, and career roadmap.

    Args:
        resume_text: The full text content of a resume/CV.
    """
    summary = _ask_openai(
        f"Summarize this resume highlighting the skills, education, and experience:\n\n{resume_text[:8000]}",
        max_tokens=500,
    )
    gaps = _ask_openai(
        f"Analyze this resume and highlight missing skills, certifications, and experiences "
        f"that would make this candidate more competitive:\n\n{resume_text[:8000]}",
        max_tokens=400,
    )
    roadmap = _ask_openai(
        f"Based on this resume, suggest a future career roadmap with concrete next steps:\n\n{resume_text[:8000]}",
        max_tokens=400,
    )
    return {"summary": summary, "skill_gaps": gaps, "career_roadmap": roadmap}


@mcp.tool()
def suggest_job_titles(resume_summary: str) -> str:
    """Generate 5-7 job title keywords to search for, based on a resume summary.

    Args:
        resume_summary: A summary of the candidate's skills and experience.

    Returns:
        Comma-separated list of job titles.
    """
    return _ask_openai(
        "Return only 5-7 job titles as a comma-separated list. No explanation.\n\n"
        f"Resume Summary:\n{resume_summary}",
        max_tokens=100,
    )


@mcp.tool()
def fetch_linkedin_jobs(
    search_query: str,
    location: str = "Sweden",
    rows: int = 10,
) -> dict[str, Any]:
    """Search LinkedIn for job listings matching a query and location.

    Args:
        search_query: Job title or keywords to search for.
        location: Country or city to filter jobs (default: Sweden).
        rows: Number of results to fetch (default: 10, max: 60).
    """
    rows = max(1, min(60, rows))

    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }

    try:
        run = _apify.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        jobs = list(_apify.dataset(run["defaultDatasetId"]).iterate_items())

        # Return only the useful fields
        cleaned = []
        for job in jobs:
            cleaned.append({
                "title": job.get("title", "N/A"),
                "company": job.get("companyName", "N/A"),
                "location": job.get("location", "N/A"),
                "link": job.get("link", ""),
            })

        return {"jobs": cleaned, "count": len(cleaned)}
    except Exception as e:
        return {"error": f"Failed to fetch jobs: {e}"}


# --- Resources ---

@mcp.resource("jobs://supported-locations")
def get_supported_locations() -> str:
    """List of example locations you can use when searching for jobs."""
    locations = [
        "Sweden", "Germany", "United States", "United Kingdom",
        "India", "Canada", "Netherlands", "France", "Australia",
    ]
    return "\n".join(f"- {loc}" for loc in locations)


if __name__ == "__main__":
    mcp.run(transport="stdio")
