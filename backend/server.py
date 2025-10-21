import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.sophia_chat_core import SophiaChatCore
from backend.websocket import handle_websocket_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# This dictionary will hold our application's state, including the chat core instance.
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager to handle startup and shutdown events.
    This ensures that resources are initialized before the server starts accepting requests.
    """
    # Startup Phase
    logger.info("Server startup initiated...")
    # Create and store the global instance of SophiaChatCore.
    # This will trigger the initialization of DatabaseManager and LLMManager,
    # including the download of the ChromaDB model if it's the first run.
    app_state["sophia_chat_core"] = SophiaChatCore()
    logger.info("SophiaChatCore has been successfully initialized.")

    yield

    # Shutdown Phase
    logger.info("Server shutdown initiated...")
    # Here you could add any cleanup logic if needed, e.g., closing database connections.
    app_state.clear()
    logger.info("Cleanup complete. Server shutting down.")

# Create FastAPI app with the new lifespan manager
app = FastAPI(
    title="Sophia Chat Backend API",
    description="Backend API for Sophia Chat",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "Sophia Chat Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws",
    }

@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for the chat."""
    # Retrieve the initialized instance from the app_state.
    sophia_chat_core_instance = app_state.get("sophia_chat_core")
    if not sophia_chat_core_instance:
        logger.error("SophiaChatCore not initialized. Closing connection.")
        await websocket.close(code=1011, reason="Server is not ready.")
        return

    await handle_websocket_connection(websocket, session_id, sophia_chat_core_instance)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
