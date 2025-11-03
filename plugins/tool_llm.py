import os
import yaml
import logging
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.logging_filter import SessionIdFilter
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

        # --- Logging fix for litellm ---
        # litellm uses the root logger, which can cause issues with structured
        # logging if it's not configured with the session_id.
        # This fix injects the SessionIdFilter into the root logger.
        root_logger = logging.getLogger()
        # Add filter only if it's not already there to prevent duplicates
        if not any(isinstance(f, SessionIdFilter) for f in root_logger.filters):
            root_logger.addFilter(SessionIdFilter())
        
        # Configure litellm logger separately with a simple formatter to avoid session_id KeyError
        litellm_logger = logging.getLogger("LiteLLM")
        litellm_logger.setLevel(logging.WARNING)  # Reduce noise, only show warnings/errors
        # Remove any handlers that might have the problematic formatter
        litellm_logger.handlers.clear()
        litellm_logger.propagate = False  # Don't propagate to root logger
        # Add a simple console handler with no session_id requirement
        console_handler = logging.StreamHandler()
        simple_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(simple_formatter)
        litellm_logger.addHandler(console_handler)

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
        Accepts an optional 'model_config' in the payload to override the default model.
        """
        prompt = context.payload.get("prompt", context.user_input)
        tools = context.payload.get("tools")
        tool_choice = context.payload.get("tool_choice")
        model_config = context.payload.get("model_config", {})

        # Determine the model to use: payload override > default
        model_to_use = model_config.get("model", self.model)

        if not prompt:
            context.payload["llm_response"] = "Error: No input provided to LLMTool."
            return context

        messages = [{"role": "system", "content": self.system_prompt}, *context.history]
        if not any(msg["role"] == "user" and msg["content"] == prompt for msg in messages):
             messages.append({"role": "user", "content": prompt})

        context.logger.info(
            f"Calling LLM '{model_to_use}' with {len(messages)} messages.",
            extra={"plugin_name": self.name}
        )
        try:
            completion_kwargs = {
                "model": model_to_use,
                "messages": messages,
                "tools": tools,
                "api_key": self.api_key,
                "timeout": 60,  # Add a timeout
            }
            if tool_choice:
                completion_kwargs["tool_choice"] = tool_choice

            response = await litellm.acompletion(**completion_kwargs)
            message = response.choices[0].message

            # Store metadata
            usage = response.usage
            
            # Try to calculate cost, but don't fail if model isn't in price database
            try:
                cost = litellm.completion_cost(completion_response=response)
            except Exception as cost_error:
                context.logger.warning(f"Could not calculate cost for model '{model_to_use}': {cost_error}", extra={"plugin_name": self.name})
                cost = 0.0  # Unknown cost
            
            context.payload["llm_response_metadata"] = {
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": cost,
            }

            if message.tool_calls:
                context.payload["llm_response"] = message.tool_calls
            else:
                context.payload["llm_response"] = message.content

            context.logger.info("LLM response received successfully.", extra={"plugin_name": self.name})
        except Exception as e:
            context.logger.error(f"Error calling LLM '{model_to_use}': {e}", exc_info=True, extra={"plugin_name": self.name})
            context.payload["llm_response"] = f"I am having trouble thinking right now. Error: {e}"
            context.payload["llm_response_metadata"] = {}

        return context
