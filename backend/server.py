"""
Nomad Backend Server - FastAPI application.

This is the main backend server that runs independently of the TUI.
It provides REST API + WebSocket for real-time communication.

Architecture:
- FastAPI for REST endpoints
- WebSocket for real-time streaming
- OrchestratorManager wraps NomadOrchestratorV2
- Singleton pattern for orchestrator instance

Usage:
    # Development
    uvicorn backend.server:app --reload --host 0.0.0.0 --port 8080
    
    # Production
    uvicorn backend.server:app --host 0.0.0.0 --port 8080 --workers 1
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.orchestrator_manager import orchestrator_manager
from backend.websocket import websocket_endpoint
from backend.routes import missions, state, plan, budget, logs, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown.
    
    Handles:
    - Orchestrator initialization on startup
    - Graceful shutdown
    """
    # Startup
    logger.info("🚀 Nomad Backend Server starting...")
    
    try:
        await orchestrator_manager.initialize_orchestrator(
            project_root=".",
            max_tokens=100000,
            max_time_seconds=3600,
        )
        logger.info("✅ Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Nomad Backend Server shutting down...")
    await orchestrator_manager.shutdown()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Nomad Backend API",
    description="Backend API for Nomad AI Agent Orchestrator",
    version="0.9.0",
    lifespan=lifespan,
)

# CORS middleware (allow TUI and Web clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "Nomad Backend API",
        "version": "0.9.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws",
    }


@app.get("/api/v1")
async def api_info():
    """API v1 information."""
    return {
        "version": "v1",
        "endpoints": {
            "missions": "/api/v1/missions",
            "state": "/api/v1/state",
            "plan": "/api/v1/plan",
            "budget": "/api/v1/budget",
            "logs": "/api/v1/logs",
            "health": "/api/v1/health",
        },
        "websocket": "/ws",
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming.
    
    Streams:
    - State updates
    - Log entries
    - LLM thinking
    - Tool execution
    - Plan updates
    - Budget updates
    """
    await websocket_endpoint(websocket)


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(missions.router)
app.include_router(state.router)
app.include_router(plan.router)
app.include_router(budget.router)
app.include_router(logs.router)
app.include_router(health.router)


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        }
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
