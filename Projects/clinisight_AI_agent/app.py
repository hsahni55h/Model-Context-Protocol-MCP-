from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from functions.symptoms_extractor import extract_symptoms
from functions.diagnose_symptoms import get_diagnosis
from functions.pubmed_articles import fetch_pubmed_articles_with_metadata
from functions.summarize_pubmed import summarize_text  # adjust if your filename differs

app = FastAPI(title="Clinisight AI", version="0.1")


class SymptomInput(BaseModel):
    description: str


@app.post("/diagnosis")
def diagnosis(data: SymptomInput):
    """
    Pipeline:
    1) Extract symptoms from free-text description
    2) Ask LLM for possible causes + next steps
    3) Fetch PubMed articles using symptoms as query
    4) Summarize abstracts using LLM
    5) Return structured response
    """

    # 1) Extract symptoms
    symptoms = extract_symptoms(data.description)

    if not symptoms:
        # Keep it friendly and clear
        raise HTTPException(
            status_code=400,
            detail="No recognizable symptoms found in your description. Please provide more details (e.g., fever, headache, cough, duration, severity)."
        )

    # 2) Diagnosis suggestions (LLM)
    diagnosis_result = get_diagnosis(symptoms)

    # 3) PubMed fetch
    query = " ".join(symptoms)
    articles = fetch_pubmed_articles_with_metadata(query, max_results=3, use_mock_if_empty=True)

    # 4) Prepare text for summarization (extract abstracts + truncate)
    # articles is a list of dicts: {"title","abstract","authors","publication_date","article_url",...}
    abstracts = []
    for a in articles:
        abstract = a.get("abstract", "")
        if abstract and abstract.lower() != "no abstract available":
            abstracts.append(abstract)

    if abstracts:
        combined_abstracts = "\n\n---\n\n".join(abstracts)
        combined_abstracts = combined_abstracts[:3000]  # keep token usage safe
        pubmed_summary = summarize_text(combined_abstracts)
    else:
        pubmed_summary = "No abstracts available to summarize from PubMed results."

    # 5) Return response
    return {
        "symptoms": symptoms,
        "diagnosis": diagnosis_result,
        "pubmed_query": query,
        "pubmed_articles": articles,          # optional but useful for debugging/UI
        "pubmed_summary": pubmed_summary
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
