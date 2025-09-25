import asyncio
import os
import uuid
from datetime import datetime

import yaml
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from contextlib import asynccontextmanager
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

from core import config as sophia_config
from core.context import SharedContext
from core.gemini_llm_adapter import GeminiLLMAdapter
from core.neocortex import Neocortex
from core.cognitive_layers import ReptilianBrain, MammalianBrain
from core.memory_systems import ShortTermMemory, LongTermMemory
from core.neocortex import Neocortex as Orchestrator
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
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:3001"],
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
        f.write(f"{timestamp} - {message}\\n")
    print(message, flush=True)

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

llm_adapter: GeminiLLMAdapter | None = None
neocortex: Neocortex | None = None
reptilian: ReptilianBrain | None = None
mammalian: MammalianBrain | None = None
short_term_memory: ShortTermMemory | None = None
long_term_memory: LongTermMemory | None = None
tasks = {}
main_event_loop = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_adapter, short_term_memory, long_term_memory, reptilian, mammalian, neocortex, main_event_loop
    log_message("FastAPI aplikace se spouští. Inicializuji globální instance (lifespan).")
    config = load_config()
    if config:
        llm_config = config.get("llm_models", {}).get("primary_llm", {})
        try:
            llm_adapter = GeminiLLMAdapter(
                model=llm_config.get("model_name", "gemini-pro"),
                temperature=llm_config.get("temperature", 0.7),
            )
            short_term_memory = ShortTermMemory()
            long_term_memory = LongTermMemory()
            reptilian = ReptilianBrain()
            mammalian = MammalianBrain(long_term_memory=long_term_memory)
            neocortex = Neocortex(llm=llm_adapter, short_term_memory=short_term_memory)
            log_message("LLM Adapter a kognitivní vrstvy úspěšně vytvořeny.")
        except Exception as e:
            log_message(f"Kritická chyba: Nepodařilo se vytvořit LLM adapter nebo kognitivní vrstvy: {e}")
    else:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Lifespan startup přeskočen.")

    try:
        main_event_loop = asyncio.get_event_loop()
    except Exception:
        main_event_loop = None

    try:
        yield
    finally:
        log_message("Lifespan shutdown: čištění zdrojů (pokud je potřeba).")

app.router.lifespan_context = lifespan

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
# ... (the rest of the file is fine)
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
    global orchestrator
    global neocortex, reptilian, mammalian, short_term_memory, long_term_memory
    if not neocortex or not reptilian or not mammalian:
        raise HTTPException(status_code=503, detail="Cognitive core is not available.")

    task_id = str(uuid.uuid4())
    context = SharedContext(
        original_prompt=task_request.prompt, session_id=task_id, user=task_request.user
    )
    tasks[task_id] = context

    log_message(
        f"Vytvořen nový úkol od uživatele {task_request.user}: {task_request.prompt} (ID: {task_id})"
    )

    from typing import cast
    import inspect

    neocortex_local = cast(Neocortex, neocortex)
    reptilian_local = cast(ReptilianBrain, reptilian)
    mammalian_local = cast(MammalianBrain, mammalian)

    def _run_pipeline(ctx: SharedContext):
        c1 = reptilian_local.process_input(ctx)
        c2 = mammalian_local.process_input(c1)
        try:
            exec_result = neocortex_local.execute_plan(c2)
            if inspect.isawaitable(exec_result) and main_event_loop is not None:
                asyncio.run_coroutine_threadsafe(exec_result, main_event_loop)
        except Exception:
            pass

    background_tasks.add_task(_run_pipeline, context)

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
        "feedback": context.feedback,
    }


@app.websocket("/api/v1/tasks/{task_id}/ws")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

if __name__ == "__main__":
    import uvicorn

    log_message("Spouštím Sophia API přímo přes Uvicorn.")
    uvicorn.run(app, host="0.0.0.0", port=8000)