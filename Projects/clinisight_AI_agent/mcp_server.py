import asyncio
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from functions.symptoms_extractor import extract_symptoms
from functions.diagnose_symptoms import get_diagnosis
from functions.pubmed_articles import fetch_pubmed_articles_with_metadata
from functions.summarize_pubmed import summarize_text

mcp = FastMCP("Clinisight AI")


@mcp.tool()
async def clinisight_ai(symptom_text: str) -> Dict[str, Any]:
    """
    End-to-end Clinisight pipeline:
    1) Extract symptoms from free text
    2) LLM suggests possible causes + next steps
    3) Fetch PubMed articles based on symptoms
    4) Summarize abstracts
    """
    # 1) Extract symptoms
    symptoms: List[str] = extract_symptoms(symptom_text)

    if not symptoms:
        return {
            "symptoms": [],
            "diagnosis": "No recognizable symptoms found. Please provide more detail (duration, severity, and symptoms like fever, headache, cough, etc.).",
            "pubmed_query": "",
            "pubmed_articles": [],
            "pubmed_summary": "No PubMed summary generated because no symptoms were detected."
        }

    # 2) Diagnosis suggestion (blocking → run in thread)
    diagnosis_result = await asyncio.to_thread(get_diagnosis, symptoms)

    # 3) PubMed fetch (blocking → run in thread)
    query = " ".join(symptoms)
    articles = await asyncio.to_thread(fetch_pubmed_articles_with_metadata, query, 3, True)

    # 4) Build a string from abstracts, then summarize
    abstracts = []
    for a in articles:
        abstract = a.get("abstract", "")
        if abstract and abstract.lower() != "no abstract available":
            abstracts.append(abstract)

    if abstracts:
        combined_abstracts = "\n\n---\n\n".join(abstracts)[:3000]
        pubmed_summary = await asyncio.to_thread(summarize_text, combined_abstracts)
    else:
        pubmed_summary = "No abstracts available to summarize from PubMed results."

    return {
        "symptoms": symptoms,
        "diagnosis": diagnosis_result,
        "pubmed_query": query,
        "pubmed_articles": articles,
        "pubmed_summary": pubmed_summary
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
