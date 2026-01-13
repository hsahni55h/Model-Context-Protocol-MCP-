import streamlit as st
from src.helper import extract_text_from_pdf, ask_openai
from src.job_api import fetch_linkedin_jobs

st.set_page_config(page_title="Job Recommender", layout="wide")
st.title("📄 AI Job Recommender")
st.markdown("Upload your resume and get LinkedIn job recommendations based on your skills.")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    # 1. Extract resume text
    with st.spinner("Extracting text from your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)
        resume_text = resume_text[:12000]  # Prevent token overflow

    # 2. AI Resume Summary
    with st.spinner("Summarizing your resume..."):
        summary = ask_openai(
            f"Summarize this resume highlighting the skills, education, and experience:\n\n{resume_text}",
            max_tokens=500
        )

    # 3. Skill Gaps
    with st.spinner("Finding skill gaps..."):
        gaps = ask_openai(
            f"Analyze this resume and highlight missing skills, certifications, and experiences:\n\n{resume_text}",
            max_tokens=400
        )

    # 4. Career Roadmap
    with st.spinner("Creating future roadmap..."):
        roadmap = ask_openai(
            f"Based on this resume, suggest a future career roadmap:\n\n{resume_text}",
            max_tokens=400
        )

    # 5. Display Results
    st.markdown("---")
    st.header("📑 Resume Summary")
    st.markdown(
        f"<div style='background-color:#000;padding:15px;border-radius:10px;color:white;'>{summary}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.header("🛠️ Skill Gaps")
    st.markdown(
        f"<div style='background-color:#000;padding:15px;border-radius:10px;color:white;'>{gaps}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.header("🚀 Career Roadmap")
    st.markdown(
        f"<div style='background-color:#000;padding:15px;border-radius:10px;color:white;'>{roadmap}</div>",
        unsafe_allow_html=True
    )

    st.success("✅ Resume analysis completed!")

    # 6. Job Recommendations
    if st.button("🔎 Get LinkedIn Job Recommendations"):
        with st.spinner("Generating job keywords..."):
            keywords = ask_openai(
                "Return only 5–7 job titles as a comma-separated list. No explanation.\n\n"
                f"Resume Summary:\n{summary}",
                max_tokens=100
            )

            search_keywords_clean = keywords.replace("\n", "").strip()

            # Use only the FIRST recommended job title
            primary_job_title = search_keywords_clean.split(",")[0].strip()

        st.success(f"AI Recommended Roles: {search_keywords_clean}")
        st.info(f"Using **{primary_job_title}** as the main job search title")

        # 7. Fetch LinkedIn Jobs
        with st.spinner("Fetching LinkedIn jobs..."):
            linkedin_jobs = fetch_linkedin_jobs(primary_job_title, rows=60)

            if isinstance(linkedin_jobs, dict) and "error" in linkedin_jobs:
                st.error(linkedin_jobs["error"])
                st.stop()

        # 8. Display Jobs
        st.markdown("---")
        st.header("💼 Top LinkedIn Jobs")

        if linkedin_jobs:
            for job in linkedin_jobs[:15]:  # Show only top 15
                st.markdown(f"**{job.get('title')}** at *{job.get('companyName')}*")
                st.markdown(f"- 📍 {job.get('location')}")
                st.markdown(f"- 🔗 [View Job]({job.get('link')})")
                st.markdown("---")
        else:
            st.warning("No LinkedIn jobs found.")
