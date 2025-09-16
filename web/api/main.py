from services.audit_service import log_event
from fastapi import BackgroundTasks

from fastapi import FastAPI, Request, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from core import config as sophia_config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
import os
from services.token_service import create_refresh_token, verify_refresh_token
from services.roles import require_role, ROLE_ADMIN, ROLE_USER, get_user_role
from services.user_service import get_current_user, set_user_session, clear_user_session
from services.chat_service import generate_reply
from services.llm_cache import get_cached_reply, set_cached_reply
from services.celery_worker import celery_app

GOOGLE_CLIENT_ID = sophia_config.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = sophia_config.GOOGLE_CLIENT_SECRET
SECRET_KEY = sophia_config.SECRET_KEY

app = FastAPI(title="Sophia Web API", version="0.1")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- Refresh session endpoint ---
@app.post('/refresh')
async def refresh_session(request: Request, background_tasks: BackgroundTasks, refresh_token: str = Body(..., embed=True)):
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
@app.post('/test-login')
async def test_login(request: Request):
    """Nastaví session na testovacího uživatele. Povolit pouze v testovacím režimu!"""
    if not sophia_config.is_test_mode():
        raise HTTPException(status_code=403, detail="Test login povolen jen v testovacím režimu")
    user = {'name': 'Test User', 'email': 'test@example.com'}
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
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth')
async def auth(request: Request, background_tasks: BackgroundTasks):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        background_tasks.add_task(log_event, "login_failed", None, str(error))
        return JSONResponse({"error": str(error)}, status_code=400)
    user = await oauth.google.parse_id_token(request, token)
    # Uložení identity do session
    request.session['user'] = dict(user)
    background_tasks.add_task(log_event, "login", user, "Google OAuth2")
    return RedirectResponse(url='/me')


# --- Session management & user info ---
@app.get('/me')
@require_role(ROLE_USER)
async def me(request: Request):
    """Vrací informace o přihlášeném uživateli (nebo 401 pokud není přihlášen)."""
    user = get_current_user(request)
    role = get_user_role(user)
    return {"user": user, "role": role}

@app.post('/logout')
@require_role(ROLE_USER)
async def logout(request: Request, background_tasks: BackgroundTasks):
    """Odhlásí uživatele (vymaže session)."""
    user = request.session.get('user')
    background_tasks.add_task(log_event, "logout", user)
    clear_user_session(request)
    return {"message": "Odhlášení úspěšné"}


# --- Synchronous chat endpoint (původní) ---
from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str

@app.post('/chat')
async def chat(msg: ChatMessage, request: Request):
    user = request.session.get('user')
    cached = get_cached_reply(msg.message, user)
    if cached:
        return {"reply": cached}
    reply = generate_reply(msg.message, user)
    set_cached_reply(msg.message, user, reply)
    return {"reply": reply}

# --- Asynchronní chat endpoint přes Celery ---
@app.post('/chat-async')
async def chat_async(msg: ChatMessage, request: Request):
    user = request.session.get('user')
    # user může být None (veřejný chat)
    task = celery_app.send_task("llm.generate_reply", args=[msg.message, user])
    return {"task_id": task.id}

# Endpoint pro vyzvednutí výsledku
@app.get('/chat-result/{task_id}')
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
from fastapi import File, UploadFile

@app.post('/upload')
async def upload_file(file: UploadFile = File(...), request: Request = None):
    user = request.session.get('user') if request else None
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Zatím pouze potvrzení přijetí souboru, neukládá se
    return {"filename": file.filename, "status": "zatím neuloženo (demo)"}

# Poznámka: Další endpoints a logika budou přidány v dalších krocích.
