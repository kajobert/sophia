"""
Sophia Chat Backend Server - FastAPI application.
"""

import logging
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

# Create a global instance of SophiaChatCore
sophia_chat_core = SophiaChatCore()

# Create FastAPI app
app = FastAPI(
    title="Sophia Chat Backend API",
    description="Backend API for Sophia Chat",
    version="1.0.0",
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
    await handle_websocket_connection(websocket, session_id, sophia_chat_core)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
