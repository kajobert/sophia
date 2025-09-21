import asyncio
import os
import uuid
from datetime import datetime

import yaml
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import (BackgroundTasks, Body, Depends, FastAPI, File,
                     HTTPException, Request, UploadFile, WebSocket,
                     WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from agents.philosopher_agent import PhilosopherAgent
from core import config as sophia_config
from core.context import SharedContext
from core.gemini_llm_adapter import GeminiLLMAdapter
from core.orchestrator import Orchestrator
from crewai import Task
from memory.advanced_memory import AdvancedMemory
from services.audit_service import log_event
from services.celery_worker import celery_app
from services.roles import ROLE_USER, get_user_role, require_role
from services.token_service import create_refresh_token, verify_refresh_token
from services.user_service import (clear_user_session, get_current_user,
                                   set_user_session)
from services.websocket_manager import manager

# Načtení .env souboru
load_dotenv()

# --- Globální proměnné a konfigurace ---
CONFIG_FILE = "config.yaml"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sophia_main.log")

# --- FastAPI Aplikace ---
app = FastAPI(title="Sophia: An Evolving AI", version="1.0")

# Middleware
app.add_middleware(SessionMiddleware, secret_key=sophia_config.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logování ---
def ensure_log_dir_exists():
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message):
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message, flush=True)

# --- Načtení Konfigurace ---
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log_message(f"CHYBA: Konfigurační soubor '{CONFIG_FILE}' nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        log_message(f"CHYBA: Chyba při parsování konfiguračního souboru: {e}")
        return None

# --- Globální instance pro Orchestrator a LLM ---
llm_adapter: GeminiLLMAdapter | None = None
orchestrator: Orchestrator | None = None
tasks = {}

# --- Cyklus Vědomí (jako background task) ---
async def consciousness_loop():
    global orchestrator, llm_adapter
    log_message("Jádro Vědomí (consciousness_loop) se spouští na pozadí.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Cyklus vědomí se nespustí.")
        return

    waking_duration = config.get("lifecycle", {}).get("waking_duration_seconds", 30)
    sleeping_duration = config.get("lifecycle", {}).get("sleeping_duration_seconds", 60)

    while True:
        log_message("STAV: Bdění - Kontrola nových úkolů z paměti.")
        memory = AdvancedMemory()
        next_task = await memory.get_next_task()

        if next_task:
            task_id = next_task["chat_id"]
            task_description = next_task["user_input"]
            log_message(f"Nalezen nový úkol z paměti: {task_description} (ID: {task_id})")
            context = SharedContext(session_id=task_id, original_prompt=task_description)
            tasks[task_id] = context
            # Orchestrator je spuštěn přes API, zde jen zaznamenáme
            await memory.update_task_status(task_id, "TASK_SEEN")
        else:
            log_message("Žádné nové úkoly ve frontě, odpočívám...")

        await asyncio.sleep(waking_duration)
        memory.close()

        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")
        # ... (logika spánku zůstává stejná)
        await asyncio.sleep(sleeping_duration)

@app.on_event("startup")
async def startup_event():
    global llm_adapter, orchestrator
    log_message("FastAPI aplikace se spouští. Inicializuji globální instance.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Konfigurace pro LLM nebyla nalezena při startu.")
        return

    llm_config = config.get("llm_models", {}).get("primary_llm", {})
    try:
        llm_adapter = GeminiLLMAdapter(
            model=llm_config.get("model_name", "gemini-pro"),
            temperature=llm_config.get("temperature", 0.7),
        )
        orchestrator = Orchestrator(llm=llm_adapter)
        log_message(f"LLM Adapter a Orchestrator úspěšně vytvořeny.")
    except Exception as e:
        log_message(f"Kritická chyba: Nepodařilo se vytvořit LLM adapter nebo Orchestrator: {e}")

    # Spuštění cyklu vědomí na pozadí
    # asyncio.create_task(consciousness_loop()) # Prozatím vypnuto, aby nerušilo API

# --- API Endpoints ---

# Přesunuto z web/api/main.py
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

@app.post("/api/v1/tasks", status_code=202)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    global orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator is not available.")

    task_id = str(uuid.uuid4())
    context = SharedContext(original_prompt=task_request.prompt, session_id=task_id)
    tasks[task_id] = context

    log_message(f"Vytvořen nový úkol přes API: {task_request.prompt} (ID: {task_id})")
    background_tasks.add_task(orchestrator.execute_plan, context)

    return {"task_id": task_id}

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    context = tasks.get(task_id)
    if not context:
        raise HTTPException(status_code=404, detail="Task not found")

    status = "completed" if context.feedback else "in_progress"
    return {
        "task_id": task_id,
        "status": status,
        "history": context.step_history,
        "feedback": context.feedback
    }

@app.websocket("/api/v1/tasks/{task_id}/ws")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

# --- Ostatní endpoints ---
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
