from typing import Optional
import yaml
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import litellm


class LLMTool(BasePlugin):
    """A tool plugin that uses an LLM to generate a response."""

    def __init__(self):
        self.model = "mistralai/mistral-7b-instruct"  # A default fallback
        self.system_prompt = "You are a helpful assistant."
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

        try:
            with open("config/prompts/sophia_dna.txt", "r") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            # Keep default system prompt if file not found
            pass

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute",
                    "description": "For general text generation, summarization, reformatting, or any other language-based task. The text to be processed must be passed as the 'prompt' argument.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The text prompt to process for the language model.",
                            },
                        },
                        "required": ["prompt"],
                    },
                },
            }
        ]

    async def execute(
        self,
        *,  # Make arguments keyword-only
        context: SharedContext,
        prompt: Optional[str] = None,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
    ) -> SharedContext:
        """
        Generate a response using the configured LLM.

        This method is called in two primary ways:
        1. By the Kernel as a planned tool: `prompt` is provided from the plan's
           arguments, and `context` is injected.
        2. By other plugins (e.g., CognitivePlanner): `context` is provided directly,
           and the input is taken from `context.user_input`.
        """
        # Determine the final input for the LLM. Prioritize the 'prompt' argument
        # from a tool call, fall back to the general user_input in the context.
        llm_input = prompt if prompt is not None else context.user_input
        if not llm_input:
            context.payload["llm_response"] = "Error: No input provided to LLMTool."
            return context

        # Base messages include system prompt and the history from the context.
        messages = [
            {"role": "system", "content": self.system_prompt},
            *context.history,
        ]

        # If this is a tool call, 'prompt' will be set. The history contains the
        # original user input, but the *actual* input for this specific LLM call
        # is the 'prompt' argument. We append it as the final user message.
        if prompt is not None:
            messages.append({"role": "user", "content": prompt})

        # If it's a call from the planner, prompt is None. The kernel ensures
        # that history already contains the latest user_input, so we don't add it again.

        context.logger.info(f"Calling LLM with {len(messages)} messages.", extra={"plugin_name": self.name})
        try:
            completion_kwargs = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
            }
            if tool_choice:
                completion_kwargs["tool_choice"] = tool_choice

            response = await litellm.acompletion(**completion_kwargs)
            message = response.choices[0].message

            if tools:
                context.payload["llm_response"] = message
            else:
                context.payload["llm_response"] = message.content

            context.logger.info("LLM response received successfully.", extra={"plugin_name": self.name})
        except Exception as e:
            context.logger.error(f"Error calling LLM: {e}", exc_info=True, extra={"plugin_name": self.name})
            context.payload["llm_response"] = "I am having trouble thinking right now."

        return context
