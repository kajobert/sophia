"""Tests for CoreProactiveAgent plugin.

These tests verify metadata, event bus injection, heartbeat publishing,
and idea file detection.
"""

import asyncio
import logging
import os
import pytest

from plugins.core_proactive_agent import CoreProactiveAgent
from core.event_bus import EventBus
from core.events import EventType


@pytest.fixture
def plugin():
    p = CoreProactiveAgent()
    cfg = {"heartbeat_interval": 0.05, "poll_interval": 0.05}
    p.setup(cfg)
    return p


@pytest.fixture
def event_bus():
    return EventBus()


def test_metadata(plugin):
    assert plugin.name == "core_proactive_agent"
    assert plugin.plugin_type.name in ("COGNITIVE",)
    assert plugin.version.startswith("0.")


@pytest.mark.asyncio
async def test_eventbus_integration_heartbeat_and_idea(plugin, event_bus, tmp_path):
    # Prepare idea file path
    idea_file = tmp_path / "ideas.txt"
    plugin.idea_file = str(idea_file)

    # Inject event bus and start it
    plugin.set_event_bus(event_bus)
    await event_bus.start()

    received = []

    async def capture(e):
        received.append(e)

    event_bus.subscribe(EventType.CUSTOM, capture)

    # Give time for a couple heartbeats
    await asyncio.sleep(0.2)

    # Create idea file to trigger NEW_IDEA_DETECTED
    idea_file.write_text("New idea content\n")

    await asyncio.sleep(0.2)

    await event_bus.stop()

    # There should be at least one heartbeat and one NEW_IDEA_DETECTED event
    assert any(evt.data.get("subtype") == "HEARTBEAT" for evt in received)
    assert any(evt.data.get("subtype") == "NEW_IDEA_DETECTED" for evt in received)
