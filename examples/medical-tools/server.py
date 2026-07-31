"""
Medical Tools MCP Server

Demonstrates a multi-tool MCP pipeline for medical information lookup.
Each tool handles one step — an LLM can chain them together or use them
individually.

Tools:
  - extract_symptoms:    Extract symptoms from free-text using OpenAI
  - diagnose_symptoms:   Suggest possible causes and next steps
  - search_pubmed:       Fetch real articles from PubMed (free, no API key)
  - summarize_articles:  Summarize medical abstracts

Resources:
  - medical://disclaimer: Important medical disclaimer

Required env vars:
  - OPENAI_API_KEY
"""

import os
import json
import requests
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from openai import OpenAI

# Resolve .env from repo root (2 levels up from examples/medical-tools/)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

mcp = FastMCP("medical-tools")

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _ask_openai(system: str, prompt: str, max_tokens: int = 400) -> str:
    response = _openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# --- Tools ---

@mcp.tool()
def extract_symptoms(text: str) -> dict[str, Any]:
    """Extract medical symptoms from a free-text description.

    Uses AI to identify symptoms rather than simple keyword matching,
    so it handles natural language like "my head has been killing me"
    or "I can't stop coughing at night".

    Args:
        text: Free-text description of how the patient feels.

    Returns:
        Dict with 'symptoms' list and 'original_text'.
    """
    result = _ask_openai(
        system="You are a medical symptom extractor. Extract symptoms from the text. "
               "Return ONLY a JSON array of symptom strings, nothing else. "
               "Example: [\"headache\", \"fever\", \"nausea\"]",
        prompt=text,
        max_tokens=200,
    )
    # Parse the JSON array from the response
    try:
        symptoms = json.loads(result)
        if not isinstance(symptoms, list):
            symptoms = [result]
    except json.JSONDecodeError:
        # Fallback: split by commas
        symptoms = [s.strip().strip('"') for s in result.split(",")]

    return {"symptoms": symptoms, "original_text": text}


@mcp.tool()
def diagnose_symptoms(symptoms: list[str]) -> str:
    """Suggest possible causes for a list of symptoms.

    Returns possible conditions, red flags, and suggested next steps.
    This is educational information, NOT a medical diagnosis.

    Args:
        symptoms: List of symptom strings (e.g. ["headache", "fever", "stiff neck"]).
    """
    if not symptoms:
        return "No symptoms provided. Please provide a list of symptoms."

    return _ask_openai(
        system="You are a cautious medical information assistant. "
               "You provide educational information, not medical diagnosis. "
               "Always recommend consulting a healthcare professional.",
        prompt=(
            f"Symptoms: {', '.join(symptoms)}\n\n"
            "Task:\n"
            "- List 3-5 possible causes in plain language\n"
            "- Mention any urgent red flags requiring immediate attention\n"
            "- Suggest safe next steps (what to track, when to see a doctor)\n"
            "- Do NOT provide a definitive diagnosis or prescribe medication"
        ),
        max_tokens=500,
    )


@mcp.tool()
def search_pubmed(query: str, max_results: int = 3) -> str:
    """Search PubMed for medical research articles.

    Uses the free NCBI eUtils API — no API key required.
    Returns a JSON array of articles with pmid, title, abstract, and url.

    Args:
        query: Search terms (e.g. "headache fever stiff neck").
        max_results: Number of articles to return (1-10, default 3).
    """
    max_results = max(1, min(10, max_results))
    headers = {"User-Agent": "MCP-Medical-Tools/1.0 (learning project)"}

    # Step 1: Search for article IDs
    search_resp = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
        headers=headers,
        timeout=10,
    )
    search_resp.raise_for_status()
    id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return json.dumps([])

    # Step 2: Fetch article metadata
    fetch_resp = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(id_list), "retmode": "xml"},
        headers=headers,
        timeout=10,
    )
    fetch_resp.raise_for_status()

    soup = BeautifulSoup(fetch_resp.text, "xml")
    articles = []

    for article_xml in soup.find_all("PubmedArticle"):
        pmid_tag = article_xml.find("PMID")
        pmid = pmid_tag.get_text(strip=True) if pmid_tag else None

        title_tag = article_xml.find("ArticleTitle")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        abstract_parts = article_xml.find_all("AbstractText")
        if abstract_parts:
            abstract = " ".join(p.get_text(" ", strip=True) for p in abstract_parts)
        else:
            abstract = "No abstract available"

        articles.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        })

    return json.dumps(articles)


@mcp.tool()
def summarize_articles(abstracts: list[str]) -> str:
    """Summarize one or more medical article abstracts.

    Returns a structured summary with objective, findings, and clinical relevance.

    Args:
        abstracts: List of abstract texts to summarize.
    """
    if not abstracts:
        return "No abstracts provided to summarize."

    # Filter out empty/placeholder abstracts
    valid = [a for a in abstracts if a and a.lower() not in {"no abstract available", "n/a", ""}]
    if not valid:
        return "No valid abstracts to summarize."

    combined = "\n\n---\n\n".join(valid)[:4000]

    return _ask_openai(
        system="You are a careful medical research summarizer. "
               "Only state facts present in the text. Do not hallucinate.",
        prompt=(
            "Summarize these medical abstracts:\n\n"
            f"{combined}\n\n"
            "Format:\n"
            "- **Objective:** ...\n"
            "- **Key Findings:** ...\n"
            "- **Clinical Relevance:** ...\n"
            "- **Limitations:** ..."
        ),
        max_tokens=400,
    )


# --- Resources ---

@mcp.resource("medical://disclaimer")
def get_disclaimer() -> str:
    """Medical disclaimer for this tool."""
    return (
        "DISCLAIMER: This tool provides educational medical information only. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always seek the advice of a qualified healthcare provider with any questions "
        "regarding a medical condition. Never disregard professional medical advice "
        "or delay seeking it because of information from this tool."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
