"""
Job Search — Streamlit MCP Client

A web UI that connects to the job-search MCP server and exposes its tools
through a visual interface. Upload a PDF resume and the app calls MCP tools
to analyze it, suggest job titles, and fetch LinkedIn listings.

Usage (from repo root):
    uv run streamlit run examples/job-search/app.py
"""

import asyncio
import json
import os
import streamlit as st
import fitz  # PyMuPDF
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Job Search MCP Client", layout="wide")
st.title("Job Search MCP Client")
st.markdown("Upload your resume and use MCP tools to analyze it and find jobs.")

# --- Helpers ---

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from an uploaded PDF."""
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


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


# --- UI ---

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    resume_text = resume_text[:8000]  # Prevent token overflow
    st.success(f"Resume extracted ({len(resume_text)} characters)")

    # --- Analyze Resume ---
    if st.button("Analyze Resume"):
        with st.spinner("Calling analyze_resume tool..."):
            raw = run_tool("analyze_resume", {"resume_text": resume_text})

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                st.error(raw)
                st.stop()

        st.session_state["analysis"] = data

    # Display analysis if available
    if "analysis" in st.session_state:
        data = st.session_state["analysis"]

        st.subheader("Resume Summary")
        st.markdown(data["summary"])

        st.subheader("Skill Gaps")
        st.markdown(data["skill_gaps"])

        st.subheader("Career Roadmap")
        st.markdown(data["career_roadmap"])

        # --- Suggest Job Titles ---
        if st.button("Suggest Job Titles"):
            with st.spinner("Calling suggest_job_titles tool..."):
                titles = run_tool("suggest_job_titles", {"resume_summary": data["summary"]})
            st.session_state["titles"] = titles

    # Display titles if available
    if "titles" in st.session_state:
        st.subheader("Recommended Job Titles")
        st.info(st.session_state["titles"])

        # --- Fetch Jobs ---
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "Search query",
                value=st.session_state["titles"].split(",")[0].strip(),
            )
        with col2:
            location = st.text_input("Location", value="Sweden")

        if st.button("Fetch LinkedIn Jobs"):
            with st.spinner("Calling fetch_linkedin_jobs tool..."):
                raw = run_tool("fetch_linkedin_jobs", {
                    "search_query": search_query,
                    "location": location,
                    "rows": 15,
                })

                try:
                    result = json.loads(raw)
                except json.JSONDecodeError:
                    st.error(raw)
                    st.stop()

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader(f"LinkedIn Jobs ({result['count']} found)")
                for job in result["jobs"]:
                    st.markdown(
                        f"**{job['title']}** at *{job['company']}*  \n"
                        f"Location: {job['location']}  \n"
                        f"[View Job]({job['link']})"
                    )
                    st.divider()
