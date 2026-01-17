import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment/.env")

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"


def summarize_text(text: str) -> str:
    """
    Summarize a medical abstract in a structured, factual way.
    """
    if not text or not text.strip() or text.strip().lower() in {"no abstract available", "n/a"}:
        return "No abstract text available to summarize."

    prompt = f"""
Summarize the medical abstract below.

Rules:
- Do not add facts not present in the abstract.
- If key details are missing (population, design, outcomes), explicitly say "Not specified".
- Keep it concise and useful for clinicians.

Return the summary in this format:
- **Objective:** ...
- **Methods/Design:** ...
- **Key Findings:** ...
- **Clinical Relevance:** ...
- **Limitations:** ...

Abstract:
{text}
""".strip()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a careful medical research summarizer. You do not hallucinate details."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
