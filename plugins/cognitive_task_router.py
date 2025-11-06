# plugins/cognitive_task_router.py
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import calendar

import yaml
import os
from core.context import SharedContext
from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class CognitiveTaskRouter(BasePlugin):
    """
    A cognitive plugin that routes tasks to the most appropriate LLM
    based on a predefined strategy WITH budget awareness.
    
    Version 2.5 Features:
    - Daily budget pacing (prevent spending $25 in 2 hours)
    - Phase-based strategy (conservative → balanced → aggressive)
    - Monthly spend tracking from operation_tracking table
    - Auto-switch to local LLM when daily or monthly budget exceeded
    - Emits BUDGET_WARNING and BUDGET_PACE_WARNING events
    """

    @property
    def name(self) -> str:
        return "cognitive_task_router"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "2.5"

    def __init__(self) -> None:
        """Initializes the CognitiveTaskRouter."""
        super().__init__()
        self.strategies: List[Dict[str, Any]] = []
        self.default_strategy: Optional[Dict[str, Any]] = None
        self.plugins: Dict[str, "BasePlugin"] = {}
        
        # Monthly budget tracking
        self.monthly_limit = 30.0  # $30/month default
        self.monthly_spent = 0.0
        self.last_budget_check = None
        self.budget_warning_thresholds = [0.5, 0.8, 0.9]  # 50%, 80%, 90%
        self.warned_thresholds = set()
        
        # Daily budget pacing (NEW in v2.5)
        self.daily_budget_cache = {}  # {date: {limit, spent, warned}}
        self.pacing_enabled = True
        self.safety_buffer_pct = 0.20  # 20% safety reserve
        self.current_phase = "conservative"  # conservative|balanced|aggressive
        self.phase_config = {
            "conservative": {"days": [1, 10], "local_pct": 0.70},
            "balanced": {"days": [11, 20], "local_pct": 0.50},
            "aggressive": {"days": [21, 31], "local_pct": 0.30}
        }
        
        # Event bus (optional)
        self.event_bus = None

    def setup(self, config: Dict[str, Any]) -> None:
        """
        Loads the model routing strategies from the configuration file.
        Also loads budget limits from autonomy.yaml.

        Args:
            config: The configuration dictionary.
        """
        self.plugins = config.get("all_plugins", {})
        
        # Get event bus if available
        self.event_bus = config.get("event_bus")
        
        # Load routing strategies
        strategy_path = "config/model_strategy.yaml"
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_config = yaml.safe_load(f)
            self.strategies = strategy_config.get("task_strategies", [])
            # Set the default strategy to the one for 'plan_generation'
            for strategy in self.strategies:
                if strategy.get("task_type") == "plan_generation":
                    self.default_strategy = strategy
                    break
            if not self.default_strategy and self.strategies:
                # Fallback to the first strategy if 'generovani_planu' is not found
                self.default_strategy = self.strategies[0]

        except FileNotFoundError:
            logger.error(
                f"Model strategy file not found at {strategy_path}",
                extra={"plugin_name": self.name},
            )
        except Exception as e:
            logger.error(
                f"Error loading model strategies: {e}",
                extra={"plugin_name": self.name},
            )
        
        # Load budget configuration from autonomy.yaml
        autonomy_path = "config/autonomy.yaml"
        try:
            if Path(autonomy_path).exists():
                with open(autonomy_path, "r", encoding="utf-8") as f:
                    autonomy_config = yaml.safe_load(f)
                
                budget_config = autonomy_config.get("autonomy", {}).get("budget", {})
                self.monthly_limit = budget_config.get("monthly_limit_usd", 30.0)
                
                # Load pacing config (NEW in v2.5)
                pacing_config = budget_config.get("pacing", {})
                self.pacing_enabled = pacing_config.get("enabled", True)
                self.safety_buffer_pct = pacing_config.get("safety_buffer_pct", 20) / 100.0
                
                # Load phase configuration
                phases_config = pacing_config.get("phases", {})
                if phases_config:
                    self.phase_config = phases_config
                
                logger.info(
                    f"[TaskRouter v2.5] Budget tracking enabled: ${self.monthly_limit}/month, "
                    f"daily pacing: {self.pacing_enabled}, safety buffer: {self.safety_buffer_pct*100:.0f}%",
                    extra={"plugin_name": self.name}
                )
            else:
                logger.warning(
                    f"[TaskRouter] {autonomy_path} not found, using default budget ${self.monthly_limit}",
                    extra={"plugin_name": self.name}
                )
        except Exception as e:
            logger.warning(
                f"[TaskRouter] Error loading budget config: {e}",
                extra={"plugin_name": self.name}
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Analyzes the user input and selects the best LLM for the task.
        
        NEW: Checks budget and forces local LLM when budget > 80% used.

        This method classifies the user's request, selects a model based
        on the configured strategies, and updates the shared context with
        the chosen model configuration.

        Args:
            context: The shared context containing the user input.

        Returns:
            The updated SharedContext with the selected model config.
        """

        if not context.user_input:
            context.logger.warning(
                "No user input found in context. Skipping routing.",
                extra={"plugin_name": self.name},
            )
            return context

        if not self.strategies or not self.default_strategy:
            context.logger.error(
                "No model strategies loaded. Skipping routing.",
                extra={"plugin_name": self.name},
            )
            return context

        # === BUDGET AWARENESS (v2.5) ===
        # Check monthly budget and update spend tracking
        await self._check_monthly_budget(context)
        
        # Check daily pacing (NEW in v2.5)
        today_spent, daily_limit, overspent = await self._check_daily_pacing(context)
        
        # Calculate current phase strategy
        current_phase = self._calculate_phase_strategy()
        if current_phase != self.current_phase:
            self.current_phase = current_phase
            context.logger.info(
                f"[TaskRouter] 📅 Budget phase changed to: {current_phase}",
                extra={"plugin_name": self.name}
            )
            
            # Emit phase change event
            if self.event_bus:
                from core.events import Event, EventType
                self.event_bus.publish(Event(
                    event_type=EventType.BUDGET_PHASE_CHANGED,
                    data={"phase": current_phase, "day": datetime.now().day}
                ))
        
        # Determine if we should force local based on budget
        budget_usage_percent = (self.monthly_spent / self.monthly_limit) if self.monthly_limit > 0 else 0
        force_local_monthly = budget_usage_percent >= 0.8  # 80% monthly threshold
        force_local_daily = overspent  # Daily overspend
        
        force_local_due_to_budget = force_local_monthly or force_local_daily
        
        if force_local_due_to_budget:
            reason = "daily overspend" if force_local_daily else f"monthly {budget_usage_percent*100:.1f}%"
            context.logger.warning(
                f"[TaskRouter] 🚨 Forcing local LLM due to {reason}",
                extra={"plugin_name": self.name}
            )
            context.offline_mode = True  # Force offline routing
        
        # Decide offline/local-only policy. Honor explicit payload flags
        force_local = os.getenv("SOPHIA_FORCE_LOCAL_ONLY", "false").lower() == "true"
        allow_cloud_payload = False
        try:
            allow_cloud_payload = bool(context.payload.get("allow_cloud", False))
        except Exception:
            allow_cloud_payload = False

        # If forced local-only and not explicitly allowed by payload or a user-originated task,
        # treat this as offline mode for routing decisions.
        if force_local and not allow_cloud_payload and context.payload.get("origin") != "user_input":
            context.offline_mode = True

        # Select LLM based on offline mode
        if context.offline_mode:
            llm_tool = self.plugins.get("tool_local_llm")
            if not llm_tool:
                context.logger.error(
                    "Offline mode enabled but tool_local_llm not available!",
                    extra={"plugin_name": self.name}
                )
                return context
            
            reason = "budget limit" if force_local_due_to_budget else "offline mode"
            context.logger.info(
                f"🔒 Task router using local LLM ({reason})",
                extra={"plugin_name": self.name}
            )
            
            # Skip classification, use local LLM directly
            if "model_config" not in context.payload:
                context.payload["model_config"] = {}
            context.payload["model_config"]["model"] = "local"
            context.payload["model_config"]["provider"] = "ollama"
            
            return context
        else:
            llm_tool = self.plugins.get("tool_llm")
            if not llm_tool:
                context.logger.error(
                    "LLMTool plugin not found. Skipping routing.",
                    extra={"plugin_name": self.name},
                )
                return context

        try:
            # Dynamically build the prompt for the LLM
            prompt = self._build_classification_prompt(context.user_input)
            llm_context = SharedContext(
                session_id=context.session_id,
                current_state=context.current_state,
                logger=context.logger,
                user_input=prompt,
                payload={"model_config": {"model": "openrouter/anthropic/claude-3-haiku"}},
            )
            classification_response = await llm_tool.execute(context=llm_context)
            classified_task_type = classification_response.payload.get("llm_response", "").strip()

            # Find the strategy for the classified task type
            selected_strategy = next(
                (s for s in self.strategies if s["task_type"] == classified_task_type),
                None,
            )

            if selected_strategy:
                context.logger.info(
                    f"Task classified as '{classified_task_type}'. "
                    f"Using model: {selected_strategy['model']}",
                    extra={"plugin_name": self.name},
                )
                model_to_use = selected_strategy["model"]
            else:
                context.logger.warning(
                    f"Could not classify task. Defaulting to high-quality model. "
                    f"LLM response: '{classified_task_type}'",
                    extra={"plugin_name": self.name},
                )
                model_to_use = self.default_strategy["model"]

            # Update the context payload with the selected model
            if "model_config" not in context.payload:
                context.payload["model_config"] = {}
            context.payload["model_config"]["model"] = model_to_use

        except Exception as e:
            context.logger.error(
                f"Error during task routing: {e}. Defaulting to high-quality model.",
                extra={"plugin_name": self.name},
            )
            if self.default_strategy:
                context.payload["model_config"] = {"model": self.default_strategy["model"]}

        return context

    async def _check_monthly_budget(self, context: SharedContext) -> None:
        """
        Check monthly budget usage from operation_tracking table.
        
        Updates self.monthly_spent and emits BUDGET_WARNING events
        when crossing thresholds (50%, 80%, 90%).
        
        Args:
            context: Shared context for logging
        """
        # Only check budget once per hour (cache)
        now = datetime.now()
        if self.last_budget_check:
            time_since_check = (now - self.last_budget_check).total_seconds()
            if time_since_check < 3600:  # 1 hour cache
                return
        
        self.last_budget_check = now
        
        try:
            # Get memory plugin for database access
            memory_plugin = self.plugins.get("memory_sqlite")
            if not memory_plugin:
                context.logger.warning(
                    "[TaskRouter] memory_sqlite plugin not available, cannot track budget",
                    extra={"plugin_name": self.name}
                )
                return
            
            # Calculate start of current month
            first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = first_day_of_month.isoformat()
            
            # Query operation_tracking for this month's operations
            # NOTE: This assumes cost tracking is implemented in operation_metadata
            # For now, we estimate based on token counts (rough approximation)
            from sqlalchemy import select, and_
            
            with memory_plugin.engine.connect() as conn:
                stmt = select(memory_plugin.operation_tracking_table).where(
                    and_(
                        memory_plugin.operation_tracking_table.c.timestamp >= cutoff_date,
                        memory_plugin.operation_tracking_table.c.offline_mode == False  # Only cloud calls cost money
                    )
                )
                
                operations = conn.execute(stmt).fetchall()
                
                # Estimate cost: ~$0.15 per 1M tokens for cheap models
                # This is VERY rough - real cost tracking should use actual model prices
                total_tokens = 0
                for op in operations:
                    # op[12] = prompt_tokens, op[13] = completion_tokens
                    prompt_tokens = op[12] if op[12] else 0
                    completion_tokens = op[13] if op[13] else 0
                    total_tokens += prompt_tokens + completion_tokens
                
                # Rough cost estimate (will be replaced with real tracking later)
                estimated_cost = (total_tokens / 1_000_000) * 0.15  # $0.15 per 1M tokens avg
                
                self.monthly_spent = estimated_cost
                
                context.logger.info(
                    f"[TaskRouter] 💰 Monthly budget: ${self.monthly_spent:.2f}/${self.monthly_limit:.2f} "
                    f"({(self.monthly_spent/self.monthly_limit*100):.1f}% used)",
                    extra={"plugin_name": self.name}
                )
                
                # Check thresholds and emit warnings
                usage_percent = self.monthly_spent / self.monthly_limit if self.monthly_limit > 0 else 0
                
                for threshold in self.budget_warning_thresholds:
                    if usage_percent >= threshold and threshold not in self.warned_thresholds:
                        self.warned_thresholds.add(threshold)
                        
                        warning_msg = (
                            f"Budget warning: {usage_percent*100:.1f}% used "
                            f"(${self.monthly_spent:.2f}/${self.monthly_limit:.2f})"
                        )
                        
                        context.logger.warning(
                            f"[TaskRouter] 🚨 {warning_msg}",
                            extra={"plugin_name": self.name}
                        )
                        
                        # Emit BUDGET_WARNING event if event bus available
                        if self.event_bus:
                            from core.events import Event, EventType
                            self.event_bus.publish(Event(
                                event_type=EventType.BUDGET_WARNING,
                                data={
                                    "threshold": threshold,
                                    "spent": self.monthly_spent,
                                    "limit": self.monthly_limit,
                                    "usage_percent": usage_percent,
                                    "message": warning_msg
                                }
                            ))
                        
                        # Auto-pause expensive operations at 100%
                        if usage_percent >= 1.0:
                            context.logger.error(
                                f"[TaskRouter] 🛑 BUDGET LIMIT REACHED - forcing local-only mode",
                                extra={"plugin_name": self.name}
                            )
                
        except Exception as e:
            context.logger.error(
                f"[TaskRouter] Error checking budget: {e}",
                extra={"plugin_name": self.name}
            )

    def _calculate_daily_budget_limit(self) -> float:
        """
        Calculate recommended daily budget based on remaining days in month.
        
        Formula: (monthly_limit - monthly_spent) / days_remaining * (1 - safety_buffer)
        
        Returns:
            float: Recommended daily budget in USD
        """
        now = datetime.now()
        
        # Days left in current month
        last_day = calendar.monthrange(now.year, now.month)[1]
        days_remaining = last_day - now.day + 1
        
        # Budget remaining
        budget_remaining = self.monthly_limit - self.monthly_spent
        
        if budget_remaining <= 0:
            return 0.0  # Budget exhausted
        
        if days_remaining <= 0:
            return budget_remaining  # Last day - use all remaining
        
        # Recommended daily limit with safety buffer
        daily_limit = (budget_remaining / days_remaining) * (1 - self.safety_buffer_pct)
        
        return max(0.0, daily_limit)
    
    async def _check_daily_pacing(self, context: SharedContext) -> tuple:
        """
        Check if today's spending is on track with daily budget limit.
        
        Args:
            context: Shared context for logging
            
        Returns:
            tuple: (today_spent, daily_limit, overspent)
        """
        if not self.pacing_enabled:
            return (0.0, 0.0, False)
        
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        # Get or initialize today's cache
        if today_str not in self.daily_budget_cache:
            self.daily_budget_cache[today_str] = {
                "limit": self._calculate_daily_budget_limit(),
                "spent": 0.0,
                "warned": False
            }
        
        today_cache = self.daily_budget_cache[today_str]
        
        try:
            # Get memory plugin for database access
            memory_plugin = self.plugins.get("memory_sqlite")
            if not memory_plugin:
                return (0.0, today_cache["limit"], False)
            
            # Calculate start of today
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = today_start.isoformat()
            
            # Query today's operations
            from sqlalchemy import select, and_
            
            with memory_plugin.engine.connect() as conn:
                stmt = select(memory_plugin.operation_tracking_table).where(
                    and_(
                        memory_plugin.operation_tracking_table.c.timestamp >= cutoff_date,
                        memory_plugin.operation_tracking_table.c.offline_mode == False
                    )
                )
                
                today_ops = conn.execute(stmt).fetchall()
                
                # Calculate today's spend
                total_tokens = 0
                for op in today_ops:
                    prompt_tokens = op[12] if op[12] else 0
                    completion_tokens = op[13] if op[13] else 0
                    total_tokens += prompt_tokens + completion_tokens
                
                today_spent = (total_tokens / 1_000_000) * 0.15  # Rough estimate
                
                # Update cache
                today_cache["spent"] = today_spent
                
                # Check if overspending
                overspent = today_spent > (today_cache["limit"] * 1.5)  # 150% threshold
                
                # Emit warning if needed
                if overspent and not today_cache["warned"]:
                    today_cache["warned"] = True
                    
                    warning_msg = (
                        f"Daily budget overspend: ${today_spent:.2f} spent "
                        f"(recommended: ${today_cache['limit']:.2f})"
                    )
                    
                    context.logger.warning(
                        f"[TaskRouter] ⚠️ {warning_msg}",
                        extra={"plugin_name": self.name}
                    )
                    
                    # Emit BUDGET_PACE_WARNING event
                    if self.event_bus:
                        from core.events import Event, EventType
                        self.event_bus.publish(Event(
                            event_type=EventType.BUDGET_PACE_WARNING,
                            data={
                                "today_spent": today_spent,
                                "daily_limit": today_cache["limit"],
                                "overspend_pct": (today_spent / today_cache["limit"] - 1) * 100,
                                "message": warning_msg
                            }
                        ))
                
                return (today_spent, today_cache["limit"], overspent)
                
        except Exception as e:
            context.logger.error(
                f"[TaskRouter] Error checking daily pacing: {e}",
                extra={"plugin_name": self.name}
            )
            return (0.0, today_cache["limit"], False)
    
    def _calculate_phase_strategy(self) -> str:
        """
        Determine which phase of the month we're in.
        
        Phases:
        - conservative (days 1-10): Prefer local LLM (70% local)
        - balanced (days 11-20): Balanced routing (50% local)
        - aggressive (days 21-31): Use remaining budget (30% local)
        
        Returns:
            str: Phase name (conservative|balanced|aggressive)
        """
        now = datetime.now()
        day_of_month = now.day
        
        for phase_name, phase_config in self.phase_config.items():
            day_range = phase_config.get("days", [])
            if len(day_range) == 2 and day_range[0] <= day_of_month <= day_range[1]:
                return phase_name
        
        return "balanced"  # Default fallback

    def _build_classification_prompt(self, user_input: str) -> str:
        """Builds the prompt for the classification LLM."""
        prompt_path = "config/prompts/classify_task_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        strategy_descriptions = "\n".join(
            [f"- {s['task_type']}: {s['description']}" for s in self.strategies]
        )
        return prompt_template.format(strategies=strategy_descriptions, user_input=user_input)

    def get_model_for_task(self, task_type: str) -> str:
        """Gets the model for a given task type."""
        selected_strategy = next(
            (s for s in self.strategies if s["task_type"] == task_type),
            None,
        )
        if selected_strategy:
            return selected_strategy["model"]
        elif self.default_strategy:
            return self.default_strategy["model"]
        else:
            return "openrouter/anthropic/claude-3-haiku"
