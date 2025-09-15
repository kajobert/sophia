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
    assert resp.status_code == 401

def test_upload_unauth():
    resp = client.post("/upload", files={"file": ("test.txt", b"data")})
    assert resp.status_code == 401

# Poznámka: Testy přihlášení přes Google OAuth2 vyžadují interaktivní flow a nelze je plně automatizovat bez mockování.
# Lze však ověřit, že endpoint /login vrací redirect (302).
def test_login_redirect():
    resp = client.get("/login", follow_redirects=False)
    assert resp.status_code == 307 or resp.status_code == 302
    assert "accounts.google.com" in resp.headers["location"]
