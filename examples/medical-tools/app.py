"""
Medical Tools — Streamlit MCP Client

A web UI that chains the medical-tools MCP server pipeline:
  1. Enter symptoms in plain text
  2. Extract structured symptoms (OpenAI NLP)
  3. Get possible diagnoses
  4. Search PubMed for relevant research
  5. Summarize the articles

Usage (from repo root):
    uv run streamlit run examples/medical-tools/app.py
"""

import asyncio
import json
import os
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

st.set_page_config(page_title="Medical Tools MCP Client", layout="wide")
st.title("Medical Research Assistant")
st.markdown(
    "Enter your symptoms below and step through the pipeline: "
    "**Extract → Diagnose → Search → Summarize**"
)

# --- MCP Helper ---

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Connect to the MCP server, call a tool, and return the result."""
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    params = StdioServerParameters(
        command="uv",
        args=["run", "python", server_script],
        env={**os.environ},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text


def run_tool(tool_name: str, arguments: dict) -> str:
    """Synchronous wrapper for calling an MCP tool."""
    return asyncio.run(call_mcp_tool(tool_name, arguments))


# --- Disclaimer ---

with st.expander("⚠️ Medical Disclaimer", expanded=False):
    st.warning(
        "This tool provides **educational medical information only**. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare provider."
    )

# --- Step 1: User Input ---

st.subheader("1. Describe your symptoms")
user_text = st.text_area(
    "Enter how you're feeling in plain language:",
    placeholder="e.g. I've had a terrible headache for 2 days, my neck is stiff, and I feel nauseous...",
    height=100,
)

# --- Step 2: Extract Symptoms ---

if st.button("Extract Symptoms", disabled=not user_text):
    with st.spinner("Calling extract_symptoms..."):
        raw = run_tool("extract_symptoms", {"text": user_text})
        try:
            data = json.loads(raw)
            st.session_state["symptoms"] = data["symptoms"]
        except (json.JSONDecodeError, KeyError):
            st.error(f"Unexpected response: {raw}")
            st.stop()

if "symptoms" in st.session_state:
    symptoms = st.session_state["symptoms"]
    st.success(f"Extracted **{len(symptoms)}** symptoms: {', '.join(symptoms)}")

    # --- Step 3: Diagnose ---

    st.subheader("2. Possible Diagnoses")
    if st.button("Get Diagnosis"):
        with st.spinner("Calling diagnose_symptoms..."):
            diagnosis = run_tool("diagnose_symptoms", {"symptoms": symptoms})
            st.session_state["diagnosis"] = diagnosis

    if "diagnosis" in st.session_state:
        st.markdown(st.session_state["diagnosis"])

        # --- Step 4: Search PubMed ---

        st.subheader("3. Research Articles")
        max_results = st.slider("Number of articles", 1, 10, 3)
        if st.button("Search PubMed"):
            with st.spinner("Calling search_pubmed..."):
                raw = run_tool("search_pubmed", {
                    "query": " ".join(symptoms),
                    "max_results": max_results,
                })
                articles = json.loads(raw)
                st.session_state["articles"] = articles

        if "articles" in st.session_state:
            articles = st.session_state["articles"]
            if not articles:
                st.info("No articles found. Try different search terms.")
            else:
                for i, article in enumerate(articles, 1):
                    with st.expander(f"📄 {article['title'][:100]}", expanded=(i == 1)):
                        st.markdown(f"**PMID:** [{article['pmid']}]({article['url']})")
                        abstract = article.get("abstract", "No abstract available")
                        st.markdown(f"**Abstract:** {abstract[:500]}{'...' if len(abstract) > 500 else ''}")

                # --- Step 5: Summarize ---

                st.subheader("4. Summary")
                if st.button("Summarize Articles"):
                    abstracts = [
                        a["abstract"] for a in articles
                        if a.get("abstract", "").lower() not in {"no abstract available", ""}
                    ]
                    if not abstracts:
                        st.warning("No abstracts available to summarize.")
                    else:
                        with st.spinner("Calling summarize_articles..."):
                            summary = run_tool("summarize_articles", {"abstracts": abstracts})
                            st.session_state["summary"] = summary

                if "summary" in st.session_state:
                    st.markdown(st.session_state["summary"])

# --- Reset ---

st.divider()
if st.button("🔄 Start Over"):
    for key in ["symptoms", "diagnosis", "articles", "summary"]:
        st.session_state.pop(key, None)
    st.rerun()
