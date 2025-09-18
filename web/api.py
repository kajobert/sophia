import sys
import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from unittest.mock import patch

# This is a hack to ensure the application can find the 'core' and 'agents' modules
# In a real-world scenario, this project should be structured as a proper Python package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Conditional Mocking for Test/Development Environment ---
# This block checks the SOPHIA_ENV variable. If it's set to 'test',
# it patches the litellm.completion function to use a mock handler.
# This allows the FastAPI server to run locally for UI development
# without needing a real LLM API key.
if os.getenv('SOPHIA_ENV') == 'test':
    from core.mocks import mock_litellm_completion_handler

    print("--- RUNNING IN TEST MODE: Patching services with mock handlers. ---")

    # We need to patch both the sync and async completion functions
    patcher_completion = patch('litellm.completion', new=mock_litellm_completion_handler)
    patcher_acompletion = patch('litellm.acompletion', new=mock_litellm_completion_handler)

    # Start the patches
    patcher_completion.start()
    patcher_acompletion.start()
    # --- End of mocking block ---

from core.orchestrator import AgentOrchestrator
import logging
from contextlib import asynccontextmanager
from fastapi import Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI app.
    It handles the initialization of the AgentOrchestrator on startup.
    """
    print("--- FastAPI app startup ---")
    try:
        app.state.orchestrator = AgentOrchestrator()
        print("--- AgentOrchestrator initialized successfully ---")
    except Exception as e:
        logging.critical(f"Failed to initialize AgentOrchestrator at startup: {e}", exc_info=True)
        app.state.orchestrator = None
    yield
    print("--- FastAPI app shutdown ---")
    app.state.orchestrator = None

app = FastAPI(lifespan=lifespan)

# Allow all origins for simplicity, as the frontend will be a local file.
# In a production environment, this should be restricted to the actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ChatRequest(BaseModel):
    prompt: str

@app.get("/", response_class=FileResponse)
async def read_index():
    return "web/ui/index.html"


@app.post("/chat")
async def chat(request: Request):
    """
    Endpoint to receive a prompt, run the full agent orchestration,
    and return a structured response.
    """
    orchestrator = request.app.state.orchestrator
    if not orchestrator:
        return {"error": "The agent orchestrator is not available due to an initialization error."}

    try:
        chat_request_data = await request.json()
        prompt = chat_request_data.get('prompt')
        if not prompt:
            return {"error": "Prompt is missing from request body."}

        final_context = await orchestrator.run_orchestration(prompt)

        # Return a structured success response with the full payload
        return {
            "status": "success",
            "message": "Orchestration completed.",
            "session_id": final_context.session_id,
            "final_context": final_context.payload
        }
    except Exception as e:
        logging.error(f"An error occurred during chat orchestration: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Tento řádek připojí celý adresář a umožní např. budoucí načítání stylů
app.mount("/", StaticFiles(directory="web/ui"), name="ui")