"""VoyageAI — FastAPI application.

Multi-agent travel planner powered by mcp-toolkit.
Demonstrates: MultiServerClient, multiple transports, OpenAI tool-calling.

Usage:
    cd examples/voyageai
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import PROJECT_ROOT
from app.agents.orchestrator import TravelOrchestrator

# Global orchestrator instance
orchestrator = TravelOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP connections on startup, close on shutdown."""
    await orchestrator.initialize()
    print(f"VoyageAI ready — connected to servers: {orchestrator._mcp_client.server_names}")
    print(f"Available tools: {orchestrator._mcp_client.tool_names}")
    yield
    await orchestrator.close()
    print("VoyageAI shut down.")


app = FastAPI(
    title="VoyageAI",
    description="AI Travel Planner powered by MCP",
    lifespan=lifespan,
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Handle a chat message from the user.

    Request body: {"message": "...", "history": [...]}
    Response: {"response": "..."}
    """
    body = await request.json()
    user_message = body.get("message", "").strip()
    history = body.get("history", [])

    if not user_message:
        return JSONResponse({"response": "Please enter a message."}, status_code=400)

    try:
        response = await orchestrator.chat(user_message, history)
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse(
            {"response": f"Sorry, something went wrong: {e}"},
            status_code=500,
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    connected = orchestrator._mcp_client is not None
    return {
        "status": "ok" if connected else "not_ready",
        "servers": orchestrator._mcp_client.server_names if connected else [],
        "tools": orchestrator._mcp_client.tool_names if connected else [],
    }
