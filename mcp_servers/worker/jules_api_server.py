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
JULES_API_URL = "https://jules.googleapis.com/v1/sessions"

@app.post("/delegate_task_to_jules")
async def delegate_task_to_jules(request: DelegationRequest):
    """
    Delegates a complex task to the external Jules API.

    This tool sends a task specification to the Jules API and returns a session ID
    to track the asynchronous operation.
    """
    logger.info(f"Received request to delegate task: '{request.task_description[:50]}...'")

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        logger.error("CRITICAL: JULES_API_KEY environment variable is not set.")
        raise HTTPException(
            status_code=500,
            detail="The JULES_API_KEY is not configured on the server, cannot delegate task."
        )

    headers = {
        "X-Goog-Api-Key": jules_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "task_specification": request.task_description,
    }

    logger.info(f"Sending request to Jules API at {JULES_API_URL}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(JULES_API_URL, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            response_data = response.json()
            session_id = response_data.get("session_id")

            if not session_id:
                logger.error(f"Invalid response from Jules API, missing 'session_id'. Response: {response_data}")
                raise HTTPException(status_code=502, detail="Invalid or unexpected response from Jules API: 'session_id' was not found.")

            logger.info(f"Task successfully delegated. Jules API responded with session_id: {session_id}")
            return {
                "status": "success",
                "message": "Task delegation initiated successfully.",
                "session_id": session_id
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