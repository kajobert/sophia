"""Tests for CoreSelfDiagnostic plugin.

Verifies that the plugin schedules and runs a short background check and
exposes a `last_result` dictionary with expected keys.
"""

import asyncio
import logging

import pytest

from plugins.core_self_diagnostic import CoreSelfDiagnostic


class DummyPM:
    def __init__(self):
        # minimal API used by plugin
        self._plugins = {}

    def get_plugins_by_type(self, t):
        return []


@pytest.fixture
def plugin():
    p = CoreSelfDiagnostic()
    cfg = {
        "plugin_manager": DummyPM(),
        "all_plugins": {},
        "logger": logging.getLogger("test.selfdiag"),
        "offline_mode": False,
    }
    p.setup(cfg)
    return p


@pytest.mark.asyncio
async def test_runs_background_check(plugin):
    # Allow background task to run
    await asyncio.sleep(0.2)

    assert plugin.last_result is not None
    # Basic keys expected in the result
    assert "plugin_count" in plugin.last_result
    assert "llm_tool_present" in plugin.last_result
    assert plugin.last_result.get("offline_mode") is False
