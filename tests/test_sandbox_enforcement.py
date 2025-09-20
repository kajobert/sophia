import pytest
import os
import tempfile

def test_httpx_blocked():
    pytest.importorskip("httpx")
    import httpx
    with pytest.raises(RuntimeError):
        httpx.get("https://example.com")

def test_urllib_blocked():
    import urllib.request
    with pytest.raises(RuntimeError):
        urllib.request.urlopen("https://example.com")

def test_socket_blocked():
    import socket
    with pytest.raises(RuntimeError):
        socket.socket()

def test_write_home_blocked():
    home = os.path.expanduser("~/.sophia_test_blocked")
    try:
        with pytest.raises(RuntimeError):
            with open(home, "w") as f:
                f.write("fail")
    finally:
        if os.path.exists(home):
            os.remove(home)

def test_write_var_blocked():
    path = "/var/tmp/sophia_test_blocked"
    try:
        with pytest.raises(RuntimeError):
            with open(path, "w") as f:
                f.write("fail")
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_spawn_process_blocked():
    import subprocess
    with pytest.raises(RuntimeError):
        subprocess.Popen(["echo", "fail"])
    with pytest.raises(RuntimeError):
        os.system("echo fail")

def test_time_change_blocked():
    import time
    with pytest.raises(RuntimeError):
        time.sleep(1)
    with pytest.raises(RuntimeError):
        os.utime("/tmp", None)

def test_rights_change_blocked():
    with pytest.raises(RuntimeError):
        os.chmod("/tmp", 0o777)
    with pytest.raises(RuntimeError):
        os.chown("/tmp", 0, 0)

def test_env_change_blocked():
    # Blokace pro ne-whitelistované proměnné
    with pytest.raises(RuntimeError):
        os.putenv("SOPHIA_TEST_ENV", "fail")
    with pytest.raises(RuntimeError):
        os.environ["SOPHIA_TEST_ENV2"] = "fail"
    # Whitelistované proměnné lze měnit
    os.environ["PATH"] = "/usr/bin"
    os.putenv("PATH", "/usr/bin")
    del os.environ["PATH"]

def test_sqlite_blocked():
    pytest.importorskip("sqlite3")
    import sqlite3
    with pytest.raises(RuntimeError):
        sqlite3.connect(":memory:")
