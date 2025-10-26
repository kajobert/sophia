import pytest
from pathlib import Path

from plugins.cognitive_historian import Historian


@pytest.fixture
def historian_plugin(tmp_path: Path):
    """Fixture to provide a Historian instance with a temporary WORKLOG.md."""
    worklog_content = """
---
**Mise:** Test Mission 1
**Agent:** Jules v1.1
**Datum:** 2025-10-25
**Status:** DOKONCENO

**1. Plán:**
*   Do something.
---
**Mise:** Test Mission 2
**Agent:** Jules v1.2
**Datum:** 2025-10-26
**Status:** PROBIHA

**1. Plán:**
*   Do something else.
---
"""
    worklog_file = tmp_path / "WORKLOG.md"
    worklog_file.write_text(worklog_content)

    historian = Historian()
    historian.setup({"worklog_file": str(worklog_file)})
    return historian


def test_historian_review_past_missions(historian_plugin: Historian):
    """Tests parsing missions from the WORKLOG.md file."""
    missions = historian_plugin.review_past_missions(limit=2)

    assert len(missions) == 2

    mission1 = missions[0]
    assert mission1["mission"] == "Test Mission 1"
    assert mission1["agent"] == "Jules v1.1"
    assert mission1["status"] == "DOKONCENO"

    mission2 = missions[1]
    assert mission2["mission"] == "Test Mission 2"
    assert mission2["agent"] == "Jules v1.2"
    assert mission2["status"] == "PROBIHA"


def test_historian_file_not_found():
    """Tests the behavior when the WORKLOG.md file does not exist."""
    historian = Historian()
    historian.setup({"worklog_file": "non_existent_worklog.md"})
    result = historian.review_past_missions()

    assert "error" in result[0]
    assert "not found" in result[0]["error"]
