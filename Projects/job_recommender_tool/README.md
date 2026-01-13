# AI Job Recommender Tool 💼🤖

This project is an AI-powered job recommendation system that analyzes a user’s resume and suggests relevant **LinkedIn job opportunities** based on their skills, experience, and career profile.

It uses:
- **Streamlit** for the user interface  
- **OpenAI** for resume analysis and keyword extraction  
- **Apify (LinkedIn Actor)** for job scraping  
- **MCP (Model Context Protocol)** for exposing job-fetching tools  

---

## What This Project Does

1. User uploads a **PDF resume**
2. The system:
   - Extracts text from the resume  
   - Generates a **summary**
   - Identifies **skill gaps**
   - Creates a **career roadmap**
3. AI generates **job search keywords**
4. The system fetches **LinkedIn job listings**
5. Jobs are displayed with:
   - Title  
   - Company  
   - Location  
   - Direct link  

---


---

## AI Features

The system uses OpenAI to:

- Summarize the resume  
- Identify missing skills  
- Suggest career improvements  
- Generate job search keywords  


---

## Job Data Source

Jobs are fetched from **LinkedIn** using an Apify actor with:
- Location filtering  
- Residential proxies  
- Real-time job scraping  

