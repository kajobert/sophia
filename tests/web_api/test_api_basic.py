from services.token_service import create_refresh_token
# Test refresh token endpoint
def test_refresh_token():
    with client as c:
        # Testovací login
        resp = c.post('/test-login')
        assert resp.status_code == 200
        user = resp.json()["user"]
        refresh_token = create_refresh_token(user["email"])
        # Odhlásit session
        c.post('/logout')
        # Ověřit, že /me vrací 401
        resp = c.get('/me')
        assert resp.status_code == 401
        # Obnovit session pomocí refresh tokenu
        resp = c.post('/refresh', json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"].startswith("Session obnovena")
        assert "refresh_token" in data
        # Ověřit, že /me opět funguje
        resp = c.get('/me')
        assert resp.status_code == 200
import os
os.environ['SOPHIA_TEST_MODE'] = '1'
import pytest
from fastapi.testclient import TestClient
import sys
# Přidat cestu k web/api pro import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../web/api')))
from main import app
client = TestClient(app)

# Test odhlášení a session
def test_logout_and_session():
    with client as c:
        # Testovací login
        resp = c.post('/test-login')
        assert resp.status_code == 200
        # Ověř, že /me funguje
        resp = c.get('/me')
        assert resp.status_code == 200
        # Odhlášení
        resp = c.post('/logout')
        assert resp.status_code == 200
        assert resp.json()["message"].startswith("Odhlášení")
        # Po odhlášení už /me vrací 401
        resp = c.get('/me')
        assert resp.status_code == 401
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Přidat cestu k web/api pro import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../web/api')))
from main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Sophia Web API")

def test_chat_unauth():
    resp = client.post("/chat", json={"message": "Ahoj"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Sophia říká" in data["reply"]

def test_upload_unauth():
    resp = client.post("/upload", files={"file": ("test.txt", b"data")})
    assert resp.status_code == 401

# Poznámka: Testy přihlášení přes Google OAuth2 vyžadují interaktivní flow a nelze je plně automatizovat bez mockování.
# Lze však ověřit, že endpoint /login vrací redirect (302).
def test_login_redirect():
    resp = client.get("/login", follow_redirects=False)
    assert resp.status_code == 307 or resp.status_code == 302
    assert "accounts.google.com" in resp.headers["location"]
