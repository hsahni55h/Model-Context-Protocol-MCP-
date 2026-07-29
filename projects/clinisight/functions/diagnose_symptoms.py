import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment/.env")

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"

def get_diagnosis(symptoms: List[str]) -> str:
    if not symptoms:
        return "No clear symptoms detected. Please describe your symptoms in more detail (duration, severity, and any relevant context)."

    prompt = f"""
Symptoms: {", ".join(symptoms)}

Task:
- List 3–5 possible causes (differential diagnosis) in plain language.
- Mention any urgent red flags that would require immediate medical attention.
- Suggest safe next steps (e.g., what information to track, when to see a doctor).
- Do NOT provide a definitive diagnosis or prescribe medication.
""".strip()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a cautious medical information assistant. You provide educational information, not medical diagnosis."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()
