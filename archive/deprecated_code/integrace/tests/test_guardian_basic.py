import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))
import guardian


def test_guardian_importable():
    assert hasattr(guardian, "main")
    assert callable(guardian.main)


def test_log_message_creates_log():
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
