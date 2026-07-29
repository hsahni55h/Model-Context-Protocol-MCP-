# StoryForge Agent (Powered by MCP) 🎬✍️

StoryForge Agent is an intelligent AI content creation system built on the  
**MCP (Multi-Context Processing)** framework.

It transforms raw ideas, topics, or keywords into **fully-structured video scripts**  
optimized for storytelling, emotion, tone, and audience engagement. With adaptive learning and real-time context integration, StoryForge produces clear, concise, and captivating scripts in minutes.

---

## 🚀 What StoryForge Does

StoryForge takes a **topic** and turns it into a **professional video script** by:

1. Understanding the topic and user intent  
2. Fetching real-time information from the internet  
3. Applying structured prompts  
4. Generating a complete video script  
5. Preparing the output for video production tools  

---

## 🧠 Core Capabilities

- Topic understanding  
- Real-time information retrieval  
- Prompt-driven storytelling  
- Script generation  

---

## 🔄 How the Workflow Operates

1. **User provides a topic**
2. The first LLM:
   - Understands the topic  
   - Fetches real-time information from the internet  
3. The system applies structured prompts  
4. A second LLM:
   - Generates a full video script  
5. The script is sent to a video platform (e.g., Higgsfield.ai)  


---


## 🔌 MCP Tools Exposed by StoryForge

StoryForge Agent exposes two MCP tools that power the entire workflow:

### get_realtime_info

Fetches **up-to-date information** about a topic using Tavily and summarizes it using OpenAI.


### generate_video_transcription

Uses real-time information to generate an engaging short-form video script.

### Testing the MCP Tools

To test the StoryForge MCP tools using the MCP Inspector:

uv run mcp dev mcp_server.py


---

## 🧩 Role of MCP (Multi-Context Processing)

MCP enables:

- Tool-based interactions  
- Context switching  
- Multi-LLM coordination  
- Real-time data access  
- Modular agent design  

StoryForge uses MCP to:
- Connect LLMs with external tools  
- Pass structured context between steps  


---

## 🔁 High-Level Flow Diagram

```mermaid
flowchart LR
    CC((Content Creator)) --> T{Topic}

    %% First LLM + Tool
    T --> L1([LLM])
    L1 -->|get_realtime_info| NET((Internet))
    NET --> L1

    %% Prompts to first LLM
    P1[/Prompts/] --> L1

    %% Second LLM + Tool
    L1 --> L2([LLM])
    P2[/Prompts/] --> L2
    L2 -->|generate_video_transcription| VS{Video Script}

    %% Final output
    VS --> H[Higgsfield.ai]








