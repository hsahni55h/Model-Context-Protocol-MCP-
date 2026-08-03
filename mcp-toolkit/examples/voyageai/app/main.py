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
from app.state import SessionStore

# Global instances
orchestrator = TravelOrchestrator()
session_store = SessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP connections on startup, close on shutdown."""
    await orchestrator.initialize()
    print(f"VoyageAI ready — connected to servers: {orchestrator._mcp_client.server_names}")
    print(f"Available tools: {orchestrator._mcp_client.tool_names}")
    yield
    await orchestrator.close()
    session_store.close()
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
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Handle a chat message from the user.

    Request body: {"message": "...", "session_id": "..."}
    Response: {"response": "...", "session_id": "..."}
    """
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id", "")

    if not user_message:
        return JSONResponse({"response": "Please enter a message."}, status_code=400)

    # Create new session or load existing history
    if not session_id:
        session_id = session_store.create_session()

    history = session_store.load_history(session_id)

    try:
        response = await orchestrator.chat(user_message, history)
        # Persist both messages
        session_store.save_message(session_id, "user", user_message)
        session_store.save_message(session_id, "assistant", response)
        return JSONResponse({"response": response, "session_id": session_id})
    except Exception as e:
        return JSONResponse(
            {"response": f"Sorry, something went wrong: {e}", "session_id": session_id},
            status_code=500,
        )


@app.get("/sessions")
async def list_sessions() -> JSONResponse:
    """List all conversation sessions."""
    return JSONResponse({"sessions": session_store.list_sessions()})


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> JSONResponse:
    """Load conversation history for a session."""
    history = session_store.load_history(session_id)
    return JSONResponse({"session_id": session_id, "history": history})


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> JSONResponse:
    """Delete a conversation session."""
    session_store.delete_session(session_id)
    return JSONResponse({"status": "deleted"})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    connected = orchestrator._mcp_client is not None
    return {
        "status": "ok" if connected else "not_ready",
        "servers": orchestrator._mcp_client.server_names if connected else [],
        "tools": orchestrator._mcp_client.tool_names if connected else [],
    }
