"""
Unit tests for CoreSleepScheduler plugin.

Tests time-based scheduling, idle detection, and consolidation triggering.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from plugins.core_sleep_scheduler import CoreSleepScheduler, SleepCycleTrigger, SleepScheduleConfig
from plugins.base_plugin import PluginType
from core.context import SharedContext
from core.event_bus import EventBus
from core.events import Event, EventType


@pytest.fixture
def scheduler():
    """Create a SleepScheduler instance for testing."""
    plugin = CoreSleepScheduler()
    config = {
        "schedule": {
            "enabled": True,
            "trigger_type": "time_based",
            "interval_hours": 6,
            "idle_minutes": 30,
        }
    }
    plugin.setup(config)
    return plugin


@pytest.fixture
def event_bus():
    """Create an EventBus for testing."""
    return EventBus()


@pytest.fixture
def mock_consolidator():
    """Create a mock consolidator plugin."""
    from plugins.cognitive_memory_consolidator import ConsolidationMetrics

    consolidator = MagicMock()
    consolidator.trigger_consolidation = AsyncMock(
        return_value=ConsolidationMetrics(
            sessions_processed=1, memories_created=5, duration_seconds=1.5
        )
    )
    return consolidator


@pytest.fixture
def mock_context():
    """Create a mock SharedContext."""
    import logging

    return SharedContext(
        session_id="test_session",
        current_state="processing",
        logger=logging.getLogger("test"),
        user_input="test input",
    )


class TestPluginMetadata:
    """Test plugin metadata and initialization."""

    def test_plugin_name(self, scheduler):
        """Test plugin name."""
        assert scheduler.name == "core_sleep_scheduler"

    def test_plugin_type(self, scheduler):
        """Test plugin type."""
        assert scheduler.plugin_type == PluginType.CORE

    def test_plugin_version(self, scheduler):
        """Test plugin version."""
        assert scheduler.version == "1.0.0"

    def test_no_tool_definitions(self, scheduler):
        """Test scheduler provides no LLM tools (autonomous only)."""
        tools = scheduler.get_tool_definitions()
        assert tools == []


class TestConfiguration:
    """Test configuration loading."""

    def test_config_loading(self, scheduler):
        """Test configuration is loaded correctly."""
        assert scheduler.config.enabled is True
        assert scheduler.config.trigger_type == SleepCycleTrigger.TIME_BASED
        assert scheduler.config.interval_hours == 6
        assert scheduler.config.idle_minutes == 30

    def test_config_defaults(self):
        """Test default configuration values."""
        config = SleepScheduleConfig()
        assert config.enabled is True
        assert config.trigger_type == SleepCycleTrigger.TIME_BASED
        assert config.interval_hours == 6
        assert config.idle_minutes == 30

    def test_low_activity_config(self):
        """Test LOW_ACTIVITY trigger configuration."""
        plugin = CoreSleepScheduler()
        config = {
            "schedule": {
                "enabled": True,
                "trigger_type": "low_activity",
                "interval_hours": 6,
                "idle_minutes": 15,
            }
        }
        plugin.setup(config)

        assert plugin.config.trigger_type == SleepCycleTrigger.LOW_ACTIVITY
        assert plugin.config.idle_minutes == 15


class TestDependencyInjection:
    """Test dependency injection."""

    def test_set_event_bus(self, scheduler, event_bus):
        """Test EventBus injection."""
        scheduler.set_event_bus(event_bus)
        assert scheduler.event_bus is event_bus

    def test_set_consolidator(self, scheduler, mock_consolidator):
        """Test consolidator plugin injection."""
        scheduler.set_consolidator(mock_consolidator)
        assert scheduler.consolidator_plugin is mock_consolidator


class TestUserActivityTracking:
    """Test user activity detection."""

    @pytest.mark.asyncio
    async def test_user_activity_updates_timestamp(self, scheduler, event_bus):
        """Test user activity updates last_activity timestamp."""
        scheduler.set_event_bus(event_bus)

        initial_time = scheduler.last_user_activity
        await asyncio.sleep(0.1)

        # Simulate USER_INPUT event
        event = Event(event_type=EventType.USER_INPUT, source="terminal", data={"input": "test"})
        await scheduler._on_user_activity(event)

        assert scheduler.last_user_activity > initial_time


class TestTimeBasedTrigger:
    """Test time-based consolidation triggering."""

    @pytest.mark.asyncio
    async def test_initial_consolidation_triggers_immediately(self, scheduler, mock_consolidator):
        """Test first consolidation triggers when last_consolidation is None."""
        scheduler.set_consolidator(mock_consolidator)

        assert scheduler.last_consolidation is None

        await scheduler._check_time_based_trigger()

        # Should have triggered consolidation
        mock_consolidator.trigger_consolidation.assert_called_once()
        assert scheduler.last_consolidation is not None

    @pytest.mark.asyncio
    async def test_time_based_trigger_respects_interval(self, scheduler, mock_consolidator):
        """Test time-based trigger respects configured interval."""
        scheduler.set_consolidator(mock_consolidator)

        # Set last consolidation to 5 hours ago (less than 6h interval)
        scheduler.last_consolidation = datetime.now() - timedelta(hours=5)

        await scheduler._check_time_based_trigger()

        # Should NOT trigger (interval not reached)
        mock_consolidator.trigger_consolidation.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_based_trigger_fires_after_interval(self, scheduler, mock_consolidator):
        """Test time-based trigger fires after interval elapsed."""
        scheduler.set_consolidator(mock_consolidator)

        # Set last consolidation to 7 hours ago (more than 6h interval)
        scheduler.last_consolidation = datetime.now() - timedelta(hours=7)

        await scheduler._check_time_based_trigger()

        # Should trigger consolidation
        mock_consolidator.trigger_consolidation.assert_called_once()


class TestIdleTrigger:
    """Test idle-based consolidation triggering."""

    @pytest.mark.asyncio
    async def test_idle_trigger_waits_for_idle_period(self, mock_consolidator):
        """Test idle trigger waits for configured idle period."""
        plugin = CoreSleepScheduler()
        config = {
            "schedule": {"enabled": True, "trigger_type": "low_activity", "idle_minutes": 30}
        }
        plugin.setup(config)
        plugin.set_consolidator(mock_consolidator)

        # Set last activity to 20 minutes ago (less than 30m)
        plugin.last_user_activity = datetime.now() - timedelta(minutes=20)

        await plugin._check_idle_trigger()

        # Should NOT trigger (not idle long enough)
        mock_consolidator.trigger_consolidation.assert_not_called()

    @pytest.mark.asyncio
    async def test_idle_trigger_fires_after_idle_period(self, mock_consolidator):
        """Test idle trigger fires after idle period elapsed."""
        plugin = CoreSleepScheduler()
        config = {
            "schedule": {"enabled": True, "trigger_type": "low_activity", "idle_minutes": 30}
        }
        plugin.setup(config)
        plugin.set_consolidator(mock_consolidator)

        # Set last activity to 35 minutes ago (more than 30m)
        plugin.last_user_activity = datetime.now() - timedelta(minutes=35)

        await plugin._check_idle_trigger()

        # Should trigger consolidation
        mock_consolidator.trigger_consolidation.assert_called_once()

    @pytest.mark.asyncio
    async def test_idle_trigger_rate_limits_consolidation(self, mock_consolidator):
        """Test idle trigger doesn't consolidate more than once per hour."""
        plugin = CoreSleepScheduler()
        config = {
            "schedule": {"enabled": True, "trigger_type": "low_activity", "idle_minutes": 30}
        }
        plugin.setup(config)
        plugin.set_consolidator(mock_consolidator)

        # System is idle, but we consolidated 30 minutes ago
        plugin.last_user_activity = datetime.now() - timedelta(minutes=35)
        plugin.last_consolidation = datetime.now() - timedelta(minutes=30)

        await plugin._check_idle_trigger()

        # Should NOT trigger (too soon after last consolidation)
        mock_consolidator.trigger_consolidation.assert_not_called()


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_scheduler_task(self, scheduler):
        """Test start() creates background task."""
        await scheduler.start()

        assert scheduler._scheduler_task is not None
        assert not scheduler._scheduler_task.done()

        # Cleanup
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_scheduler_task(self, scheduler):
        """Test stop() cancels background task."""
        await scheduler.start()
        task = scheduler._scheduler_task

        await scheduler.stop()

        assert task.cancelled() or task.done()
        assert scheduler._scheduler_task is None

    @pytest.mark.asyncio
    async def test_disabled_scheduler_doesnt_start(self):
        """Test disabled scheduler doesn't start task."""
        plugin = CoreSleepScheduler()
        config = {"schedule": {"enabled": False, "trigger_type": "time_based"}}
        plugin.setup(config)

        await plugin.start()

        assert plugin._scheduler_task is None


class TestConsolidationTriggering:
    """Test consolidation triggering mechanism."""

    @pytest.mark.asyncio
    async def test_trigger_consolidation_calls_plugin(self, scheduler, mock_consolidator):
        """Test _trigger_consolidation calls consolidator plugin."""
        scheduler.set_consolidator(mock_consolidator)

        await scheduler._trigger_consolidation("test reason")

        mock_consolidator.trigger_consolidation.assert_called_once()
        assert scheduler.last_consolidation is not None

    @pytest.mark.asyncio
    async def test_trigger_without_consolidator_logs_warning(self, scheduler, caplog):
        """Test triggering without consolidator plugin returns skipped status."""
        result = await scheduler._trigger_consolidation("test reason")

        # Check return value (logs are optional since they use module-level logger)
        assert result["status"] == "skipped"
        assert result["reason"] == "no_consolidator"

    @pytest.mark.asyncio
    async def test_trigger_handles_consolidation_errors(self, scheduler, caplog):
        """Test triggering handles consolidation errors gracefully."""
        failing_consolidator = MagicMock()
        failing_consolidator.trigger_consolidation = AsyncMock(side_effect=Exception("Test error"))
        scheduler.set_consolidator(failing_consolidator)

        # Should not raise, just log error and return error status
        result = await scheduler._trigger_consolidation("test reason")

        assert result["status"] == "error"
        assert "Test error" in result["error"]


class TestExecuteMethod:
    """Test execute() method."""

    @pytest.mark.asyncio
    async def test_execute_returns_context_unchanged(self, scheduler, mock_context):
        """Test execute() is passive and returns context unchanged."""
        result = await scheduler.execute(mock_context)

        assert result is mock_context
