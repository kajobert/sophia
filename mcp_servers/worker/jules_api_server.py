import os
import sys
import httpx
import yaml
from fastapi import FastAPI, HTTPException

# Add project root to the Python path
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)
from pydantic import BaseModel
from typing import Optional
import logging

# --- Configuration Loading Function ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Loads the application configuration from the YAML file."""
    config_path = os.path.join("config/config.yaml")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}, using defaults.")
        return {}

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Pydantic Models ---
class DelegationRequest(BaseModel):
    # Required fields
    prompt: str
    source: str
    starting_branch: str
    # Optional fields based on API documentation
    title: Optional[str] = None
    requirePlanApproval: Optional[bool] = None
    automationMode: Optional[str] = None # e.g., "AUTO_CREATE_PR"

# --- API Endpoints ---
@app.get("/list_jules_sources")
async def list_jules_sources():
    """
    Lists all available sources (e.g., GitHub repositories) that Jules can work with.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("list_sources_timeout", 30.0)

    logger.info("Received request to list Jules sources.")
    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        raise HTTPException(status_code=500, detail="JULES_API_KEY is not configured.")

    headers = {"X-Goog-Api-Key": jules_api_key}
    url = f"{base_url}/sources"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Jules API returned an error while listing sources: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Jules API error: {e.response.text}")
    except Exception as e:
        logger.exception("An unexpected error occurred while listing Jules sources.")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delegate_task_to_jules")
async def delegate_task_to_jules(request: DelegationRequest):
    """
    Creates a new session in the Jules API to delegate a task.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("delegate_task_timeout", 45.0)

    logger.info(f"Received request to create Jules session.")

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        logger.error("CRITICAL: JULES_API_KEY environment variable is not set.")
        raise HTTPException(status_code=500, detail="The JULES_API_KEY is not configured.")

    headers = {
        "X-Goog-Api-Key": jules_api_key,
        "Content-Type": "application/json",
    }

    # Dynamically build the payload with required and optional fields
    payload = {
        "prompt": request.prompt,
        "sourceContext": {
            "source": request.source,
            "githubRepoContext": {"startingBranch": request.starting_branch}
        }
    }
    if request.title:
        payload["title"] = request.title
    if request.requirePlanApproval is not None:
        payload["requirePlanApproval"] = request.requirePlanApproval
    if request.automationMode:
        payload["automationMode"] = request.automationMode

    url = f"{base_url}/sessions"
    logger.info(f"Sending request to Jules API at {url} with payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()

            response_data = response.json()
            session_name = response_data.get("name")

            if not session_name:
                logger.error(f"Invalid response from Jules API, missing 'name'. Response: {response_data}")
                raise HTTPException(status_code=502, detail="Invalid response from Jules API: 'name' not found.")

            logger.info(f"Task successfully delegated. Jules API responded with session name: {session_name}")
            return {
                "status": "success",
                "message": "Jules session created successfully.",
                "session_name": session_name
            }
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Could not connect to Jules API: {e}")
        raise HTTPException(status_code=503, detail=f"Service Unavailable: Could not connect to Jules API. Reason: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Jules API returned an error. Status: {e.response.status_code}, Response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Jules API returned an error: {e.response.text}")
    except Exception as e:
        logger.exception("An unexpected error occurred while delegating task to Jules.")
        raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {e}")