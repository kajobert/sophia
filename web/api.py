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

    print("--- RUNNING IN TEST MODE: Patching litellm.completion with mock handler. ---")

    # We need to patch both the sync and async completion functions
    patcher_completion = patch('litellm.completion', new=mock_litellm_completion_handler)
    patcher_acompletion = patch('litellm.acompletion', new=mock_litellm_completion_handler)

    # Start the patches
    patcher_completion.start()
    patcher_acompletion.start()

# Only import what is absolutely necessary at the module level
from core.context import SharedContext

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

class ChatRequest(BaseModel):
    prompt: str

@app.get("/", response_class=FileResponse)
async def read_index():
    return "web/ui/index.html"

from core.llm_config import get_llm
from agents.planner_agent import PlannerAgent

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint to receive a prompt and return a plan from the PlannerAgent.
    """
    try:
        # 1. Create a context for the request
        session_id = str(uuid.uuid4())
        context = SharedContext(session_id=session_id, original_prompt=request.prompt)

        # 2. Instantiate and run the PlannerAgent
        llm_instance = get_llm()
        planner_agent = PlannerAgent(llm=llm_instance)
        updated_context = planner_agent.run_task(context)

        # 3. Extract the results from the context payload
        plan = updated_context.payload.get('plan', 'No plan generated.')
        ethical_review = updated_context.payload.get('ethical_review', 'No ethical review conducted.')

        return {"plan": plan, "ethical_review": ethical_review}
    except Exception as e:
        # Return a more detailed error message for debugging
        return {"error": f"An error occurred: {str(e)}"}

# Tento řádek připojí celý adresář a umožní např. budoucí načítání stylů
app.mount("/", StaticFiles(directory="web/ui"), name="ui")