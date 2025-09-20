import os
import sys


import pytest
from tests.conftest import robust_import, safe_remove
import tempfile
import os

guardian = robust_import('guardian')
def test_guardian_importable(request):
    assert hasattr(guardian, "main")
    assert callable(guardian.main)
    assert hasattr(guardian, "main")
    assert callable(guardian.main)
    # Audit snapshot
    snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
    if snapshot:
        snapshot(str(dir(guardian)))
def test_log_message_creates_log(request):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "guardian.log")
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "guardian.log")
        # monkeypatch log path
        orig_log_file = guardian.LOG_FILE
        guardian.LOG_FILE = log_path
        guardian.log_message("test123")
        with open(log_path) as f:
            content = f.read()
        assert "test123" in content
        guardian.LOG_FILE = orig_log_file
        # Audit snapshot
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot(content)
