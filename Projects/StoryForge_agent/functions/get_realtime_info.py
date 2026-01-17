import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MODEL_INFO = "gpt-4o-mini"


def get_realtime_info(query: str, max_results: int = 3) -> str:
    """
    Fetch real-time information using Tavily and summarize with OpenAI.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # 1) Fetch sources from Tavily
    try:
        resp = tavily_client.search(query=query, max_results=max_results, topic="general")
        if resp and resp.get("results"):
            summaries = []
            for r in resp["results"]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                summaries.append(f"**{title}**\n\n{snippet}\n\n🔗 {url}")
            source_info = "\n\n---\n\n".join(summaries)
        else:
            source_info = f"No recent updates found on '{query}'."
    except Exception as e:
        source_info = f"Error fetching info from Tavily: {e}"

    # 2) Summarize with OpenAI
    prompt = f"""
You are a professional researcher and content creator.
Write an accurate, engaging, human-like summary for the topic: '{query}'.

Requirements:
- Around 200 words
- Factual, insightful
- Smooth tone
- No greetings or self-references

Source information:
{source_info}

Output only the refined content.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_INFO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=350,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return source_info
