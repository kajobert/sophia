import yaml
import os
import re
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import litellm


class LLMTool(BasePlugin):
    """A tool plugin that uses an LLM to generate a response."""

    def __init__(self):
        self.model = "mistralai/mistral-7b-instruct"  # A default fallback
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
    
    def _resolve_env_vars(self, value: str) -> str:
        """
        Resolves environment variables in the format ${VAR_NAME}.
        
        SECURITY: This allows API keys to be stored in environment variables
        instead of plain text in config files.
        
        Args:
            value: String that may contain ${VAR_NAME} patterns.
            
        Returns:
            String with ${VAR_NAME} replaced by actual environment variable values.
        """
        def replacer(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ValueError(f"Environment variable '{var_name}' is not set")
            return env_value
        
        return re.sub(r'\$\{([^}]+)\}', replacer, value)

    def setup(self, config: dict) -> None:
        """Configure the LLM provider from a YAML file."""
        try:
            with open("config/settings.yaml", "r") as f:
                config_data = yaml.safe_load(f)
                llm_config = config_data.get("llm", {})
                
                self.model = llm_config.get("model", self.model)
                
                # SECURITY: Resolve API key from environment variable if present
                api_key_config = llm_config.get("api_key")
                if api_key_config:
                    try:
                        self.api_key = self._resolve_env_vars(api_key_config)
                        # Set for litellm
                        os.environ["OPENROUTER_API_KEY"] = self.api_key
                    except ValueError as e:
                        print(f"Warning: {e}. LLM may not work without API key.")
                        
        except FileNotFoundError:
            # Keep default model if config file is not found
            pass
        except Exception as e:
            # Handle other potential errors like parsing errors
            print(f"Error loading config: {e}")

    async def execute(self, context: SharedContext) -> SharedContext:
        """Generate a response using the configured LLM."""
        if not context.user_input:
            return context

        messages = [
            {"role": "system", "content": "You are Sophia, an Artificial Mindful Intelligence."},
            *context.history,
        ]

        context.logger.info(f"Calling LLM with {len(messages)} messages.")
        try:
            # Using litellm allows us to easily switch models and providers
            response = await litellm.acompletion(model=self.model, messages=messages)
            llm_response = response.choices[0].message.content
            context.payload["llm_response"] = llm_response
            context.logger.info("LLM response received successfully.")
        except Exception as e:
            context.logger.error(f"Error calling LLM: {e}", exc_info=True)
            context.payload["llm_response"] = "I am having trouble thinking right now."

        return context
