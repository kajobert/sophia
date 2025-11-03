"""
Sleep Cycle Scheduler Plugin

Schedules and triggers memory consolidation ("dreaming") at configurable intervals.
Integrates with EventDrivenLoop to run consolidation during low-activity periods.

Version: 1.0.0
Phase: 3 - Memory Consolidation & Dreaming
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.event_bus import EventBus


logger = logging.getLogger(__name__)


class SleepCycleTrigger(Enum):
    """When to trigger memory consolidation."""
    TIME_BASED = "time_based"          # Every N hours
    LOW_ACTIVITY = "low_activity"      # No user input for N minutes
    SESSION_END = "session_end"        # When session ends
    MANUAL = "manual"                  # Manually triggered


class SleepScheduleConfig(BaseModel):
    """Configuration for sleep cycle scheduling."""
    enabled: bool = True
    trigger_type: SleepCycleTrigger = SleepCycleTrigger.TIME_BASED
    interval_hours: int = 6              # For TIME_BASED
    idle_minutes: int = 30               # For LOW_ACTIVITY


class CoreSleepScheduler(BasePlugin):
    """
    Core Sleep Scheduler Plugin
    
    Autonomously schedules memory consolidation based on configurable triggers.
    Monitors system activity and triggers consolidation during appropriate times.
    
    No LLM tools - this is a purely autonomous background system.
    """

    @property
    def name(self) -> str:
        """Returns the unique name of the plugin."""
        return "core_sleep_scheduler"

    @property
    def plugin_type(self) -> PluginType:
        """Returns the type of the plugin."""
        return PluginType.CORE

    @property
    def version(self) -> str:
        """Returns the version of the plugin."""
        return "1.0.0"
    
    def setup(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sleep scheduler.
        
        Args:
            config: Plugin configuration
        """
        self.config = SleepScheduleConfig(**config.get("schedule", {}))
        self.event_bus: Optional[EventBus] = None
        self.consolidator_plugin = None
        
        # Tracking
        self.last_user_activity: datetime = datetime.now()
        self.last_consolidation: Optional[datetime] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"Sleep Scheduler initialized (trigger={self.config.trigger_type.value}, "
            f"interval={self.config.interval_hours}h)"
        )
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Inject EventBus dependency."""
        self.event_bus = event_bus
        
        # Subscribe to USER_INPUT to track activity
        from core.events import EventType
        self.event_bus.subscribe(EventType.USER_INPUT, self._on_user_activity)
    
    def set_consolidator(self, consolidator) -> None:
        """
        Inject memory consolidator plugin dependency.
        
        Args:
            consolidator: CognitiveMemoryConsolidator instance
        """
        self.consolidator_plugin = consolidator
    
    async def _on_user_activity(self, event) -> None:
        """
        Track user activity for idle detection.
        
        Args:
            event: USER_INPUT event
        """
        self.last_user_activity = datetime.now()
        logger.debug(f"User activity detected at {self.last_user_activity}")
    
    async def start(self) -> None:
        """Start the sleep cycle scheduler."""
        if not self.config.enabled:
            logger.info("Sleep scheduler disabled in config")
            return
        
        if self._scheduler_task is not None:
            logger.warning("Sleep scheduler already running")
            return
        
        logger.info("🛌 Sleep scheduler started")
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
    
    async def stop(self) -> None:
        """Stop the sleep cycle scheduler."""
        if self._scheduler_task is None:
            return
        
        logger.info("Sleep scheduler stopping...")
        self._scheduler_task.cancel()
        
        try:
            await self._scheduler_task
        except asyncio.CancelledError:
            pass
        
        self._scheduler_task = None
        logger.info("Sleep scheduler stopped")
    
    async def _run_scheduler(self) -> None:
        """
        Main scheduler loop.
        
        Monitors conditions and triggers consolidation when appropriate.
        """
        try:
            while True:
                if self.config.trigger_type == SleepCycleTrigger.TIME_BASED:
                    await self._check_time_based_trigger()
                    # Check every 10 minutes
                    await asyncio.sleep(600)
                
                elif self.config.trigger_type == SleepCycleTrigger.LOW_ACTIVITY:
                    await self._check_idle_trigger()
                    # Check every minute
                    await asyncio.sleep(60)
                
                else:
                    # SESSION_END and MANUAL don't need polling
                    await asyncio.sleep(3600)  # Sleep 1 hour
        
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}", exc_info=True)
    
    async def _check_time_based_trigger(self) -> None:
        """Check if it's time for a scheduled consolidation."""
        if self.last_consolidation is None:
            # Never consolidated - trigger now
            await self._trigger_consolidation("Initial consolidation")
            return
        
        elapsed = datetime.now() - self.last_consolidation
        required = timedelta(hours=self.config.interval_hours)
        
        if elapsed >= required:
            await self._trigger_consolidation(
                f"Scheduled consolidation ({self.config.interval_hours}h elapsed)"
            )
    
    async def _check_idle_trigger(self) -> None:
        """Check if system has been idle long enough."""
        idle_time = datetime.now() - self.last_user_activity
        required_idle = timedelta(minutes=self.config.idle_minutes)
        
        if idle_time >= required_idle:
            # Check if we've consolidated recently
            if self.last_consolidation:
                since_last = datetime.now() - self.last_consolidation
                # Don't consolidate more than once per hour
                if since_last < timedelta(hours=1):
                    return
            
            await self._trigger_consolidation(
                f"Idle consolidation ({self.config.idle_minutes}m idle)"
            )
    
    async def _trigger_consolidation(self, reason: str) -> None:
        """
        Trigger memory consolidation.
        
        Args:
            reason: Why consolidation is being triggered
        """
        if not self.consolidator_plugin:
            logger.warning("Cannot trigger consolidation - no consolidator plugin")
            return
        
        logger.info(f"💤 Triggering consolidation: {reason}")
        
        try:
            metrics = await self.consolidator_plugin.trigger_consolidation()
            self.last_consolidation = datetime.now()
            
            logger.info(
                f"✨ Consolidation complete: {metrics.memories_created} memories created "
                f"in {metrics.duration_seconds:.1f}s"
            )
        
        except Exception as e:
            logger.error(f"❌ Consolidation failed: {e}", exc_info=True)
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Sleep scheduler is autonomous - doesn't process context.
        
        Args:
            context: Shared context object
            
        Returns:
            Unchanged context
        """
        return context
    
    def get_tool_definitions(self) -> list:
        """No LLM tools - purely autonomous."""
        return []
