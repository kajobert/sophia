import os
import uuid
from datetime import datetime

import yaml
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# --- New Architecture Imports ---
from core import config as sophia_config
from core.cognitive_layers import MammalianBrain, ReptilianBrain
from core.gemini_llm_adapter import GeminiLLMAdapter
from core.memory_systems import LongTermMemory, ShortTermMemory
from core.neocortex import Neocortex
from agents.planner_agent import PlannerAgent

# --- End New Architecture Imports ---

from services.audit_service import log_event
from services.roles import ROLE_USER, get_user_role, require_role
from services.token_service import create_refresh_token, verify_refresh_token
from services.user_service import clear_user_session, get_current_user, set_user_session
from services.websocket_manager import manager

load_dotenv()

CONFIG_FILE = "config.yaml"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sophia_main.log")

app = FastAPI(title="Sophia: An Evolving AI", version="1.0")

app.add_middleware(SessionMiddleware, secret_key=sophia_config.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_log_dir_exists():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_message(message):
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message, flush=True)


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log_message(f"ERROR: Config file '{CONFIG_FILE}' not found.")
        return None
    except yaml.YAMLError as e:
        log_message(f"ERROR: Error parsing config file: {e}")
        return None


# --- Global instances for the new architecture ---
neocortex: Neocortex | None = None
stm: ShortTermMemory | None = None


@app.on_event("startup")
async def startup_event():
    global neocortex, stm
    log_message("FastAPI application starting up. Initializing cognitive architecture.")

    config = load_config()
    if not config:
        log_message("CRITICAL: LLM configuration not found on startup.")
        return

    llm_config_data = config.get("llm_models", {}).get("primary_llm", {})

    try:
        # 1. Initialize LLM Adapter
        llm_adapter = GeminiLLMAdapter(
            model=llm_config_data.get("model_name", "gemini-pro"),
            temperature=llm_config_data.get("temperature", 0.7),
        )

        # 2. Initialize Memory Systems
        stm = ShortTermMemory(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        ltm = LongTermMemory(
            db_url=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
        )

        # 3. Initialize Planner
        planner = PlannerAgent(llm=llm_adapter)

        # 4. Initialize Cognitive Layers
        reptilian_brain = ReptilianBrain(llm_config=llm_config_data)
        mammalian_brain = MammalianBrain(long_term_memory=ltm)

        # 5. Initialize Neocortex
        neocortex = Neocortex(
            reptilian_brain=reptilian_brain,
            mammalian_brain=mammalian_brain,
            short_term_memory=stm,
            planner=planner,
        )
        log_message("Neocortex and cognitive architecture initialized successfully.")

    except Exception as e:
        log_message(f"CRITICAL: Failed to create cognitive architecture: {e}")


# --- API Endpoints ---

oauth = OAuth(sophia_config.config)
oauth.register(
    name="google",
    client_id=sophia_config.GOOGLE_CLIENT_ID,
    client_secret=sophia_config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.get("/")
def root():
    return {"message": "Sophia API is running."}


# ... (Auth endpoints remain the same) ...
@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth")
async def auth(request: Request, background_tasks: BackgroundTasks):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        background_tasks.add_task(log_event, "login_failed", None, str(error))
        return JSONResponse({"error": str(error)}, status_code=400)
    user = await oauth.google.parse_id_token(request, token)
    request.session["user"] = dict(user)
    background_tasks.add_task(log_event, "login", user, "Google OAuth2")
    return RedirectResponse(url="/me")


@app.get("/me")
@require_role(ROLE_USER)
async def me(request: Request):
    user = get_current_user(request)
    role = get_user_role(user)
    return {"user": user, "role": role}


@app.post("/logout")
@require_role(ROLE_USER)
async def logout(request: Request, background_tasks: BackgroundTasks):
    user = request.session.get("user")
    background_tasks.add_task(log_event, "logout", user)
    clear_user_session(request)
    return {"message": "Odhlášení úspěšné"}


class TaskRequest(BaseModel):
    prompt: str
    user: str | None = None


@app.post("/api/v1/tasks", status_code=202)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    global neocortex
    if not neocortex:
        raise HTTPException(status_code=503, detail="Neocortex is not available.")

    task_id = str(uuid.uuid4())
    log_message(
        f"Created new task from user {task_request.user}: {task_request.prompt} (ID: {task_id})"
    )

    # The Neocortex now handles the entire process
    background_tasks.add_task(
        neocortex.process_input, session_id=task_id, user_input=task_request.prompt
    )

    return {"task_id": task_id}


@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    global stm
    if not stm:
        raise HTTPException(status_code=503, detail="ShortTermMemory is not available.")

    state = stm.load_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    # Determine status based on the state
    is_complete = "plan_success" in [
        h.get("type") for h in state.get("step_history", [])
    ]  # This is a simplification

    return {
        "task_id": task_id,
        "status": "completed" if is_complete else "in_progress",
        "history": state.get("step_history", []),
        "current_plan": state.get("current_plan", []),
    }


@app.websocket("/api/v1/tasks/{task_id}/ws")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)


# ... (Other endpoints like /refresh, /test-login, /upload remain the same for now) ...
@app.post("/refresh")
async def refresh_session(
    request: Request,
    background_tasks: BackgroundTasks,
    refresh_token: str = Body(..., embed=True),
):
    """Obnoví session pomocí refresh tokenu. Vydá nový refresh token a nastaví session."""
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload["sub"]
        user = {"email": user_id, "name": user_id}
        set_user_session(request, user)
        new_refresh = create_refresh_token(user_id)
        background_tasks.add_task(log_event, "refresh", user)
        return {"message": "Session obnovena", "refresh_token": new_refresh}
    except Exception as e:
        background_tasks.add_task(log_event, "refresh_failed", None, str(e))
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")


@app.post("/test-login")
async def test_login(request: Request):
    """Nastaví session na testovacího uživatele. Povolit pouze v testovacím režimu!"""
    if not sophia_config.is_test_mode():
        raise HTTPException(
            status_code=403, detail="Test login povolen jen v testovacím režimu"
        )
    user = {"name": "Test User", "email": "test@example.com"}
    set_user_session(request, user)
    return {"message": "Testovací přihlášení úspěšné", "user": user}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), user: dict = Depends(get_current_user)
):
    # The user is now injected by the get_current_user dependency, which handles the 401 error.
    # Zatím pouze potvrzení přijetí souboru, neukládá se
    return {
        "filename": file.filename,
        "status": "zatím neuloženo (demo)",
        "user": user["email"],
    }


if __name__ == "__main__":
    import uvicorn

    log_message("Spouštím Sophia API přímo přes Uvicorn.")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
