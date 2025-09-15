# Sophia Web API – FastAPI backend (základní skeleton)


from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
import os

config = Config('.env')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', cast=str, default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', cast=str, default='')
SECRET_KEY = config('SECRET_KEY', cast=str, default='supersecretkey')


app = FastAPI(title="Sophia Web API", version="0.1")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

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
oauth = OAuth(config)
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
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return JSONResponse({"error": str(error)}, status_code=400)
    user = await oauth.google.parse_id_token(request, token)
    # Uložení identity do session
    request.session['user'] = dict(user)
    return RedirectResponse(url='/me')

@app.get('/me')
async def me(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}
# TODO: Session management, user info endpoint

# --- Dummy chat endpoint ---
from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str

@app.post('/chat')
async def chat(msg: ChatMessage, request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Zatím pouze echo odpověď
    return {"reply": f"Sophia říká: {msg.message}"}

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
