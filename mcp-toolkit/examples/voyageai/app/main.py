"""VoyageAI — FastAPI application.

Multi-agent travel planner powered by mcp-toolkit.
Demonstrates: MultiServerClient, multiple transports, OpenAI tool-calling.

Development workflow:
    # Terminal 1 — FastAPI backend
    cd examples/voyageai
    uvicorn app.main:app --reload

    # Terminal 2 — Vite dev server (hot-reload, proxies /chat /sessions /health)
    cd examples/voyageai/frontend
    npm install && npm run dev

Production (single server):
    cd examples/voyageai/frontend && npm run build
    cd .. && uvicorn app.main:app
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import PROJECT_ROOT, validate_config
from app.agents.orchestrator import TravelOrchestrator
from app.state import SessionStore

# Global instances
orchestrator = TravelOrchestrator()
session_store = SessionStore()

# React build output — populated by `cd frontend && npm run build`
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP connections on startup, close on shutdown."""
    validate_config()
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

# Mount Vite's hashed asset bundle (only present after `npm run build`)
_assets_dir = FRONTEND_DIST / "assets"
if _assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="frontend-assets")


@app.get("/")
async def home() -> FileResponse:
    """Serve the React SPA.

    Requires the frontend to be built first:
        cd frontend && npm install && npm run build

    During development, run `npm run dev` in frontend/ instead —
    it starts a Vite server on :5173 that proxies API calls here.
    """
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        return JSONResponse(
            {
                "error": "Frontend not built.",
                "fix": "cd frontend && npm install && npm run build",
            },
            status_code=503,
        )
    return FileResponse(str(index))


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
    if not session_store.session_exists(session_id):
        return JSONResponse({"error": "Session not found"}, status_code=404)
    history = session_store.load_history(session_id)
    return JSONResponse({"session_id": session_id, "history": history})


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> JSONResponse:
    """Delete a conversation session."""
    session_store.delete_session(session_id)
    return JSONResponse({"status": "deleted"})


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint. Returns 503 if MCP servers are not connected."""
    connected = orchestrator._mcp_client is not None
    payload = {
        "status": "ok" if connected else "not_ready",
        "servers": orchestrator._mcp_client.server_names if connected else [],
        "tools": orchestrator._mcp_client.tool_names if connected else [],
    }
    return JSONResponse(payload, status_code=200 if connected else 503)
