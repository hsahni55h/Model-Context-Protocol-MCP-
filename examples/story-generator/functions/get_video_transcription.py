import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_SCRIPT = "gpt-4o-mini"


def generate_video_transcription(info_text: str) -> str:
    """
    Turn real-time info into a short video script.
    """
    if not info_text or not info_text.strip():
        raise ValueError("info_text cannot be empty.")

    prompt = f"""
You are a creative scriptwriter.
Turn this information into an engaging short video script
for YouTube Shorts or Instagram Reels.

Requirements:
- 100–120 words
- Strong hook
- Conversational tone
- Clear call to action

{info_text}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_SCRIPT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error generating video script: {e}"
