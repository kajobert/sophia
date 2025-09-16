import sys
import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# This is a hack to ensure the application can find the 'core' and 'agents' modules
# In a real-world scenario, this project should be structured as a proper Python package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint to receive a prompt and return a plan from the PlannerAgent.
    """
    # --- Lazy Loading ---
    # Import the agent here to prevent slow startup and import-time side effects.
    from agents.planner_agent import PlannerAgent

    try:
        # 1. Create a context for the request
        session_id = str(uuid.uuid4())
        context = SharedContext(session_id=session_id, original_prompt=request.prompt)

        # 2. Instantiate and run the PlannerAgent
        planner_agent = PlannerAgent()
        updated_context = planner_agent.run_task(context)

        # 3. Extract the results from the context payload
        plan = updated_context.payload.get('plan', 'No plan generated.')
        ethical_review = updated_context.payload.get('ethical_review', 'No ethical review conducted.')

        return {"plan": plan, "ethical_review": ethical_review}
    except Exception as e:
        # Return a more detailed error message for debugging
        return {"error": f"An error occurred: {str(e)}"}
