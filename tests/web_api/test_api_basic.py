
import os
import sys

import pytest
# Robustní import JWT, pokud není dostupný, testy budou přeskočeny
try:
    import jwt
except ImportError:
    pytest.skip("Modul 'jwt' není dostupný, přeskočeno.", allow_module_level=True)

from fastapi.testclient import TestClient
from services.token_service import create_refresh_token


# This setup needs to run before `main` is imported
os.environ["SOPHIA_TEST_MODE"] = "1"

# Add the web/api path to sys.path to allow importing 'main'
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web/api"))
)

from main import app  # noqa: E402

client = TestClient(app)


def test_root():
    """Test the root endpoint."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Sophia Web API")


def test_login_and_me_endpoint(monkeypatch):
    """Test the test-login and /me endpoint."""
    # Ensure the test user is an admin for this test
    monkeypatch.setenv("SOPHIA_ADMIN_EMAILS", "test@example.com")
    # We need to reload the config/roles module for the change to take effect
    from core import config as sophia_config
    from services import roles
    import importlib
    importlib.reload(sophia_config)
    importlib.reload(roles)

    with client as c:
        resp = c.post("/test-login")
        assert resp.status_code == 200
        assert "Testovací přihlášení úspěšné" in resp.json()["message"]

        resp = c.get("/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "test@example.com"
        assert data["role"] == "admin"


def test_logout_and_session():
    """Test that logout invalidates the session."""
    with client as c:
        # Login first
        c.post("/test-login")
        resp = c.get("/me")
        assert resp.status_code == 200

        # Logout
        resp = c.post("/logout")
        assert resp.status_code == 200
        assert "Odhlášení úspěšné" in resp.json()["message"]

        # Verify /me is now unauthorized
        resp = c.get("/me")
        assert resp.status_code == 401


def test_refresh_token():
    """Test that a refresh token can restore a session."""
    with client as c:
        # 1. Login to get a valid user
        resp = c.post("/test-login")
        assert resp.status_code == 200
        user = resp.json()["user"]
        refresh_token = create_refresh_token(user["email"])

        # 2. Logout to destroy the session
        c.post("/logout")
        resp = c.get("/me")
        assert resp.status_code == 401

        # 3. Use the refresh token to get a new session
        resp = c.post("/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "Session obnovena" in data["message"]
        assert "refresh_token" in data

        # 4. Verify the new session works
        resp = c.get("/me")
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "test@example.com"


@pytest.mark.skip(
    reason="Requires a running Redis and Celery worker, which is not available in the test environment."
)
def test_chat_async_endpoints():
    """Test the async chat submission and result retrieval."""
    with client as c:
        # Submit a task
        resp = c.post("/chat-async", json={"message": "Ahoj"})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]
        assert isinstance(task_id, str)

        # For testing, we can't easily wait for celery, so we just check the pending status
        resp = c.get(f"/chat-result/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] in [
            "PENDING",
            "SUCCESS",
        ]  # Depending on test speed


def test_upload_unauth():
    """Test that uploading without auth fails."""
    with client as c:
        c.post("/logout")  # Ensure clean session
        resp = c.post("/upload", files={"file": ("test.txt", b"data")})
        assert resp.status_code == 401


def test_login_redirect():
    """Test that the /login endpoint redirects to Google."""
    resp = client.get("/login", follow_redirects=False)
    # It's a redirect status
    assert resp.status_code in [302, 307]
    assert "accounts.google.com" in resp.headers["location"]
