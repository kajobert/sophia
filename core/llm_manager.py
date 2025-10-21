import os
import yaml
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
from core.llm_adapters import OpenRouterAdapter
from core.gemini_adapter import GeminiAdapter

# Use the logger configured in run.py
logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self, project_root: str = "."):
        logger.info("Initializing LLMManager...")
        self.project_root = os.path.abspath(project_root)
        self._openrouter_client = None
        self._gemini_adapter = None
        self._load_config()

        llm_config = self.config.get("llm_models", {})
        self.models_config = llm_config.get("models", {})
        self.aliases = llm_config.get("aliases", {})
        self.default_model_name = llm_config.get("default", None)
        self.fallback_models = llm_config.get("fallback_models", [])
        logger.info(f"LLM config loaded: {len(self.models_config)} models, {len(self.aliases)} aliases.")

        self._initialize_clients()

    def _load_config(self):
        config_path = os.path.join(self.project_root, "config/config.yaml")
        logger.info(f"Loading config from: {config_path}")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
            logger.error("Config file 'config.yaml' not found!")
            raise RuntimeError("Config file 'config.yaml' not found.")

    def _initialize_clients(self):
        logger.info("Initializing LLM provider clients...")
        dotenv_path = os.path.join(self.project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        if gemini_api_key:
            try:
                self._gemini_adapter = GeminiAdapter(api_key=gemini_api_key)
                logger.info(f"Gemini adapter initialized successfully: {self._gemini_adapter.model_name}")
            except Exception as e:
                logger.error("Gemini initialization failed.", exc_info=True)
                self._gemini_adapter = None
        
        if openrouter_api_key:
            try:
                self._openrouter_client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_api_key,
                )
                logger.info("OpenRouter client initialized successfully.")
            except Exception as e:
                logger.error("OpenRouter initialization failed.", exc_info=True)
                self._openrouter_client = None
        
        if not self._gemini_adapter and not self._openrouter_client:
            logger.critical("No LLM provider is available. Set GEMINI_API_KEY or OPENROUTER_API_KEY.")
            raise ValueError("No LLM provider is available.")

    def get_llm(self, name: str = None):
        model_alias = name or self.default_model_name
        logger.info(f"Request for LLM with alias: '{model_alias}'")
        if not model_alias:
            logger.error("No default model or alias provided.")
            raise ValueError("No default model or alias defined.")

        actual_model_name = self.aliases.get(model_alias, model_alias)
        logger.info(f"Alias '{model_alias}' resolved to model name: '{actual_model_name}'")

        is_gemini_model = "gemini" in actual_model_name.lower()
        
        if is_gemini_model and self._gemini_adapter:
            logger.info(f"Using Gemini adapter for model '{actual_model_name}'.")
            return self._gemini_adapter
        
        if self._openrouter_client:
            logger.info(f"Using OpenRouter adapter for model '{actual_model_name}'.")
            if actual_model_name not in self.models_config:
                logger.error(f"Model '{actual_model_name}' not found in 'config.yaml' models section.")
                raise ValueError(f"Model '{actual_model_name}' not found in config.")

            model_specific_config = self.models_config.get(actual_model_name) or {}
            logger.info(f"Found config for model '{actual_model_name}': {model_specific_config}")

            return OpenRouterAdapter(
                model_name=actual_model_name,
                client=self._openrouter_client,
                fallback_models=self.fallback_models,
                **model_specific_config
            )
        
        logger.critical(f"Could not create adapter for model '{actual_model_name}'. No suitable provider available.")
        raise RuntimeError(f"Cannot create adapter for model '{actual_model_name}'.")
