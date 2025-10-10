import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Pydantic model for the request body
class DelegationRequest(BaseModel):
    task_description: str

# Jules API configuration from documentation
JULES_API_URL_V1_ALPHA = "https://jules.googleapis.com/v1alpha"

class DelegationRequest(BaseModel):
    prompt: str
    source: str
    starting_branch: str
    title: str

@app.get("/list_jules_sources")
async def list_jules_sources():
    """
    Lists all available sources (e.g., GitHub repositories) that Jules can work with.
    """
    logger.info("Received request to list Jules sources.")
    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        raise HTTPException(status_code=500, detail="JULES_API_KEY is not configured.")

    headers = {"X-Goog-Api-Key": jules_api_key}
    url = f"{JULES_API_URL_V1_ALPHA}/sources"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
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
    logger.info(f"Received request to create Jules session: '{request.title}'")

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        logger.error("CRITICAL: JULES_API_KEY environment variable is not set.")
        raise HTTPException(status_code=500, detail="The JULES_API_KEY is not configured.")

    headers = {
        "X-Goog-Api-Key": jules_api_key,
        "Content-Type": "application/json",
    }

    # Construct the payload according to the API documentation
    payload = {
        "prompt": request.prompt,
        "sourceContext": {
            "source": request.source,
            "githubRepoContext": {
                "startingBranch": request.starting_branch
            }
        },
        "title": request.title
    }

    url = f"{JULES_API_URL_V1_ALPHA}/sessions"
    logger.info(f"Sending request to Jules API at {url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=45.0)
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
        # Re-raise HTTPException to prevent it from being caught by the generic Exception handler
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