# Clinisight AI 🩺🤖  
*(Powered by MCP – Model Context Protocol)*

Clinisight AI is an intelligent **medical research and diagnostic agent** designed to assist clinicians, researchers, and healthcare professionals in analyzing symptoms, exploring potential diagnoses, and summarizing relevant medical literature.

Built using **MCP (Model Context Protocol)**, Clinisight AI orchestrates multiple AI and tool-based steps to process complex medical queries with precision, traceability, and explainability.

---

## 🚀 What Clinisight AI Does

Clinisight AI takes a **medical query or symptom description** and:

1. Extracts clinically relevant symptoms  
2. Suggesting possible diagnoses using LLM reasoning  
3. Fetching relevant PubMed articles  
4. Summarizing medical literature   
5. Returning a consolidated response via an API 


---

## 🔄 How the Workflow Operates

1. **User submits a medical query**  
   Example:  
   *“Persistent chest pain, fatigue, and shortness of breath”*

2. **extract_symptoms**  
   - Identifies key medical symptoms  
   - Structures them for downstream processing  

3. **get_diagnosis (LLM)**  
   - Uses medical reasoning prompts  
   - Suggests possible conditions  

4. **fetch_pubmed**  
   - Retrieves relevant peer-reviewed articles  
   - Ensures evidence-based grounding  

5. **summarize_text (LLM)**  
   - Condenses research into concise insights  
   - Highlights findings and treatment options  

6. **FastAPI Endpoint**  
   - Returns the final structured response to the user  

---

## Role of MCP (Model Context Protocol)

MCP enables Clinisight AI to:

- Orchestrate multi-step AI workflows  
- Connect LLMs with medical tools  
- Pass structured context between steps  
- Integrate real-time research sources  
- Build modular, scalable AI agents  

---

## Module details

| Module | Purpose |
|--------|---------|
| `extract_symptoms` | Identify symptoms from user query |
| `get_diagnosis` | Suggest possible diagnoses via LLM |
| `fetch_pubmed` | Retrieve medical research articles |
| `summarize_text` | Summarize medical literature |
| `FastAPI` | Serve responses to clients |

---

## 🔁 High-Level Flow Diagram

```mermaid
flowchart LR
    U((User)) --> Q[Medical Query]

    Q --> S[extract_symptoms]
    S --> L1([LLM])
    P1[/Prompt/] --> L1

    L1 --> D[get_diagnosis]
    D --> P[fetch_pubmed]

    P --> L2([LLM])
    P2[/Prompt/] --> L2

    L2 --> R[summarize_text]
    R --> API[FastAPI Endpoint]

    API --> U
