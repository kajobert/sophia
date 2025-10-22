import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.sophia_chat_core import SophiaChatCore
from backend.websocket import handle_websocket_connection
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server startup initiated...")
    app_state["sophia_chat_core"] = SophiaChatCore()
    logger.info("SophiaChatCore has been successfully initialized.")
    yield
    logger.info("Server shutdown initiated...")
    app_state.clear()
    logger.info("Cleanup complete.")

app = FastAPI(title="Sophia Chat Backend API", version="1.0.0", lifespan=lifespan)

# --- Static File Serving ---
# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, "frontend")
docs_dir = os.path.join(project_root, "docs")

# Mount the 'docs' directory to be accessible under '/docs'
app.mount("/docs", StaticFiles(directory=docs_dir), name="docs")

@app.get("/")
async def read_index():
    """Serves the main chat.html file."""
    return FileResponse(os.path.join(frontend_dir, 'chat.html'))
# --- End of Static File Serving ---


@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for the chat."""
    sophia_chat_core_instance = app_state.get("sophia_chat_core")
    if not sophia_chat_core_instance:
        logger.error("SophiaChatCore not initialized. Closing connection.")
        await websocket.close(code=1011, reason="Server is not ready.")
        return
    
    await handle_websocket_connection(websocket, session_id, sophia_chat_core_instance)
