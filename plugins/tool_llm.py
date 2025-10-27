from typing import Optional
import yaml
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import litellm


class LLMTool(BasePlugin):
    """A tool plugin that uses an LLM to generate a response."""

    def __init__(self):
        self.model = "mistralai/mistral-7b-instruct"  # A default fallback
        self.setup(config={})

    @property
    def name(self) -> str:
        return "tool_llm"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Configure the LLM provider from a YAML file."""
        try:
            with open("config/settings.yaml", "r") as f:
                config_data = yaml.safe_load(f)
                self.model = config_data.get("llm", {}).get("model", self.model)
        except FileNotFoundError:
            # Keep default model if config file is not found
            pass
        except Exception as e:
            # Handle other potential errors like parsing errors
            print(f"Error loading config: {e}")

    async def execute(
        self,
        context: SharedContext,
        tools: Optional[list] = None,
        tool_choice: str = "auto",
    ) -> SharedContext:
        """Generate a response using the configured LLM, with optional function calling."""
        if not context.user_input:
            return context

        messages = [
            {"role": "system", "content": "You are Sophia, an Artificial Mindful Intelligence."},
            # For planner calls, history is not needed, but it's here for general use
            *context.history,
        ]

        context.logger.info(f"Calling LLM with {len(messages)} messages.")
        try:
            # Using litellm allows us to easily switch models and providers
            response = await litellm.acompletion(
                model=self.model, messages=messages, tools=tools, tool_choice=tool_choice
            )
            # The response for a tool call is in a different place
            message = response.choices[0].message

            # The planner needs the full message object to check for tool calls.
            # Other consumers (like the responder) just need the text content.
            # Heuristic: if tools were passed, the caller is likely the planner.
            if tools:
                context.payload["llm_response"] = message
            else:
                context.payload["llm_response"] = message.content

            context.logger.info("LLM response received successfully.")
        except Exception as e:
            context.logger.error(f"Error calling LLM: {e}", exc_info=True)
            context.payload["llm_response"] = "I am having trouble thinking right now."

        return context
