from authlib.integrations.starlette_client import OAuth, OAuthError
from core import config as sophia_config
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
import uuid
import asyncio
from core.orchestrator import Orchestrator
from core.context import SharedContext
from core.gemini_llm_adapter import GeminiLLMAdapter
from services.audit_service import log_event
from services.celery_worker import celery_app
from web.api.websocket_manager import manager
from services.roles import ROLE_USER, get_user_role, require_role
from services.token_service import create_refresh_token, verify_refresh_token
from services.user_service import (
    clear_user_session,
    get_current_user,
    set_user_session,
)
from starlette.middleware.sessions import SessionMiddleware

GOOGLE_CLIENT_ID = sophia_config.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = sophia_config.GOOGLE_CLIENT_SECRET
SECRET_KEY = sophia_config.SECRET_KEY

app = FastAPI(title="Sophia Web API", version="0.1")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# --- Refresh session endpoint ---
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


# --- Testovací login endpoint (pouze pro testy) ---
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


# CORS pro vývoj (povolit localhost, později zpřísnit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Sophia Web API is running."}


# --- Google OAuth2 login ---
oauth = OAuth(sophia_config.config)
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


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
    # Uložení identity do session
    request.session["user"] = dict(user)
    background_tasks.add_task(log_event, "login", user, "Google OAuth2")
    return RedirectResponse(url="/me")


# --- Session management & user info ---
@app.get("/me")
@require_role(ROLE_USER)
async def me(request: Request):
    """Vrací informace o přihlášeném uživateli (nebo 401 pokud není přihlášen)."""
    user = get_current_user(request)
    role = get_user_role(user)
    return {"user": user, "role": role}


@app.post("/logout")
@require_role(ROLE_USER)
async def logout(request: Request, background_tasks: BackgroundTasks):
    """Odhlásí uživatele (vymaže session)."""
    user = request.session.get("user")
    background_tasks.add_task(log_event, "logout", user)
    clear_user_session(request)
    return {"message": "Odhlášení úspěšné"}


# --- Asynchronní chat endpoint přes Celery ---
class ChatMessage(BaseModel):
    message: str


@app.post("/chat-async")
async def chat_async(msg: ChatMessage, request: Request):
    user = request.session.get("user")
    # user může být None (veřejný chat)
    task = celery_app.send_task("llm.generate_reply", args=[msg.message, user])
    return {"task_id": task.id}


# Endpoint pro vyzvednutí výsledku
@app.get("/chat-result/{task_id}")
async def chat_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "success", "reply": result.result}
    elif result.state == "FAILURE":
        return {"status": "failure", "error": str(result.result)}
    else:
        return {"status": result.state}


# --- Dummy upload endpoint (zatím nefunkční) ---
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

# --- Task management endpoints ---
tasks = {}

class TaskRequest(BaseModel):
    prompt: str

@app.post("/api/v1/tasks", status_code=202)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())

    # In a real app, LLM would be managed via dependency injection
    try:
        llm_adapter = GeminiLLMAdapter()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM: {e}")

    orchestrator = Orchestrator(llm=llm_adapter)
    context = SharedContext(original_prompt=task_request.prompt, session_id=task_id)
    tasks[task_id] = context

    background_tasks.add_task(orchestrator.execute_plan, context)

    return {"task_id": task_id}

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    context = tasks.get(task_id)
    if not context:
        raise HTTPException(status_code=404, detail="Task not found")

    # This status is a placeholder. A more robust solution would track the orchestrator's state.
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
            # Keep the connection alive to send updates from the orchestrator
            # We are not expecting any messages from the client in this implementation
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

# Poznámka: Další endpoints a logika budou přidány v dalších krocích.
