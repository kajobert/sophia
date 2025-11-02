# plugins/cognitive_task_router.py
import logging
from typing import Any, Dict, List, Optional

import yaml

from core.context import SharedContext
from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class CognitiveTaskRouter(BasePlugin):
    """
    A cognitive plugin that routes tasks to the most appropriate LLM
    based on a predefined strategy.
    """

    name: str = "cognitive_task_router"
    version: str = "1.0"
    plugin_type: PluginType = PluginType.COGNITIVE

    def __init__(self) -> None:
        """Initializes the CognitiveTaskRouter."""
        super().__init__()
        self.strategies: List[Dict[str, Any]] = []
        self.default_strategy: Optional[Dict[str, Any]] = None
        self.plugins: Dict[str, "BasePlugin"] = {}

    def setup(self, config: Dict[str, Any]) -> None:
        """
        Loads the model routing strategies from the configuration file.

        Args:
            config: The configuration dictionary.
        """
        self.plugins = config.get("plugins", {})
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

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Analyzes the user input and selects the best LLM for the task.

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
