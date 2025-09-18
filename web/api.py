import sys
import os
import uuid
from fastapi import FastAPI, Request, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse, RedirectResponse
from starlette.config import Config
from fastapi.staticfiles import StaticFiles
from unittest.mock import patch

from authlib.integrations.starlette_client import OAuth, OAuthError

# This is a hack to ensure the application can find the 'core' and 'agents' modules
# In a real-world scenario, this project should be structured as a proper Python package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SOPHIA_SECRET_KEY", "a_very_secret_key_that_should_be_changed")
)

# --- OAuth2 Configuration ---
try:
    config = Config(".env")
    oauth = OAuth(config)
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    print("--- OAuth configured successfully for Google. ---")
except Exception as e:
    print(f"--- CRITICAL: Failed to configure OAuth: {e} ---")
    oauth = None

# --- Authentication Dependencies and Routes ---
async def get_current_user(request: Request):
    """Dependency to get user from session; raises 401 if not authenticated."""
    user = request.session.get('user')
    if not user:
        # In test mode, we can return a mock user to bypass login
        if os.getenv('SOPHIA_ENV') == 'test':
            return {"email": "test@example.com", "name": "Test User"}
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get('/login')
async def login(request: Request):
    """Redirects user to Google's authentication page."""
    if not oauth:
        raise HTTPException(status_code=500, detail="OAuth is not configured.")
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth')
async def auth(request: Request):
    """Callback endpoint for Google OAuth2."""
    if not oauth:
        raise HTTPException(status_code=500, detail="OAuth is not configured.")
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        if user:
            request.session['user'] = dict(user)
    except OAuthError as error:
        return RedirectResponse(url=f'/?error={error.error}')
    return RedirectResponse(url='/')

@app.post('/logout')
async def logout(request: Request):
    """Logs out the user by clearing the session."""
    request.session.pop('user', None)
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Returns the current logged-in user's information."""
    return current_user

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    """
    Endpoint to receive a prompt, run the full agent orchestration,
    and return a structured response. Requires authentication.
    """
    orchestrator = request.app.state.orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="The agent orchestrator is not available.")

    try:
        chat_request_data = await request.json()
        prompt = chat_request_data.get('prompt')
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is missing from request body.")

        final_context = await orchestrator.route_prompt(prompt)

        return {
            "status": "success",
            "message": "Orchestration completed.",
            "session_id": final_context.session_id,
            "final_context": final_context.payload
        }
    except Exception as e:
        logging.error(f"An error occurred during chat orchestration for user {user.get('email')}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# --- Static file serving ---
# This must be the last mounted path to avoid overriding other routes.
static_files_path = os.path.join(os.path.dirname(__file__), "ui")
if os.path.exists(static_files_path):
    app.mount("/", StaticFiles(directory=static_files_path, html=True), name="ui")
else:
    @app.get("/")
    async def serve_root_message():
        return {"message": "Welcome to Sophia's API. UI not found."}
    print(f"--- WARNING: Static files directory not found at {static_files_path} ---")
