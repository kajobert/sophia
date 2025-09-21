import pytest
import requests
import subprocess
import os
import time

def test_sandbox_blocks_network_requests():
    """Verify that the sandbox blocks network calls via requests."""
    # The sandbox blocks this at the lowest level, which is socket creation.
    with pytest.raises(RuntimeError, match="Tests must not create network sockets in test mode!"):
        requests.get("https://www.google.com")

def test_sandbox_blocks_forbidden_file_writes():
    """Verify that the sandbox blocks writing files outside allowed directories."""
    with pytest.raises(RuntimeError, match="Test tried to write outside of allowed directories"):
        with open("/forbidden_file.txt", "w") as f:
            f.write("This should fail.")

def test_sandbox_blocks_subprocess():
    """Verify that the sandbox blocks spawning subprocesses."""
    with pytest.raises(RuntimeError, match="Tests must not call 'subprocess.Popen' in test mode!"):
        subprocess.Popen(["ls"])

def test_sandbox_blocks_os_system():
    """Verify that the sandbox blocks os.system calls."""
    with pytest.raises(RuntimeError, match="Tests must not call 'os.system' in test mode!"):
        os.system("echo 'hello'")

def test_sandbox_blocks_time_sleep():
    """Verify that the sandbox blocks time.sleep calls."""
    with pytest.raises(RuntimeError, match="Tests must not call 'time.sleep' in test mode!"):
        time.sleep(1)

def test_sandbox_blocks_env_var_changes():
    """Verify that the sandbox blocks changes to non-whitelisted env vars."""
    with pytest.raises(RuntimeError, match="Test must not change un-whitelisted env var: FORBIDDEN_VAR"):
        os.environ["FORBIDDEN_VAR"] = "some_value"

def test_sandbox_allows_whitelisted_env_var_changes(monkeypatch):
    """Verify that the sandbox allows changes to whitelisted env vars."""
    # This should not raise an exception
    original_value = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv("PYTHONPATH", "/new/path")
    assert os.environ["PYTHONPATH"] == "/new/path"
    # monkeypatch will restore the original value automatically
