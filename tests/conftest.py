import builtins
import pathlib
import pytest
import os
import time as _time
import datetime as _datetime
import sqlite3
import subprocess as _subprocess
import yaml


@pytest.fixture(autouse=True, scope="function")
def enforce_test_mode_and_sandbox(monkeypatch):
    """
    1. Enforces SOPHIA_TEST_MODE=1, otherwise all tests fail.
    2. Mocks network requests to prevent real API calls.
    3. Restricts file writes to temporary/test directories.
    4. Blocks other dangerous operations like spawning processes, changing time, etc.
    5. Logs all violations for auditing.
    """
    # Step 1: Enforce test mode
    if os.environ.get("SOPHIA_TEST_MODE") != "1":
        pytest.exit(
            "SOPHIA_TEST_MODE is not active! Tests can only be run in test mode."
        )

    audit_log = pathlib.Path("tests/sandbox_audit.log")

    def log_violation(msg):
        with open(audit_log, "a") as f:
            f.write(f"[{_datetime.datetime.now()}] [sandbox] {msg}\\n")

    # Step 2: Block network libraries
    def fake_request(*args, **kwargs):
        log_violation(f"Network request attempt with args: {args}, kwargs: {kwargs}")
        raise RuntimeError("Tests must not make real network calls in test mode!")

    # Patch requests
    try:
        import requests

        monkeypatch.setattr(requests, "request", fake_request)
    except ImportError:
        pass

    # Patch httpx
    try:
        import httpx

        monkeypatch.setattr(httpx, "request", fake_request)
    except ImportError:
        pass

    # Patch urllib
    try:
        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", fake_request)
    except ImportError:
        pass

    # Patch socket to allow local communication (AF_UNIX) but block networking
    try:
        import socket

        original_socket = socket.socket

        # The 'family' argument is crucial for distinguishing network sockets
        def safe_socket_factory(family, *args, **kwargs):
            if family in (socket.AF_INET, socket.AF_INET6):
                log_violation(f"Network socket attempt with family {family}")
                raise RuntimeError(
                    "Tests must not create network sockets in test mode!"
                )
            # Allow other socket types (e.g., AF_UNIX for asyncio/multiprocessing)
            return original_socket(family, *args, **kwargs)

        monkeypatch.setattr(socket, "socket", safe_socket_factory)

    except (ImportError, AttributeError):
        # Handle cases where socket might not be available or fully featured
        pass

    # Step 3: Restrict file writes
    original_open = builtins.open

    def safe_open(file, mode="r", *args, **kwargs):
        if "w" in mode or "a" in mode or "+" in mode:
            p = pathlib.Path(file).resolve()
            # Allow writes to /tmp, the project's tests/, sandbox/, and logs/ directories
            allowed_dirs = [
                "/tmp",
                str(pathlib.Path("tests").resolve()),
                str(pathlib.Path("sandbox").resolve()),
                str(pathlib.Path("logs").resolve()),
            ]
            if not any(str(p).startswith(allowed_dir) for allowed_dir in allowed_dirs):
                log_violation(f"Forbidden file write attempt: {file}")
                raise RuntimeError(
                    f"Test tried to write outside of allowed directories: {file}"
                )
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", safe_open)

    # Step 4: Block dangerous operations
    def block_dangerous_call(name):
        def blocked_function(*args, **kwargs):
            log_violation(f"Dangerous call attempt: {name}")
            raise RuntimeError(f"Tests must not call '{name}' in test mode!")

        return blocked_function

    monkeypatch.setattr(_subprocess, "Popen", block_dangerous_call("subprocess.Popen"))
    monkeypatch.setattr(os, "system", block_dangerous_call("os.system"))
    monkeypatch.setattr(sqlite3, "connect", block_dangerous_call("sqlite3.connect"))
    monkeypatch.setattr(os, "chmod", block_dangerous_call("os.chmod"))
    monkeypatch.setattr(os, "chown", block_dangerous_call("os.chown"))
    monkeypatch.setattr(_time, "sleep", block_dangerous_call("time.sleep"))

    # Block environment variable changes (with a whitelist)
    ENV_WHITELIST = {
        "SOPHIA_TEST_MODE",
        "PYTEST_CURRENT_TEST",
        "PYTHONPATH",
        "PATH",
        "HOME",
        "TMPDIR",
        "TEMP",
        "TMP",
        "SOPHIA_ADMIN_EMAILS",
        "GEMINI_API_KEY",
    }
    original_setitem = os.environ.__setitem__
    original_delitem = os.environ.__delitem__

    def safe_setitem(self, key, value):
        if key not in ENV_WHITELIST:
            log_violation(f"os.environ.__setitem__ attempt for key: {key}")
            raise RuntimeError(f"Test must not change un-whitelisted env var: {key}")
        original_setitem(key, value)

    def safe_delitem(self, key):
        if key not in ENV_WHITELIST:
            log_violation(f"os.environ.__delitem__ attempt for key: {key}")
            raise RuntimeError(f"Test must not delete un-whitelisted env var: {key}")
        original_delitem(key)

    # Directly patching the class method is more robust for os.environ
    monkeypatch.setattr(os.environ.__class__, "__setitem__", safe_setitem)
    monkeypatch.setattr(os.environ.__class__, "__delitem__", safe_delitem)

    yield

    # Teardown is handled by monkeypatch


@pytest.fixture(scope="session", autouse=True)
def create_test_config():
    """
    Creates a dummy config.yaml for tests that initialize the full FastAPI app.
    This prevents the app startup from failing when it can't find the config.
    """
    # Set a dummy API key to allow the real GeminiLLMAdapter to initialize without errors
    # The actual tests will use a mocked version anyway.
    os.environ["GEMINI_API_KEY"] = "test-key"

    config_path = "config.yaml"
    config_data = {
        "llm_models": {
            "primary_llm": {
                "model_name": "test-model",
                "temperature": 0.1,
            }
        },
        "lifecycle": {
            "waking_duration_seconds": 1,
            "sleeping_duration_seconds": 1,
        },
    }
    # Use builtins.open to bypass the sandbox for this setup task
    with builtins.open(config_path, "w") as f:
        yaml.dump(config_data, f)

    yield

    # Cleanup the file and env var after the test session is over
    os.remove(config_path)
    del os.environ["GEMINI_API_KEY"]


@pytest.fixture(scope="function")
def client(enforce_test_mode_and_sandbox):
    """
    Creates a new TestClient for each test function.
    This ensures the app is created *after* setup fixtures like create_test_config have run.
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c
