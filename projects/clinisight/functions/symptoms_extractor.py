import re
from typing import List

# Add more common symptoms + include multi-word phrases
SYMPTOM_PATTERNS = [
    r"headache",
    r"fever",
    r"nausea",
    r"fatigue",
    r"pain",
    r"cough",
    r"dizziness",
    r"shortness of breath",
    r"chest pain",
    r"sore throat"
]

SYMPTOM_REGEX = re.compile(r"\b(" + "|".join(SYMPTOM_PATTERNS) + r")\b", re.IGNORECASE)

def extract_symptoms(text: str) -> List[str]:
    matches = SYMPTOM_REGEX.findall(text.lower())
    # Deduplicate while preserving order
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out
