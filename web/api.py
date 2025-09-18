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

    # --- Mock AdvancedMemory to prevent live DB connection during tests ---
    class MockAdvancedMemory:
        def __init__(self, config_path='config.yaml', user_id="sophia"):
            print("--- API Server: MockAdvancedMemory initialized ---")
        async def add_memory(self, content, mem_type, metadata=None):
            print(f"--- API Server: Mocked add_memory called with content: '{content}' ---")
            return "mock_chat_id_api_123"
        def close(self):
            pass

    patcher_memory = patch('memory.advanced_memory.AdvancedMemory', new=MockAdvancedMemory)
    patcher_memory.start()
    # --- End of mocking block ---

# Only import what is absolutely necessary at the module level
from core.orchestrator import AgentOrchestrator
import logging

app = FastAPI()

# Allow all origins for simplicity, as the frontend will be a local file.
# In a production environment, this should be restricted to the actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Singleton Orchestrator Instance ---
# We create one instance of the orchestrator when the app starts.
# This is more efficient than creating it on every request.
try:
    orchestrator = AgentOrchestrator()
except Exception as e:
    logging.critical(f"Failed to initialize AgentOrchestrator at startup: {e}")
    orchestrator = None


class ChatRequest(BaseModel):
    prompt: str

@app.get("/", response_class=FileResponse)
async def read_index():
    return "web/ui/index.html"


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint to receive a prompt, run the full agent orchestration,
    and return a structured response.
    """
    if not orchestrator:
        return {"error": "The agent orchestrator is not available due to an initialization error."}

    try:
        final_context = await orchestrator.route_prompt(request.prompt)

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