import os
import yaml
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import litellm


class LLMTool(BasePlugin):
    """A tool plugin that uses an LLM to generate a response."""

    def __init__(self):
        self.model = "mistralai/mistral-7b-instruct"  # A default fallback
        self.system_prompt = "You are a helpful assistant."
        self.api_key = None
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
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute",
                    "description": (
                        "For general text generation, summarization, reformatting, or "
                        "any other language-based task. The text to be processed must "
                        "be passed in the context payload."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "object",
                                "description": (
                                    "The shared context containing the prompt in its payload."
                                ),
                            },
                        },
                        "required": ["context"],
                    },
                },
            }
        ]

    async def execute(self, *, context: SharedContext) -> SharedContext:
        """
        Generate a response using the configured LLM.
        This method is now compatible with the BasePlugin and expects all
        arguments to be passed within the context.payload.
        """
        prompt = context.payload.get("prompt")
        tools = context.payload.get("tools")
        tool_choice = context.payload.get("tool_choice")

        # Determine the final input for the LLM.
        llm_input = prompt if prompt is not None else context.user_input
        if not llm_input:
            context.payload["llm_response"] = "Error: No input provided to LLMTool."
            return context

        # Base messages include system prompt and the history from the context.
        messages = [
            {"role": "system", "content": self.system_prompt},
            *context.history,
        ]

        if prompt is not None:
            messages.append({"role": "user", "content": prompt})

        context.logger.info(
            f"Calling LLM with {len(messages)} messages.", extra={"plugin_name": self.name}
        )
        try:
            completion_kwargs = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "api_key": self.api_key,
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
